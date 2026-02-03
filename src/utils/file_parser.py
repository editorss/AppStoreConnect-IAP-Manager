#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件解析器 - 支持TXT、CSV、Excel文件导入
"""

import csv
from typing import List
from ..core.models import BatchProduct


class FileParser:
    """文件解析器类"""
    
    @staticmethod
    def parse_txt_file(file_path: str) -> List[BatchProduct]:
        """
        解析TXT文件（欢牛模板格式）
        格式：价格 数量 商品ID（Tab或空格分隔）
        
        Args:
            file_path: 文件路径
            
        Returns:
            BatchProduct列表
        """
        products = []
        package_name = "coins"  # 默认包名
        found_data_section = False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # 提取包名
            if "包名:" in line or "包名：" in line:
                parts = line.split(":" if ":" in line else "：")
                if len(parts) >= 2:
                    package_name = parts[1].strip()
                continue
            
            # 检测数据区域开始
            if "内购id:" in line or "金额" in line:
                found_data_section = True
                continue
            
            if not found_data_section:
                continue
            
            # 遇到非数据行停止
            if any(keyword in line for keyword in ["姓名", "账户", "银行", "配置地址", "正式官网"]):
                break
            
            # 分割数据
            parts = line.split()
            if len(parts) < 3:
                continue
            
            try:
                price = parts[0]
                amount = parts[1]
                product_id = parts[2]
                
                # 验证价格格式
                float(price)
                
                # 验证数量格式
                int(amount)
                
                # 生成显示名称
                display_text = f"{amount} {package_name} cons"
                
                products.append(BatchProduct(
                    product_id=product_id,
                    display_name=display_text,
                    description=display_text,
                    price=price
                ))
                
            except (ValueError, IndexError):
                continue
        
        if not products:
            raise ValueError(
                "未找到有效的内购数据\n\n"
                "请确保文件包含类似格式的数据：\n"
                "金额\t钻石数\t批次号\n"
                "99.99\t63700\tyfxpoqqjlgsdzcwh"
            )
        
        return products
    
    @staticmethod
    def parse_csv_file(file_path: str) -> List[BatchProduct]:
        """
        解析CSV文件
        格式：金币数,原价,折扣价,内购id,app名字,小标题,奖励金币数
        
        Args:
            file_path: 文件路径
            
        Returns:
            BatchProduct列表
        """
        products = []
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            is_first_line = True
            
            for row in reader:
                # 跳过空行
                if not row:
                    continue
                
                # 跳过标题行
                if is_first_line or "金币数" in str(row):
                    is_first_line = False
                    continue
                
                if len(row) < 4:
                    continue
                
                try:
                    coin_amount = row[0].strip()
                    # original_price = row[1].strip()  # 不使用
                    discount_price = row[2].strip()
                    product_id = row[3].strip()
                    
                    # 验证数据
                    int(coin_amount)
                    float(discount_price)
                    
                    if not product_id:
                        continue
                    
                    # 生成显示名称
                    display_text = f"{coin_amount} cons"
                    
                    products.append(BatchProduct(
                        product_id=product_id,
                        display_name=display_text,
                        description=display_text,
                        price=discount_price
                    ))
                    
                except (ValueError, IndexError):
                    continue
        
        if not products:
            raise ValueError(
                "未找到有效的内购数据\n\n"
                "请确保CSV文件格式正确：\n"
                "金币数,原价,折扣价,内购id,app名字,小标题,奖励金币数\n"
                "10000,3.99,1.99,g90iyshr1v,16895260964,Get 100%,4000"
            )
        
        return products
    
    @staticmethod
    def parse_excel_file(file_path: str) -> List[BatchProduct]:
        """
        解析Excel文件（.xlsx格式）
        格式：金币数,原价,折扣价,内购id,app名字,小标题,奖励金币数
        
        Args:
            file_path: 文件路径
            
        Returns:
            BatchProduct列表
        """
        try:
            import openpyxl
        except ImportError:
            raise ImportError(
                "需要安装openpyxl库来解析Excel文件\n\n"
                "请运行: pip install openpyxl"
            )
        
        products = []
        
        try:
            workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            sheet = workbook.active
            
            is_first_row = True
            
            for row in sheet.iter_rows(values_only=True):
                # 跳过空行
                if not row or all(cell is None for cell in row):
                    continue
                
                # 跳过标题行
                if is_first_row:
                    is_first_row = False
                    # 检查是否是标题行
                    first_cell = str(row[0]) if row[0] else ""
                    if "金币" in first_cell or not first_cell.isdigit():
                        continue
                
                if len(row) < 4:
                    continue
                
                try:
                    coin_amount = str(row[0]).strip() if row[0] else ""
                    # original_price = str(row[1]).strip()  # 不使用
                    discount_price = str(row[2]).strip() if row[2] else ""
                    product_id = str(row[3]).strip() if row[3] else ""
                    
                    # 验证数据
                    if not coin_amount or not discount_price or not product_id:
                        continue
                    
                    # 尝试转换验证
                    int(float(coin_amount))
                    float(discount_price)
                    
                    # 生成显示名称
                    coin_int = int(float(coin_amount))
                    display_text = f"{coin_int} cons"
                    
                    products.append(BatchProduct(
                        product_id=product_id,
                        display_name=display_text,
                        description=display_text,
                        price=discount_price
                    ))
                    
                except (ValueError, TypeError):
                    continue
            
            workbook.close()
            
        except Exception as e:
            raise ValueError(f"Excel文件解析失败: {str(e)}")
        
        if not products:
            raise ValueError(
                "未找到有效的内购数据\n\n"
                "请确保Excel文件格式正确：\n"
                "第1列：金币数\n"
                "第2列：原价\n"
                "第3列：折扣价（实际价格）\n"
                "第4列：内购id"
            )
        
        return products
    
    @staticmethod
    def parse_json_file(file_path: str) -> List[BatchProduct]:
        """
        解析JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            BatchProduct列表
        """
        import json
        
        products = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 支持两种格式：直接数组或包装器对象
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and 'products' in data:
            items = data['products']
        else:
            raise ValueError("不支持的JSON格式")
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            product = BatchProduct(
                product_id=item.get('productId', item.get('product_id', '')),
                display_name=item.get('displayName', item.get('display_name', item.get('referenceName', ''))),
                description=item.get('description', ''),
                price=item.get('price', item.get('pricePointId', '0.99'))
            )
            
            if product.product_id and product.display_name:
                products.append(product)
        
        if not products:
            raise ValueError("JSON文件中未找到有效的产品数据")
        
        return products
