from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union


class RecommendationRequest(BaseModel):
    """推荐请求模型"""
    user_id: str = Field(..., description="用户ID")
    request_id: str = Field(..., description="请求ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="请求时间")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤条件")
    limit: int = Field(default=20, ge=1, le=100, description="返回结果数量")


class RecommendationItem(BaseModel):
    """推荐项模型"""
    dish_id: str = Field(..., description="菜品ID")
    merchant_id: str = Field(..., description="商家ID")
    score: float = Field(..., ge=0, le=1, description="推荐得分")
    rank: int = Field(..., ge=1, description="排名")
    reason: Optional[str] = Field(None, description="推荐理由")
    features: Optional[Dict[str, Any]] = Field(None, description="特征信息")


class RecommendationResponse(BaseModel):
    """推荐响应模型"""
    request_id: str = Field(..., description="请求ID")
    user_id: str = Field(..., description="用户ID")
    items: List[RecommendationItem] = Field(..., min_items=0, max_items=100, description="推荐结果列表")
    algorithm: str = Field(..., description="使用的算法")
    latency: float = Field(..., description="响应延迟(ms)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class ModelConfig(BaseModel):
    """模型配置"""
    model_name: str = Field(..., description="模型名称")
    model_type: str = Field(..., description="模型类型")
    version: str = Field(..., description="模型版本")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="模型参数")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")


class TrainingResult(BaseModel):
    """训练结果"""
    model_name: str = Field(..., description="模型名称")
    version: str = Field(..., description="模型版本")
    metrics: Dict[str, float] = Field(..., description="评估指标")
    training_time: float = Field(..., description="训练时间(秒)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="完成时间")


class AlgorithmMetrics(BaseModel):
    """算法评估指标"""
    precision: float = Field(..., ge=0, le=1, description="精确率")
    recall: float = Field(..., ge=0, le=1, description="召回率")
    f1_score: float = Field(..., ge=0, le=1, description="F1分数")
    ndcg: float = Field(..., ge=0, le=1, description="归一化折损累积增益")
    coverage: float = Field(..., ge=0, le=1, description="覆盖率")
    diversity: float = Field(..., ge=0, le=1, description="多样性")
