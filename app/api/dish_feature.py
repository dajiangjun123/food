from typing import List
from fastapi import APIRouter, HTTPException
from app.models.dish_feature import DishFeature, DishFeatureCreate, DishFeatureBatch
from app.services.dish_feature_service import dish_feature_service
from app.core.logging_config import logger

router = APIRouter(
    prefix="/api/v1/dish-feature",
    tags=["dish-feature"]
)


@router.post("/create", response_model=DishFeature)
async def create_dish_feature(feature: DishFeatureCreate):
    """创建菜品特征"""
    try:
        result = dish_feature_service.create_dish_feature(feature)
        return result
    except Exception as e:
        logger.error(f"Failed to create dish feature: {e}")
        raise HTTPException(status_code=500, detail="Failed to create dish feature")


@router.post("/create-batch", response_model=List[DishFeature])
async def create_batch_dish_features(batch: DishFeatureBatch):
    """批量创建菜品特征"""
    try:
        results = dish_feature_service.create_batch_features(batch.features)
        return results
    except Exception as e:
        logger.error(f"Failed to create batch dish features: {e}")
        raise HTTPException(status_code=500, detail="Failed to create batch dish features")


@router.put("/{dish_id}", response_model=DishFeature)
async def update_dish_feature(dish_id: str, feature: DishFeatureCreate):
    """更新菜品特征"""
    try:
        result = dish_feature_service.update_dish_feature(dish_id, feature)
        return result
    except ValueError as e:
        logger.error(f"Dish feature not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update dish feature: {e}")
        raise HTTPException(status_code=500, detail="Failed to update dish feature")


@router.get("/{dish_id}", response_model=DishFeature)
async def get_dish_feature(dish_id: str):
    """获取菜品特征"""
    try:
        result = dish_feature_service.get_dish_feature(dish_id)
        return result
    except ValueError as e:
        logger.error(f"Dish feature not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get dish feature: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dish feature")