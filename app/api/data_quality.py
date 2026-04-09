from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from app.services.data_quality_service import data_quality_service
from app.core.logging_config import logger

router = APIRouter(
    prefix="/api/v1/data-quality",
    tags=["data-quality"]
)


@router.post("/calculate/{data_type}", response_model=Dict[str, Any])
async def calculate_quality_metrics(data_type: str, data: List[Dict[str, Any]]):
    """计算数据质量指标"""
    try:
        if data_type not in ["user_behavior", "dish_feature"]:
            raise ValueError("Invalid data type. Must be 'user_behavior' or 'dish_feature'")
        
        metrics = data_quality_service.calculate_data_quality_metrics(data, data_type)
        return metrics
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to calculate quality metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate quality metrics")


@router.get("/report/{data_type}", response_model=Dict[str, Any])
async def get_quality_report(data_type: str):
    """获取数据质量报告"""
    try:
        if data_type not in ["user_behavior", "dish_feature"]:
            raise ValueError("Invalid data type. Must be 'user_behavior' or 'dish_feature'")
        
        report = data_quality_service.get_data_quality_report(data_type)
        
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        return report
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality report: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quality report")


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """健康检查"""
    try:
        # 获取用户行为数据质量报告
        user_behavior_report = data_quality_service.get_data_quality_report("user_behavior")
        
        # 获取菜品特征数据质量报告
        dish_feature_report = data_quality_service.get_data_quality_report("dish_feature")
        
        # 计算整体健康状况
        overall_health = {
            "status": "healthy",
            "user_behavior_quality": user_behavior_report.get("quality_level", "unknown"),
            "dish_feature_quality": dish_feature_report.get("quality_level", "unknown"),
            "timestamp": user_behavior_report.get("timestamp", "")
        }
        
        # 如果任一数据类型质量较差，标记为警告
        if (user_behavior_report.get("quality_level") in ["poor", "critical"] or
            dish_feature_report.get("quality_level") in ["poor", "critical"]):
            overall_health["status"] = "warning"
        
        return {
            "status": "ok",
            "data_quality": overall_health,
            "components": {
                "user_behavior": user_behavior_report,
                "dish_feature": dish_feature_report
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }