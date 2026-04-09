from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.services.ab_test_service import ABTestService
from app.services.recommendation_service import RecommendationService
from app.models.ab_test import (
    ExperimentConfig, ExperimentCreate, ExperimentUpdate, 
    ExperimentStatus, UserAssignment, ExperimentEvent,
    ExperimentAnalysis, TrafficAllocation
)
import uuid

router = APIRouter(prefix="/api/ab-test", tags=["ab-test"])


@router.post("/experiments", response_model=ExperimentConfig)
def create_experiment(
    experiment: ExperimentCreate,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """创建实验"""
    try:
        experiment_data = experiment.model_dump()
        result = ab_test_service.create_experiment(experiment_data, created_by="system")
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/experiments/{experiment_id}", response_model=ExperimentConfig)
def get_experiment(
    experiment_id: str,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """获取实验配置"""
    try:
        experiment = ab_test_service.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return experiment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/experiments/{experiment_id}", response_model=ExperimentConfig)
def update_experiment(
    experiment_id: str,
    experiment_update: ExperimentUpdate,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """更新实验"""
    try:
        update_data = experiment_update.model_dump(exclude_unset=True)
        experiment = ab_test_service.update_experiment(experiment_id, update_data)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return experiment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/experiments")
def list_experiments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: Optional[ExperimentStatus] = None,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """列出实验"""
    try:
        result = ab_test_service.list_experiments(page=page, page_size=page_size, status=status)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/experiments/{experiment_id}/start")
def start_experiment(
    experiment_id: str,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """启动实验"""
    try:
        success = ab_test_service.start_experiment(experiment_id)
        if not success:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return {"message": "Experiment started successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/experiments/{experiment_id}/pause")
def pause_experiment(
    experiment_id: str,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """暂停实验"""
    try:
        success = ab_test_service.pause_experiment(experiment_id)
        if not success:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return {"message": "Experiment paused successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/experiments/{experiment_id}/complete")
def complete_experiment(
    experiment_id: str,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """完成实验"""
    try:
        success = ab_test_service.complete_experiment(experiment_id)
        if not success:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return {"message": "Experiment completed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/experiments/{experiment_id}/assign/{user_id}", response_model=UserAssignment)
def assign_user(
    experiment_id: str,
    user_id: str,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """用户分组分配"""
    try:
        assignment = ab_test_service.assign_user(user_id, experiment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Experiment not found or not running")
        return assignment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/experiments/{experiment_id}/assignments/{user_id}", response_model=UserAssignment)
def get_user_assignment(
    experiment_id: str,
    user_id: str,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """获取用户分组分配"""
    try:
        assignment = ab_test_service.get_user_assignment(user_id, experiment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return assignment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/events")
def track_event(
    event: ExperimentEvent,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """跟踪实验事件"""
    try:
        ab_test_service.track_event(event)
        return {"message": "Event tracked successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/experiments/{experiment_id}/analysis", response_model=ExperimentAnalysis)
def analyze_experiment(
    experiment_id: str,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """分析实验结果"""
    try:
        analysis = ab_test_service.analyze_experiment(experiment_id)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/experiments/{experiment_id}/stats")
def get_experiment_stats(
    experiment_id: str,
    ab_test_service: ABTestService = Depends(ABTestService)
):
    """获取实验统计信息"""
    try:
        stats = ab_test_service.get_experiment_stats(experiment_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/experiments/{experiment_id}/recommend/{user_id}")
def get_recommendation_with_ab_test(
    experiment_id: str,
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    ab_test_service: ABTestService = Depends(ABTestService),
    recommendation_service: RecommendationService = Depends(RecommendationService)
):
    """结合A/B测试的推荐"""
    try:
        # 获取用户分组分配
        assignment = ab_test_service.assign_user(user_id, experiment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Experiment not found or not running")
        
        # 根据分组策略进行推荐
        from app.models.recommendation import RecommendationRequest
        
        request = RecommendationRequest(
            user_id=user_id,
            request_id=str(uuid.uuid4()),
            filters={"algorithm": assignment.strategy_id},
            limit=limit
        )
        
        recommendation = recommendation_service.recommend(request)
        
        return {
            "experiment_id": experiment_id,
            "group_id": assignment.group_id,
            "group_name": assignment.group_name,
            "strategy_id": assignment.strategy_id,
            "recommendation": recommendation
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
