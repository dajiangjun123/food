from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.services.data_cleaning_service import data_cleaning_service
from app.core.logging_config import logger

router = APIRouter(
    prefix="/api/v1/data-processing",
    tags=["data-processing"]
)


@router.post("/clean/user-behavior", response_model=List[Dict[str, Any]])
async def clean_user_behavior_data(data: List[Dict[str, Any]]):
    """清洗用户行为数据"""
    try:
        cleaned_data = data_cleaning_service.clean_user_behavior_data(data)
        return cleaned_data
    except Exception as e:
        logger.error(f"Failed to clean user behavior data: {e}")
        raise HTTPException(status_code=500, detail="Failed to clean user behavior data")


@router.post("/clean/dish-feature", response_model=List[Dict[str, Any]])
async def clean_dish_feature_data(data: List[Dict[str, Any]]):
    """清洗菜品特征数据"""
    try:
        cleaned_data = data_cleaning_service.clean_dish_feature_data(data)
        return cleaned_data
    except Exception as e:
        logger.error(f"Failed to clean dish feature data: {e}")
        raise HTTPException(status_code=500, detail="Failed to clean dish feature data")


@router.post("/normalize", response_model=Dict[str, Any])
async def normalize_features(data: Dict[str, Any]):
    """标准化特征数据"""
    try:
        import pandas as pd
        
        df = pd.DataFrame(data['data'])
        numeric_columns = data.get('numeric_columns', [])
        
        if not numeric_columns:
            raise ValueError("numeric_columns is required")
        
        normalized_df = data_cleaning_service.normalize_features(df, numeric_columns)
        return {"normalized_data": normalized_df.to_dict('records')}
        
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to normalize features: {e}")
        raise HTTPException(status_code=500, detail="Failed to normalize features")


@router.post("/encode", response_model=Dict[str, Any])
async def encode_categorical_features(data: Dict[str, Any]):
    """编码分类特征"""
    try:
        import pandas as pd
        
        df = pd.DataFrame(data['data'])
        categorical_columns = data.get('categorical_columns', [])
        
        if not categorical_columns:
            raise ValueError("categorical_columns is required")
        
        encoded_df = data_cleaning_service.encode_categorical_features(df, categorical_columns)
        return {"encoded_data": encoded_df.to_dict('records')}
        
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to encode categorical features: {e}")
        raise HTTPException(status_code=500, detail="Failed to encode categorical features")