from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.services.performance_service import PerformanceService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
def health_check(
    performance_service: PerformanceService = Depends(PerformanceService)
) -> Dict[str, Any]:
    """健康检查接口"""
    health_status = performance_service.check_system_health()
    return health_status


@router.get("/metrics")
def get_performance_metrics(
    performance_service: PerformanceService = Depends(PerformanceService)
) -> Dict[str, Any]:
    """获取性能指标"""
    metrics = performance_service.get_performance_metrics()
    return metrics


@router.get("/cache")
def get_cache_info(
    performance_service: PerformanceService = Depends(PerformanceService)
) -> Dict[str, Any]:
    """获取缓存信息"""
    return {
        "cache_size": len(performance_service.cache),
        "cache_keys": list(performance_service.cache.keys())
    }


@router.post("/cache/clear")
def clear_cache(
    key: str = None,
    performance_service: PerformanceService = Depends(PerformanceService)
) -> Dict[str, Any]:
    """清理缓存"""
    performance_service.clear_cache(key)
    return {"message": "Cache cleared successfully"}


@router.get("/recommendation/models")
def get_recommendation_models(
    recommendation_service: RecommendationService = Depends(RecommendationService)
) -> Dict[str, Any]:
    """获取推荐模型信息"""
    model_info = recommendation_service.get_model_info()
    return model_info


@router.get("/system")
def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    import platform
    import sys
    import os
    
    return {
        "system": platform.system(),
        "version": platform.version(),
        "python_version": sys.version,
        "cpu_count": os.cpu_count(),
        "platform": platform.platform()
    }
