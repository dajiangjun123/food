from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class DishFeatureBase(BaseModel):
    """菜品特征基础模型"""
    dish_id: str = Field(..., description="菜品ID")
    merchant_id: str = Field(..., description="商家ID")
    name: str = Field(..., description="菜品名称")
    price: float = Field(..., gt=0, description="菜品价格")
    category: str = Field(..., description="菜品分类")
    tags: List[str] = Field(default_factory=list, description="菜品标签")
    description: Optional[str] = Field(None, description="菜品描述")
    image_url: Optional[str] = Field(None, description="菜品图片URL")
    sales_volume: int = Field(default=0, ge=0, description="销量")
    rating: Optional[float] = Field(None, ge=0, le=5, description="评分")
    review_count: int = Field(default=0, ge=0, description="评价数量")


class DishFeatureCreate(DishFeatureBase):
    """创建菜品特征模型"""
    pass


class DishFeature(DishFeatureBase):
    """菜品特征响应模型"""
    id: str = Field(..., description="特征记录ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    text_features: Optional[Dict[str, float]] = Field(None, description="文本特征向量")
    image_features: Optional[List[float]] = Field(None, description="图像特征向量")
    
    class Config:
        from_attributes = True


class DishFeatureBatch(BaseModel):
    """批量菜品特征模型"""
    features: List[DishFeatureCreate] = Field(..., min_items=1, max_items=100, description="菜品特征列表")