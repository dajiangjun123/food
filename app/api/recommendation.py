from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.services.recommendation_service import RecommendationService
from app.models.recommendation import (
    RecommendationRequest, RecommendationResponse, 
    ModelConfig, TrainingResult, AlgorithmMetrics
)
import uuid

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("/", response_model=RecommendationResponse)
def get_recommendations(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    algorithm: Optional[str] = Query(default=None, regex="^(collaborative_filtering|content_based|hybrid)$"),
    filters: Optional[Dict[str, Any]] = None,
    recommendation_service: RecommendationService = Depends(RecommendationService)
):
    """获取推荐结果"""
    try:
        # 构建过滤条件
        filter_dict = filters or {}
        if algorithm:
            filter_dict['algorithm'] = algorithm
        
        # 创建推荐请求
        request = RecommendationRequest(
            user_id=user_id,
            request_id=str(uuid.uuid4()),
            filters=filter_dict,
            limit=limit
        )
        
        # 获取推荐结果
        response = recommendation_service.recommend(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch", response_model=List[RecommendationResponse])
def get_batch_recommendations(
    requests: List[RecommendationRequest],
    recommendation_service: RecommendationService = Depends(RecommendationService)
):
    """批量获取推荐结果"""
    try:
        responses = []
        for request in requests:
            response = recommendation_service.recommend(request)
            responses.append(response)
        return responses
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/train/{model_name}", response_model=TrainingResult)
def train_model(
    model_name: str,
    data: Dict[str, Any],
    recommendation_service: RecommendationService = Depends(RecommendationService)
):
    """训练推荐模型"""
    try:
        result = recommendation_service.train_model(model_name, data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/evaluate/{algorithm}", response_model=AlgorithmMetrics)
def evaluate_algorithm(
    algorithm: str,
    test_data: Dict[str, Any],
    recommendation_service: RecommendationService = Depends(RecommendationService)
):
    """评估算法性能"""
    try:
        metrics = recommendation_service.evaluate_algorithm(algorithm, test_data)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models")
def get_models(
    model_name: Optional[str] = None,
    recommendation_service: RecommendationService = Depends(RecommendationService)
):
    """获取模型信息"""
    try:
        model_info = recommendation_service.get_model_info(model_name)
        return model_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/models/{model_name}")
def update_model_parameters(
    model_name: str,
    parameters: Dict[str, Any],
    recommendation_service: RecommendationService = Depends(RecommendationService)
):
    """更新模型参数"""
    try:
        success = recommendation_service.update_model_parameters(model_name, parameters)
        if not success:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        return {"message": f"Model {model_name} parameters updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/test")
def test_recommendation(
    user_id: str = "test_user",
    algorithm: str = "hybrid",
    recommendation_service: RecommendationService = Depends(RecommendationService)
):
    """测试推荐功能"""
    try:
        request = RecommendationRequest(
            user_id=user_id,
            request_id=str(uuid.uuid4()),
            filters={"algorithm": algorithm},
            limit=5
        )
        
        response = recommendation_service.recommend(request)
        return {
            "message": "Recommendation test successful",
            "algorithm": response.algorithm,
            "latency": response.latency,
            "recommendations": len(response.items)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
