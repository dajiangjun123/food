import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from app.core.logging_config import logger


class DataCleaningService:
    """数据清洗和标准化服务"""
    
    @staticmethod
    def clean_user_behavior_data(behavior_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清洗用户行为数据"""
        try:
            if not behavior_data:
                return []
            
            # 转换为DataFrame进行批量处理
            df = pd.DataFrame(behavior_data)
            
            # 1. 处理缺失值
            df = DataCleaningService._handle_missing_values(df)
            
            # 2. 处理异常值
            df = DataCleaningService._handle_outliers(df)
            
            # 3. 去重
            df = DataCleaningService._remove_duplicates(df)
            
            # 4. 标准化数据格式
            df = DataCleaningService._standardize_data_format(df)
            
            # 5. 验证数据完整性
            df = DataCleaningService._validate_data_integrity(df)
            
            # 转换回字典列表
            cleaned_data = df.to_dict('records')
            
            logger.info(f"Cleaned {len(cleaned_data)} user behavior records")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Failed to clean user behavior data: {e}")
            return []
    
    @staticmethod
    def clean_dish_feature_data(feature_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清洗菜品特征数据"""
        try:
            if not feature_data:
                return []
            
            # 转换为DataFrame进行批量处理
            df = pd.DataFrame(feature_data)
            
            # 1. 处理缺失值
            df = DataCleaningService._handle_missing_values(df, is_dish_feature=True)
            
            # 2. 处理异常值
            df = DataCleaningService._handle_outliers(df, is_dish_feature=True)
            
            # 3. 去重
            df = DataCleaningService._remove_duplicates(df, key_column='dish_id')
            
            # 4. 标准化数据格式
            df = DataCleaningService._standardize_data_format(df, is_dish_feature=True)
            
            # 5. 验证数据完整性
            df = DataCleaningService._validate_data_integrity(df, is_dish_feature=True)
            
            # 转换回字典列表
            cleaned_data = df.to_dict('records')
            
            logger.info(f"Cleaned {len(cleaned_data)} dish feature records")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Failed to clean dish feature data: {e}")
            return []
    
    @staticmethod
    def _handle_missing_values(df: pd.DataFrame, is_dish_feature: bool = False) -> pd.DataFrame:
        """处理缺失值"""
        # 用户行为数据缺失值处理
        if not is_dish_feature:
            # 删除关键字段缺失的记录
            df = df.dropna(subset=['user_id', 'behavior_type', 'timestamp'])
            
            # 删除空字符串的记录
            df = df[df['user_id'].astype(str).str.strip() != '']
            df = df[df['behavior_type'].astype(str).str.strip() != '']
            
            # 填充可选字段
            if 'dish_id' in df.columns:
                df['dish_id'] = df['dish_id'].fillna('')
            if 'merchant_id' in df.columns:
                df['merchant_id'] = df['merchant_id'].fillna('')
            if 'context' in df.columns:
                df['context'] = df['context'].fillna({})
            
        # 菜品特征数据缺失值处理
        else:
            # 删除关键字段缺失的记录
            df = df.dropna(subset=['dish_id', 'merchant_id', 'name', 'price', 'category'])
            
            # 删除空字符串的记录
            df = df[df['dish_id'].astype(str).str.strip() != '']
            df = df[df['merchant_id'].astype(str).str.strip() != '']
            df = df[df['name'].astype(str).str.strip() != '']
            df = df[df['category'].astype(str).str.strip() != '']
            
            # 填充可选字段
            if 'description' in df.columns:
                df['description'] = df['description'].fillna('')
            if 'image_url' in df.columns:
                df['image_url'] = df['image_url'].fillna('')
            if 'tags' in df.columns:
                df['tags'] = df['tags'].fillna([])
            if 'sales_volume' in df.columns:
                df['sales_volume'] = df['sales_volume'].fillna(0)
            if 'rating' in df.columns:
                df['rating'] = df['rating'].fillna(0)
            if 'review_count' in df.columns:
                df['review_count'] = df['review_count'].fillna(0)
            
        return df
    
    @staticmethod
    def _handle_outliers(df: pd.DataFrame, is_dish_feature: bool = False) -> pd.DataFrame:
        """处理异常值"""
        if is_dish_feature:
            # 价格异常值处理（移除价格过高或过低的记录）
            df = df[(df['price'] > 0) & (df['price']< 1000)]
            
            # 销量异常值处理（使用IQR方法）
            if 'sales_volume' in df.columns:
                Q1 = df['sales_volume'].quantile(0.25)
                Q3 = df['sales_volume'].quantile(0.75)
                IQR = Q3 - Q1
                df = df[(df['sales_volume'] >= Q1 - 1.5 * IQR) & (df['sales_volume']<= Q3 + 1.5 * IQR)]
            
            # 评分异常值处理
            df = df[(df['rating'] >= 0) & (df['rating']<= 5)]
            
        return df
    
    @staticmethod
    def _remove_duplicates(df: pd.DataFrame, key_column: str = None) -> pd.DataFrame:
        """去重"""
        if key_column:
            # 根据指定列去重
            df = df.drop_duplicates(subset=[key_column], keep='last')
        else:
            # 根据所有列去重
            df = df.drop_duplicates()
            
        return df
    
    @staticmethod
    def _standardize_data_format(df: pd.DataFrame, is_dish_feature: bool = False) -> pd.DataFrame:
        """标准化数据格式"""
        # 标准化字符串字段
        string_columns = ['user_id', 'behavior_type', 'dish_id', 'merchant_id'] if not is_dish_feature else \
                        ['dish_id', 'merchant_id', 'name', 'category', 'description']
        
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # 标准化时间格式
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
        # 标准化数值格式
        if is_dish_feature:
            if 'price' in df.columns:
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
            if 'sales_volume' in df.columns:
                df['sales_volume'] = pd.to_numeric(df['sales_volume'], errors='coerce').fillna(0).astype(int)
            if 'rating' in df.columns:
                df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
            if 'review_count' in df.columns:
                df['review_count'] = pd.to_numeric(df['review_count'], errors='coerce').fillna(0).astype(int)
            
        return df
    
    @staticmethod
    def _validate_data_integrity(df: pd.DataFrame, is_dish_feature: bool = False) -> pd.DataFrame:
        """验证数据完整性"""
        # 验证用户行为类型
        valid_behavior_types = ['click', 'view', 'order', 'rate', 'favorite', 'share']
        if not is_dish_feature and 'behavior_type' in df.columns:
            df = df[df['behavior_type'].isin(valid_behavior_types)]
            
        # 验证时间范围（只保留最近1年的数据）
        if 'timestamp' in df.columns:
            # 确保timestamp是datetime类型
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            # 删除时间解析失败的记录
            df = df.dropna(subset=['timestamp'])
            # 只保留最近1年的数据
            one_year_ago = datetime.utcnow() - pd.Timedelta(days=365)
            df = df[df['timestamp'] >= one_year_ago]
            
        return df
    
    @staticmethod
    def normalize_features(df: pd.DataFrame, numeric_columns: List[str]) -> pd.DataFrame:
        """标准化数值特征"""
        try:
            from sklearn.preprocessing import StandardScaler
            
            scaler = StandardScaler()
            df[numeric_columns] = scaler.fit_transform(df[numeric_columns])
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to normalize features: {e}")
            return df
    
    @staticmethod
    def encode_categorical_features(df: pd.DataFrame, categorical_columns: List[str]) -> pd.DataFrame:
        """编码分类特征"""
        try:
            from sklearn.preprocessing import LabelEncoder
            
            for col in categorical_columns:
                if col in df.columns:
                    encoder = LabelEncoder()
                    df[col] = encoder.fit_transform(df[col])
                    
            return df
            
        except Exception as e:
            logger.error(f"Failed to encode categorical features: {e}")
            return df


# 创建全局服务实例
data_cleaning_service = DataCleaningService()