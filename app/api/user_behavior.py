from typing import List
from fastapi import APIRouter, HTTPException, Depends
from app.models.user_behavior import UserBehavior, UserBehaviorCreate, UserBehaviorBatch
from app.services.user_behavior_service import user_behavior_service
from app.core.logging_config import logger

router = APIRouter(
    prefix="/api/v1/user-behavior",
    tags=["user-behavior"]
)


@router.post("/collect", response_model=UserBehavior)
async def collect_user_behavior(behavior: UserBehaviorCreate):
    """采集单个用户行为"""
    try:
        result = user_behavior_service.collect_behavior(behavior)
        return result
    except Exception as e:
        logger.error(f"Failed to collect user behavior: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect user behavior")


@router.post("/collect-batch", response_model=List[UserBehavior])
async def collect_batch_user_behaviors(batch: UserBehaviorBatch):
    """批量采集用户行为"""
    try:
        results = user_behavior_service.collect_batch_behaviors(batch.behaviors)
        return results
    except Exception as e:
        logger.error(f"Failed to collect batch user behaviors: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect batch user behaviors")


@router.get("/{user_id}", response_model=List[UserBehavior])
async def get_user_behaviors(user_id: str, limit: int = 100):
    """获取用户行为历史"""
    try:
        behaviors = user_behavior_service.get_user_behaviors(user_id, limit)
        return behaviors
    except Exception as e:
        logger.error(f"Failed to get user behaviors: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user behaviors")