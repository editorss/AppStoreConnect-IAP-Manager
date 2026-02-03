#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型 - App Store Connect API相关数据结构
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


# ============ 枚举类型 ============

class InAppPurchaseType(Enum):
    """内购产品类型枚举"""
    CONSUMABLE = "CONSUMABLE"               # 消耗型
    NON_CONSUMABLE = "NON_CONSUMABLE"       # 非消耗型
    AUTO_RENEWABLE = "AUTO_RENEWABLE"       # 自动续费订阅
    NON_RENEWING = "NON_RENEWING"          # 非续费订阅
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            self.CONSUMABLE: "消耗型",
            self.NON_CONSUMABLE: "非消耗型",
            self.AUTO_RENEWABLE: "自动续费订阅",
            self.NON_RENEWING: "非续费订阅"
        }
        return names.get(self, self.value)
    
    @property
    def description(self) -> str:
        """获取描述信息"""
        descriptions = {
            self.CONSUMABLE: "可重复购买的产品，如游戏币、道具等",
            self.NON_CONSUMABLE: "一次性购买的功能，如移除广告、解锁功能等",
            self.AUTO_RENEWABLE: "自动续费的订阅服务，如月度/年度会员",
            self.NON_RENEWING: "有限期的订阅，不会自动续费"
        }
        return descriptions.get(self, "")


class InAppPurchaseState(Enum):
    """内购产品状态枚举"""
    CREATED = "CREATED"                             # 已创建
    MISSING_METADATA = "MISSING_METADATA"           # 缺少元数据
    DEVELOPER_SIGNED_OFF = "DEVELOPER_SIGNED_OFF"   # 开发者已签署
    DEVELOPER_ACTION_NEEDED = "DEVELOPER_ACTION_NEEDED"  # 需要开发者操作
    PENDING_BINARY_APPROVAL = "PENDING_BINARY_APPROVAL"  # 等待二进制审核
    WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"       # 等待审核
    IN_REVIEW = "IN_REVIEW"                         # 审核中
    PENDING_DEVELOPER_RELEASE = "PENDING_DEVELOPER_RELEASE"  # 等待开发者发布
    READY_FOR_SALE = "READY_FOR_SALE"              # 准备销售
    APPROVED = "APPROVED"                           # 已批准
    REJECTED = "REJECTED"                           # 被拒绝
    REMOVED = "REMOVED"                             # 已移除
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        names = {
            self.CREATED: "已创建",
            self.MISSING_METADATA: "缺少元数据",
            self.DEVELOPER_SIGNED_OFF: "开发者已签署",
            self.DEVELOPER_ACTION_NEEDED: "需要开发者操作",
            self.PENDING_BINARY_APPROVAL: "等待二进制审核",
            self.WAITING_FOR_REVIEW: "等待审核",
            self.IN_REVIEW: "审核中",
            self.PENDING_DEVELOPER_RELEASE: "等待开发者发布",
            self.READY_FOR_SALE: "准备销售",
            self.APPROVED: "已批准",
            self.REJECTED: "被拒绝",
            self.REMOVED: "已移除"
        }
        return names.get(self, self.value)


# ============ 数据类 ============

@dataclass
class App:
    """应用信息模型"""
    id: str
    name: str
    bundle_id: str
    sku: str
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'App':
        """从API响应创建App对象"""
        attributes = data.get('attributes', {})
        return cls(
            id=data.get('id', ''),
            name=attributes.get('name', ''),
            bundle_id=attributes.get('bundleId', ''),
            sku=attributes.get('sku', '')
        )


@dataclass
class InAppPurchaseLocalization:
    """内购产品本地化信息"""
    id: Optional[str] = None
    locale: str = "en-US"
    name: str = ""
    description: str = ""
    state: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'InAppPurchaseLocalization':
        """从API响应创建对象"""
        attributes = data.get('attributes', {})
        return cls(
            id=data.get('id'),
            locale=attributes.get('locale', 'en-US'),
            name=attributes.get('name', ''),
            description=attributes.get('description', ''),
            state=attributes.get('state')
        )
    
    def to_api_request(self) -> Dict[str, Any]:
        """转换为API请求格式"""
        return {
            "locale": self.locale,
            "name": self.name,
            "description": self.description
        }


# 支持的语言列表
SUPPORTED_LOCALES = {
    "zh-Hans": "简体中文",
    "zh-Hant": "繁体中文",
    "en-US": "英语(美国)",
    "ja": "日语",
    "ko": "韩语",
    "de-DE": "德语",
    "fr-FR": "法语",
    "es-ES": "西班牙语",
    "it": "意大利语",
    "pt-BR": "葡萄牙语(巴西)",
    "ru": "俄语",
    "ar": "阿拉伯语"
}


