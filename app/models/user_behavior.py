from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class UserBehaviorBase(BaseModel):
    """用户行为基础模型"""
    user_id: str = Field(..., description="用户ID")
    behavior_type: str = Field(..., description="行为类型：click, view, order, rate, favorite, share")
    dish_id: Optional[str] = Field(None, description="菜品ID")
    merchant_id: Optional[str] = Field(None, description="商家ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="行为时间戳")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")


class UserBehaviorCreate(UserBehaviorBase):
    """创建用户行为模型"""
    pass


class UserBehavior(UserBehaviorBase):
    """用户行为响应模型"""
    id: str = Field(..., description="行为记录ID")
    
    class Config:
        from_attributes = True


class UserBehaviorBatch(BaseModel):
    """批量用户行为模型"""
    behaviors: List[UserBehaviorCreate] = Field(..., min_items=1, max_items=1000, description="用户行为列表")