import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from app.core.logging_config import logger
from app.core.database import redis_client


class DataQualityService:
    """数据质量监控和验证服务"""
    
    @staticmethod
    def calculate_data_quality_metrics(data: List[Dict[str, Any]], data_type: str) -> Dict[str, Any]:
        """计算数据质量指标"""
        try:
            if not data:
                return {
                    "data_type": data_type,
                    "record_count": 0,
                    "completeness": 0.0,
                    "accuracy": 0.0,
                    "consistency": 0.0,
                    "timeliness": 0.0,
                    "duplicate_count": 0,
                    "error_count": 0
                }
            
            df = pd.DataFrame(data)
            
            metrics = {
                "data_type": data_type,
                "record_count": len(df),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 1. 完整性指标
            metrics["completeness"] = DataQualityService._calculate_completeness(df, data_type)
            
            # 2. 准确性指标
            metrics["accuracy"] = DataQualityService._calculate_accuracy(df, data_type)
            
            # 3. 一致性指标
            metrics["consistency"] = DataQualityService._calculate_consistency(df, data_type)
            
            # 4. 时效性指标
            metrics["timeliness"] = DataQualityService._calculate_timeliness(df)
            
            # 5. 重复数据统计
            metrics["duplicate_count"] = DataQualityService._count_duplicates(df, data_type)
            
            # 6. 错误数据统计
            metrics["error_count"] = DataQualityService._count_errors(df, data_type)
            
            # 7. 详细字段统计
            metrics["field_statistics"] = DataQualityService._calculate_field_statistics(df)
            
            # 更新Redis中的质量指标
            DataQualityService._update_quality_metrics_in_redis(metrics)
            
            logger.info(f"Calculated data quality metrics for {data_type}: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate data quality metrics: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _calculate_completeness(df: pd.DataFrame, data_type: str) -> float:
        """计算数据完整性"""
        # 根据数据类型定义必填字段
        required_fields = {
            "user_behavior": ["user_id", "behavior_type", "timestamp"],
            "dish_feature": ["dish_id", "merchant_id", "name", "price", "category"]
        }.get(data_type, [])
        
        # 计算记录级别的完整性（所有必填字段都非空且非空字符串）
        if not required_fields:
            return 1.0
            
        # 计算每条记录是否所有必填字段都完整
        complete_records = []
        for _, row in df.iterrows():
            is_complete = True
            for field in required_fields:
                if field in df.columns:
                    value = row[field]
                    if pd.isna(value) or (isinstance(value, str) and value.strip() == ''):
                        is_complete = False
                        break
            complete_records.append(is_complete)
        
        return np.mean(complete_records) if complete_records else 1.0
    
    @staticmethod
    def _calculate_accuracy(df: pd.DataFrame, data_type: str) -> float:
        """计算数据准确性"""
        accuracy_scores = []
        
        if data_type == "dish_feature":
            # 价格准确性（必须大于0）
            if "price" in df.columns:
                price_accuracy = (df["price"] > 0).mean()
                accuracy_scores.append(price_accuracy)
            
            # 评分准确性（必须在0-5之间）
            if "rating" in df.columns:
                rating_accuracy = ((df["rating"] >= 0) & (df["rating"]<= 5)).mean()
                accuracy_scores.append(rating_accuracy)
            
            # 销量准确性（必须大于等于0）
            if "sales_volume" in df.columns:
                sales_accuracy = (df["sales_volume"] >= 0).mean()
                accuracy_scores.append(sales_accuracy)
                
        elif data_type == "user_behavior":
            # 行为类型准确性
            valid_behaviors = ['click', 'view', 'order', 'rate', 'favorite', 'share']
            if "behavior_type" in df.columns:
                behavior_accuracy = df["behavior_type"].isin(valid_behaviors).mean()
                accuracy_scores.append(behavior_accuracy)
        
        return np.mean(accuracy_scores) if accuracy_scores else 1.0
    
    @staticmethod
    def _calculate_consistency(df: pd.DataFrame, data_type: str) -> float:
        """计算数据一致性"""
        consistency_scores = []
        
        if data_type == "dish_feature":
            # 分类一致性（检查分类值是否一致）
            if "category" in df.columns:
                # 这里可以根据预定义的分类列表进行验证
                # 简化实现：检查分类不为空
                category_consistency = (df["category"].str.strip() != "").mean()
                consistency_scores.append(category_consistency)
                
        return np.mean(consistency_scores) if consistency_scores else 1.0
    
    @staticmethod
    def _calculate_timeliness(df: pd.DataFrame) -> float:
        """计算数据时效性"""
        if "timestamp" not in df.columns:
            return 1.0
        
        # 转换时间戳
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
        
        # 计算数据的平均新鲜度（越新越好）
        current_time = datetime.utcnow()
        df["age_hours"] = (current_time - df["timestamp"]).dt.total_seconds() / 3600
        
        # 时效性评分：1小时内为1.0，超过72小时为0.0
        df["timeliness_score"] = 1.0 - (df["age_hours"] / 72.0)
        df["timeliness_score"] = df["timeliness_score"].clip(0.0, 1.0)
        
        return df["timeliness_score"].mean()
    
    @staticmethod
    def _count_duplicates(df: pd.DataFrame, data_type: str) -> int:
        """统计重复数据"""
        if data_type == "dish_feature" and "dish_id" in df.columns:
            # 根据dish_id去重
            return len(df) - len(df.drop_duplicates(subset=["dish_id"]))
        else:
            # 根据所有列去重
            return len(df) - len(df.drop_duplicates())
    
    @staticmethod
    def _count_errors(df: pd.DataFrame, data_type: str) -> int:
        """统计错误数据"""
        error_count = 0
        
        if data_type == "dish_feature":
            # 价格错误
            if "price" in df.columns:
                error_count += (df["price"]<= 0).sum()
            
            # 评分错误
            if "rating" in df.columns:
                error_count += ((df["rating"]< 0) | (df["rating"] >5)).sum()
                
        elif data_type == "user_behavior":
            # 用户ID为空的错误
            if "user_id" in df.columns:
                error_count += (df["user_id"].astype(str).str.strip() == "").sum()
            
            # 行为类型错误
            valid_behaviors = ['click', 'view', 'order', 'rate', 'favorite', 'share']
            if "behavior_type" in df.columns:
                error_count += (~df["behavior_type"].isin(valid_behaviors)).sum()
        
        return error_count
    
    @staticmethod
    def _calculate_field_statistics(df: pd.DataFrame) -> Dict[str, Any]:
        """计算字段统计信息"""
        statistics = {}
        
        for column in df.columns:
            col_stats = {}
            
            # 基本统计
            col_stats["non_null_count"] = df[column].notna().sum()
            col_stats["null_count"] = df[column].isna().sum()
            col_stats["unique_count"] = df[column].nunique()
            
            # 数值型字段统计
            if pd.api.types.is_numeric_dtype(df[column]):
                col_stats["mean"] = df[column].mean()
                col_stats["min"] = df[column].min()
                col_stats["max"] = df[column].max()
                col_stats["std"] = df[column].std()
            
            # 字符串型字段统计
            elif pd.api.types.is_string_dtype(df[column]):
                non_empty = df[column].dropna().astype(str).str.strip() != ""
                col_stats["non_empty_count"] = non_empty.sum()
                
            statistics[column] = col_stats
        
        return statistics
    
    @staticmethod
    def _update_quality_metrics_in_redis(metrics: Dict[str, Any]):
        """更新Redis中的质量指标"""
        try:
            data_type = metrics["data_type"]
            timestamp = metrics["timestamp"]
            
            # 存储最新的质量指标
            redis_key = f"data_quality:{data_type}:latest"
            redis_client.hset(redis_key, mapping={
                "record_count": str(metrics["record_count"]),
                "completeness": str(metrics["completeness"]),
                "accuracy": str(metrics["accuracy"]),
                "consistency": str(metrics["consistency"]),
                "timeliness": str(metrics["timeliness"]),
                "duplicate_count": str(metrics["duplicate_count"]),
                "error_count": str(metrics["error_count"]),
                "timestamp": timestamp
            })
            
            # 存储历史记录（保留最近100条）
            history_key = f"data_quality:{data_type}:history"
            redis_client.lpush(history_key, str(metrics))
            redis_client.ltrim(history_key, 0, 99)
            
        except Exception as e:
            logger.warning(f"Failed to update Redis quality metrics: {e}")
    
    @staticmethod
    def get_data_quality_report(data_type: str) -> Dict[str, Any]:
        """获取数据质量报告"""
        try:
            # 从Redis获取最新指标
            redis_key = f"data_quality:{data_type}:latest"
            metrics = redis_client.hgetall(redis_key)
            
            if not metrics:
                return {"error": "No quality metrics found"}
            
            # 转换数据类型
            report = {
                "data_type": data_type,
                "record_count": int(metrics.get("record_count", 0)),
                "completeness": float(metrics.get("completeness", 0)),
                "accuracy": float(metrics.get("accuracy", 0)),
                "consistency": float(metrics.get("consistency", 0)),
                "timeliness": float(metrics.get("timeliness", 0)),
                "duplicate_count": int(metrics.get("duplicate_count", 0)),
                "error_count": int(metrics.get("error_count", 0)),
                "timestamp": metrics.get("timestamp", "")
            }
            
            # 添加质量等级评估
            report["quality_level"] = DataQualityService._assess_quality_level(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to get data quality report: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _assess_quality_level(metrics: Dict[str, Any]) -> str:
        """评估数据质量等级"""
        # 根据各项指标的平均值确定质量等级
        avg_score = (metrics["completeness"] + metrics["accuracy"] + 
                    metrics["consistency"] + metrics["timeliness"]) / 4
        
        if avg_score >= 0.95:
            return "excellent"
        elif avg_score >= 0.90:
            return "good"
        elif avg_score >= 0.80:
            return "fair"
        elif avg_score >= 0.70:
            return "poor"
        else:
            return "critical"


# 创建全局服务实例
data_quality_service = DataQualityService()