@dataclass
class InAppPurchase:
    """内购产品模型"""
    id: str
    product_id: str
    reference_name: str
    type: InAppPurchaseType
    state: InAppPurchaseState
    available_in_all_territories: bool = True
    content_hosting: bool = False
    family_shareable: bool = False
    localizations: List[InAppPurchaseLocalization] = field(default_factory=list)
    created_date: Optional[datetime] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'InAppPurchase':
        """从API响应创建InAppPurchase对象"""
        attributes = data.get('attributes', {})
        
        # 解析类型
        iap_type_str = attributes.get('inAppPurchaseType', 'CONSUMABLE')
        try:
            iap_type = InAppPurchaseType(iap_type_str)
        except ValueError:
            iap_type = InAppPurchaseType.CONSUMABLE
        
        # 解析状态
        state_str = attributes.get('state', 'CREATED')
        try:
            state = InAppPurchaseState(state_str)
        except ValueError:
            state = InAppPurchaseState.CREATED
        
        return cls(
            id=data.get('id', ''),
            product_id=attributes.get('productId', ''),
            reference_name=attributes.get('name', ''),
            type=iap_type,
            state=state,
            available_in_all_territories=True,
            content_hosting=attributes.get('contentHosting', False),
            family_shareable=attributes.get('familySharable', False)
        )


@dataclass
class InAppPurchasePricePoint:
    """价格点信息"""
    id: str
    customer_price: str
    price_tier: Optional[str] = None
    proceeds: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'InAppPurchasePricePoint':
        """从API响应创建对象"""
        attributes = data.get('attributes', {})
        return cls(
            id=data.get('id', ''),
            customer_price=attributes.get('customerPrice', ''),
            price_tier=attributes.get('priceTier'),
            proceeds=attributes.get('proceeds')
        )


@dataclass
class Territory:
    """销售区域信息"""
    id: str
    currency: str
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'Territory':
        """从API响应创建对象"""
        attributes = data.get('attributes', {})
        return cls(
            id=data.get('id', ''),
            currency=attributes.get('currency', '')
        )


# 中国大陆和港澳台地区的Territory ID列表
CHINA_HK_MACAU_TAIWAN_TERRITORY_IDS = {
    "CHN", "CN",   # 中国大陆
    "HKG", "HK",   # 香港
    "MAC", "MO",   # 澳门
    "TWN", "TW"    # 台湾
}


def is_china_hk_macau_taiwan(territory_id: str) -> bool:
    """检查给定的territory ID是否为中国大陆和港澳台地区"""
    return territory_id in CHINA_HK_MACAU_TAIWAN_TERRITORY_IDS


def filter_out_china_hk_macau_taiwan(territories: List[Territory]) -> List[Territory]:
    """过滤掉中国大陆和港澳台地区的territories"""
    return [t for t in territories if not is_china_hk_macau_taiwan(t.id)]


@dataclass
class BatchProduct:
    """批量创建的产品项"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_selected: bool = True
    product_id: str = ""
    display_name: str = ""
    description: str = ""
    price: str = "0.99"
    
    def to_iap_template(self) -> 'InAppPurchaseTemplate':
        """转换为内购模板"""
        return InAppPurchaseTemplate(
            product_id=self.product_id,
            reference_name=self.display_name,
            type=InAppPurchaseType.CONSUMABLE,
            display_name=self.display_name,
            description=self.description,
            price=self.price,
            available_in_all_territories=True,
            family_shareable=False,
            localizations=[
                InAppPurchaseLocalization(
                    locale="en-US",
                    name=self.display_name,
                    description=self.description
                )
            ]
        )


@dataclass
class InAppPurchaseTemplate:
    """内购产品创建模板"""
    product_id: str
    reference_name: str
    type: InAppPurchaseType
    display_name: str
    description: str
    price: str = "0.99"
    available_in_all_territories: bool = True
    family_shareable: bool = False
    localizations: List[InAppPurchaseLocalization] = field(default_factory=list)
    
    def to_api_request(self, app_id: str) -> Dict[str, Any]:
        """转换为API创建请求格式"""
        return {
            "data": {
                "type": "inAppPurchases",
                "attributes": {
                    "name": self.display_name,
                    "productId": self.product_id,
                    "inAppPurchaseType": self.type.value,
                    "familySharable": self.family_shareable
                },
                "relationships": {
                    "app": {
                        "data": {
                            "type": "apps",
                            "id": app_id
                        }
                    }
                }
            }
        }


@dataclass
class BatchOperationResult:
    """批量操作结果"""
    product_id: str
    success: bool
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "product_id": self.product_id,
            "success": self.success,
            "message": self.message
        }


@dataclass
class APIError:
    """API错误信息"""
    status: str
    code: str
    title: str
    detail: str
    
    @classmethod
    def from_api_response(cls, error_data: Dict[str, Any]) -> 'APIError':
        """从API错误响应创建对象"""
        return cls(
            status=error_data.get('status', ''),
            code=error_data.get('code', ''),
            title=error_data.get('title', ''),
            detail=error_data.get('detail', '')
        )
    
    def __str__(self) -> str:
        return f"{self.title}: {self.detail}"


# 常用价格列表
COMMON_PRICES = [
    "0.99", "1.99", "2.99", "4.99", "6.99", 
    "9.99", "14.99", "19.99", "29.99", "49.99", "99.99"
]
