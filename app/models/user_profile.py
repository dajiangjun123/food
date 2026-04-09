from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union


class UserProfileBase(BaseModel):
    """用户画像基础模型"""
    user_id: str = Field(..., description="用户ID")
    profile_type: str = Field(..., description="画像类型：basic, preference, behavioral, demographic")
    tags: Dict[str, Union[str, float, int]] = Field(default_factory=dict, description="用户标签及权重")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")


class UserProfileCreate(UserProfileBase):
    """创建用户画像模型"""
    pass


class UserProfile(UserProfileBase):
    """用户画像响应模型"""
    id: str = Field(..., description="画像记录ID")
    
    class Config:
        from_attributes = True


class UserPreferenceProfile(UserProfile):
    """用户偏好画像模型"""
    food_preferences: Dict[str, float] = Field(default_factory=dict, description="菜品偏好")
    price_sensitivity: float = Field(default=0.5, ge=0, le=1, description="价格敏感度")
    taste_preferences: Dict[str, float] = Field(default_factory=dict, description="口味偏好")
    dining_frequency: float = Field(default=0, ge=0, description="就餐频率")
    favorite_categories: List[str] = Field(default_factory=list, description="喜爱的菜品分类")


class UserSegment(BaseModel):
    """用户分群模型"""
    segment_id: str = Field(..., description="分群ID")
    segment_name: str = Field(..., description="分群名称")
    segment_description: str = Field(..., description="分群描述")
    user_count: int = Field(default=0, description="分群用户数量")
    characteristics: Dict[str, Any] = Field(default_factory=dict, description="分群特征")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")


class UserProfileUpdate(BaseModel):
    """用户画像更新模型"""
    tags: Optional[Dict[str, Union[str, float, int]]] = None
    food_preferences: Optional[Dict[str, float]] = None
    price_sensitivity: Optional[float] = None
    taste_preferences: Optional[Dict[str, float]] = None
    favorite_categories: Optional[List[str]] = None


class UserProfileBatch(BaseModel):
    """批量用户画像模型"""
    profiles: List[UserProfileCreate] = Field(..., min_items=1, max_items=100, description="用户画像列表")
