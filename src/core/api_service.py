#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App Store Connect API 服务类
负责处理所有与App Store Connect API的通信
"""

import requests
import hashlib
import base64
import time
from typing import Optional, List, Dict, Any, Tuple
from .jwt_authenticator import JWTAuthenticator
from .models import (
    App, InAppPurchase, InAppPurchaseTemplate, InAppPurchaseLocalization,
    InAppPurchasePricePoint, Territory, APIError,
    filter_out_china_hk_macau_taiwan
)


class AppStoreConnectAPIService:
    """App Store Connect API 服务类"""
    
    BASE_URL = "https://api.appstoreconnect.apple.com"
    
    def __init__(self):
        """初始化API服务"""
        self._authenticator: Optional[JWTAuthenticator] = None
        self._is_authenticated = False
        self._cached_jwt: Optional[str] = None
        self._jwt_expiry: float = 0
        
    @property
    def is_authenticated(self) -> bool:
        """是否已认证"""
        return self._is_authenticated
    
    def configure_authentication(self, key_id: str, issuer_id: str, private_key: str) -> Tuple[bool, str]:
        """
        配置API认证信息
        
        Args:
            key_id: API Key ID
            issuer_id: Issuer ID
            private_key: 私钥内容
            
        Returns:
            (成功与否, 错误信息)
        """
        # 验证参数
        valid, msg = JWTAuthenticator.validate_all(key_id, issuer_id, private_key)
        if not valid:
            self._is_authenticated = False
            return False, msg
        
        try:
            self._authenticator = JWTAuthenticator(key_id, issuer_id, private_key)
            # 尝试生成JWT验证配置是否正确
            self._authenticator.generate_jwt()
            self._is_authenticated = True
            return True, ""
        except Exception as e:
            self._is_authenticated = False
            return False, f"认证配置失败: {str(e)}"
    
    def _get_jwt(self) -> str:
        """获取JWT令牌（带缓存）"""
        if not self._authenticator:
            raise ValueError("认证器未配置")
        
        current_time = time.time()
        # 如果缓存的JWT还有5分钟以上有效期，继续使用
        if self._cached_jwt and current_time < self._jwt_expiry - 300:
            return self._cached_jwt
        
        # 生成新的JWT
        self._cached_jwt = self._authenticator.generate_jwt()
        self._jwt_expiry = current_time + (20 * 60)  # 20分钟有效期
        return self._cached_jwt
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        发送API请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            body: 请求体
            timeout: 超时时间
            
        Returns:
            API响应数据
            
        Raises:
            APIException: API调用失败时抛出
        """
        if not self._authenticator:
            raise APIException("未配置API认证")
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._get_jwt()}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                timeout=timeout
            )
            
            # 处理无内容响应（如DELETE操作）
            if response.status_code == 204:
                return {}
            
            # 解析响应
            data = response.json() if response.text else {}
            
            # 检查错误
            if response.status_code >= 400:
                errors = data.get('errors', [])
                if errors:
                    error = APIError.from_api_response(errors[0])
                    raise APIException(str(error), response.status_code, errors)
                raise APIException(f"HTTP错误: {response.status_code}", response.status_code)
            
            return data
            
        except requests.exceptions.Timeout:
            raise APIException("请求超时", 408)
        except requests.exceptions.ConnectionError:
            raise APIException("网络连接失败", 0)
        except requests.exceptions.RequestException as e:
            raise APIException(f"请求失败: {str(e)}", 0)
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        测试API连接
        
        Returns:
            (成功与否, 状态消息)
        """
        if not self._authenticator:
            return False, "未配置API认证"
        
        try:
            self._make_request("GET", "/v1/apps?limit=1")
            return True, "连接成功"
        except APIException as e:
            return False, str(e)
    
    # ============ 应用管理 ============
    
    def fetch_apps(self) -> List[App]:
        """
        获取应用列表
        
        Returns:
            应用列表
        """
        response = self._make_request("GET", "/v1/apps")
        apps_data = response.get('data', [])
        return [App.from_api_response(app) for app in apps_data]
    
    # ============ 内购产品管理 ============
    
    def fetch_in_app_purchases(self, app_id: str) -> List[InAppPurchase]:
        """
        获取指定应用的内购产品列表
        
        Args:
            app_id: 应用ID
            
        Returns:
            内购产品列表
        """
        response = self._make_request("GET", f"/v1/apps/{app_id}/inAppPurchasesV2")
        iaps_data = response.get('data', [])
        return [InAppPurchase.from_api_response(iap) for iap in iaps_data]
    
    def create_in_app_purchase(self, app_id: str, template: InAppPurchaseTemplate) -> InAppPurchase:
        """
        创建内购产品
        
        Args:
            app_id: 应用ID
            template: 内购产品模板
            
        Returns:
            创建的内购产品
        """
        request_body = template.to_api_request(app_id)
        response = self._make_request("POST", "/v2/inAppPurchases", request_body)
        return InAppPurchase.from_api_response(response.get('data', {}))
    
    def delete_in_app_purchase(self, iap_id: str) -> bool:
        """
        删除内购产品
        
        Args:
            iap_id: 内购产品ID
            
        Returns:
            是否成功
        """
        self._make_request("DELETE", f"/v2/inAppPurchases/{iap_id}")
        return True
    
    def update_in_app_purchase(
        self,
        iap_id: str,
        reference_name: str,
        family_shareable: bool = False
    ) -> InAppPurchase:
        """
        更新内购产品信息
        
        Args:
            iap_id: 内购产品ID
            reference_name: 引用名称
            family_shareable: 是否家庭共享
            
        Returns:
            更新后的内购产品
        """
        request_body = {
            "data": {
                "type": "inAppPurchases",
                "id": iap_id,
                "attributes": {
                    "name": reference_name,
                    "familyShareable": family_shareable
                }
            }
        }
        response = self._make_request("PATCH", f"/v2/inAppPurchases/{iap_id}", request_body)
        return InAppPurchase.from_api_response(response.get('data', {}))
    
    # ============ 本地化管理 ============
    
    def create_localization(
        self,
        iap_id: str,
        localization: InAppPurchaseLocalization
    ) -> InAppPurchaseLocalization:
        """
        创建内购产品本地化信息
        
        Args:
            iap_id: 内购产品ID
            localization: 本地化信息
            
        Returns:
            创建的本地化信息
        """
        request_body = {
            "data": {
                "type": "inAppPurchaseLocalizations",
                "attributes": {
                    "locale": localization.locale,
                    "name": localization.name,
                    "description": localization.description
                },
                "relationships": {
                    "inAppPurchaseV2": {
                        "data": {
                            "type": "inAppPurchases",
                            "id": iap_id
                        }
                    }
                }
            }
        }
        response = self._make_request("POST", "/v1/inAppPurchaseLocalizations", request_body)
        return InAppPurchaseLocalization.from_api_response(response.get('data', {}))
    
    # ============ 价格管理 ============
    
    def fetch_price_points(self, iap_id: str, territory: str = "USA") -> List[InAppPurchasePricePoint]:
        """
        获取内购产品的价格点选项
        
        Args:
            iap_id: 内购产品ID
            territory: 地区代码
            
        Returns:
            价格点列表
        """
        endpoint = f"/v2/inAppPurchases/{iap_id}/pricePoints?filter[territory]={territory}&limit=200"
        response = self._make_request("GET", endpoint)
        points_data = response.get('data', [])
        return [InAppPurchasePricePoint.from_api_response(p) for p in points_data]
    
    def find_matching_price_point(
        self,
        target_price: str,
        price_points: List[InAppPurchasePricePoint]
    ) -> Optional[InAppPurchasePricePoint]:
        """
        查找匹配的价格点
        
        Args:
            target_price: 目标价格
            price_points: 可用价格点列表
            
        Returns:
            匹配的价格点，未找到返回None
        """
        # 首先尝试精确匹配
        for point in price_points:
            if target_price in point.customer_price:
                return point
        
        # 尝试数值匹配
        try:
            target_value = float(target_price)
            closest_point = None
            smallest_diff = float('inf')
            
            for point in price_points:
                # 提取价格数值
                price_str = ''.join(c for c in point.customer_price if c.isdigit() or c == '.')
                if price_str:
                    try:
                        price_value = float(price_str)
                        diff = abs(price_value - target_value)
                        if diff < smallest_diff:
                            smallest_diff = diff
                            closest_point = point
                    except ValueError:
                        continue
            
            return closest_point
        except ValueError:
            return None
    
    def create_price_schedule(
        self,
        iap_id: str,
        price_point_id: str,
        territory: str = "USA"
    ) -> bool:
        """
        设置内购产品价格计划
        
        Args:
            iap_id: 内购产品ID
            price_point_id: 价格点ID
            territory: 基础地区
            
        Returns:
            是否成功
        """
        request_body = {
            "data": {
                "type": "inAppPurchasePriceSchedules",
                "relationships": {
                    "baseTerritory": {
                        "data": {
                            "type": "territories",
                            "id": territory
                        }
                    },
                    "inAppPurchase": {
                        "data": {
                            "type": "inAppPurchases",
                            "id": iap_id
                        }
                    },
                    "manualPrices": {
                        "data": [{
                            "type": "inAppPurchasePrices",
                            "id": "${price1}"
                        }]
                    }
                }
            },
            "included": [{
                "type": "inAppPurchasePrices",
                "id": "${price1}",
                "attributes": {
                    "startDate": None,
                    "endDate": None
                },
                "relationships": {
                    "inAppPurchaseV2": {
                        "data": {
                            "type": "inAppPurchases",
                            "id": iap_id
                        }
                    },
                    "inAppPurchasePricePoint": {
                        "data": {
                            "type": "inAppPurchasePricePoints",
                            "id": price_point_id
                        }
                    }
                }
            }]
        }
        
        self._make_request("POST", "/v1/inAppPurchasePriceSchedules", request_body)
        return True
    
    # ============ 销售区域管理 ============
    
    def fetch_territories(self) -> List[Territory]:
        """
        获取所有可用的销售地区
        
        Returns:
            地区列表
        """
        response = self._make_request("GET", "/v1/territories?limit=200")
        territories_data = response.get('data', [])
        return [Territory.from_api_response(t) for t in territories_data]
    
    def create_availability(
        self,
        iap_id: str,
        exclude_china_hk_macau_taiwan: bool = False
    ) -> bool:
        """
        设置内购产品销售范围
        
        Args:
            iap_id: 内购产品ID
            exclude_china_hk_macau_taiwan: 是否排除中国大陆和港澳台地区
            
        Returns:
            是否成功
        """
        # 获取所有地区
        all_territories = self.fetch_territories()
        
        # 根据设置过滤地区
        if exclude_china_hk_macau_taiwan:
            territories = filter_out_china_hk_macau_taiwan(all_territories)
        else:
            territories = all_territories
        
        # 构建请求体
        territory_data = [
            {"type": "territories", "id": t.id}
            for t in territories
        ]
        
        request_body = {
            "data": {
                "type": "inAppPurchaseAvailabilities",
                "attributes": {
                    "availableInNewTerritories": True
                },
                "relationships": {
                    "inAppPurchase": {
                        "data": {
                            "type": "inAppPurchases",
                            "id": iap_id
                        }
                    },
                    "availableTerritories": {
                        "data": territory_data
                    }
                }
            }
        }
        
        self._make_request("POST", "/v1/inAppPurchaseAvailabilities", request_body)
        return True
    
    # ============ 审核截图上传 ============
    
    def upload_review_screenshot(
        self,
        iap_id: str,
        image_data: bytes,
        file_name: str
    ) -> bool:
        """
        上传内购产品审核截图（三步流程）
        
        Args:
            iap_id: 内购产品ID
            image_data: 图片二进制数据
            file_name: 文件名
            
        Returns:
            是否成功
        """
        # 步骤1: Reserve - 创建截图记录
        reserve_body = {
            "data": {
                "type": "inAppPurchaseAppStoreReviewScreenshots",
                "attributes": {
                    "fileName": file_name,
                    "fileSize": len(image_data)
                },
                "relationships": {
                    "inAppPurchaseV2": {
                        "data": {
                            "type": "inAppPurchases",
                            "id": iap_id
                        }
                    }
                }
            }
        }
        
        reserve_response = self._make_request(
            "POST",
            "/v1/inAppPurchaseAppStoreReviewScreenshots",
            reserve_body
        )
        
        screenshot_data = reserve_response.get('data', {})
        screenshot_id = screenshot_data.get('id')
        attributes = screenshot_data.get('attributes', {})
        upload_operations = attributes.get('uploadOperations', [])
        
        if not upload_operations:
            raise APIException("未获取到上传操作信息")
        
        # 步骤2: Upload - 上传图片到S3
        for operation in upload_operations:
            upload_url = operation.get('url')
            method = operation.get('method', 'PUT')
            offset = operation.get('offset', 0)
            length = operation.get('length', len(image_data))
            request_headers = operation.get('requestHeaders', [])
            
            # 准备数据片段
            chunk = image_data[offset:offset + length]
            
            # 计算MD5
            md5_hash = base64.b64encode(hashlib.md5(chunk).digest()).decode('utf-8')
            
            # 构建请求头
            headers = {
                "Content-MD5": md5_hash,
                "Content-Length": str(len(chunk))
            }
            for h in request_headers:
                if h.get('name') and h.get('value'):
                    headers[h['name']] = h['value']
            
            # 上传到S3（不使用JWT认证）
            upload_response = requests.request(
                method=method,
                url=upload_url,
                headers=headers,
                data=chunk,
                timeout=60
            )
            
            if upload_response.status_code >= 400:
                raise APIException(f"上传失败: HTTP {upload_response.status_code}")
        
        # 步骤3: Commit - 确认上传完成
        commit_body = {
            "data": {
                "id": screenshot_id,
                "type": "inAppPurchaseAppStoreReviewScreenshots",
                "attributes": {
                    "uploaded": True
                }
            }
        }
        
        self._make_request(
            "PATCH",
            f"/v1/inAppPurchaseAppStoreReviewScreenshots/{screenshot_id}",
            commit_body
        )
        
        return True


class APIException(Exception):
    """API异常"""
    
    def __init__(self, message: str, status_code: int = 0, errors: List[Dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
    
    def __str__(self) -> str:
        return self.message
