from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ExperimentStatus(str, Enum):
    """实验状态"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TrafficAllocation(BaseModel):
    """流量分配配置"""
    group_id: str = Field(..., description="分组ID")
    group_name: str = Field(..., description="分组名称")
    traffic_percentage: float = Field(..., ge=0, le=100, description="流量百分比")
    strategy_id: str = Field(..., description="策略ID")


class ExperimentConfig(BaseModel):
    """实验配置"""
    experiment_id: str = Field(..., description="实验ID")
    name: str = Field(..., description="实验名称")
    description: Optional[str] = Field(None, description="实验描述")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    status: ExperimentStatus = Field(default=ExperimentStatus.DRAFT, description="实验状态")
    traffic_allocations: List[TrafficAllocation] = Field(..., min_items=2, description="流量分配配置")
    metrics: List[str] = Field(default_factory=lambda: ["ctr", "cvr", "gmv"], description="评估指标")
    created_by: str = Field(..., description="创建者")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")


class ExperimentResult(BaseModel):
    """实验结果"""
    experiment_id: str = Field(..., description="实验ID")
    group_id: str = Field(..., description="分组ID")
    group_name: str = Field(..., description="分组名称")
    metrics: Dict[str, float] = Field(..., description="评估指标")
    sample_size: int = Field(..., description="样本数量")
    confidence_interval: Dict[str, List[float]] = Field(default_factory=dict, description="置信区间")
    p_value: float = Field(..., description="显著性检验p值")
    is_significant: bool = Field(..., description="是否显著")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="统计时间")


class UserAssignment(BaseModel):
    """用户分组分配"""
    user_id: str = Field(..., description="用户ID")
    experiment_id: str = Field(..., description="实验ID")
    group_id: str = Field(..., description="分组ID")
    group_name: str = Field(..., description="分组名称")
    strategy_id: str = Field(..., description="策略ID")
    assigned_at: datetime = Field(default_factory=datetime.utcnow, description="分配时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class ExperimentEvent(BaseModel):
    """实验事件"""
    event_id: str = Field(..., description="事件ID")
    user_id: str = Field(..., description="用户ID")
    experiment_id: str = Field(..., description="实验ID")
    group_id: str = Field(..., description="分组ID")
    event_type: str = Field(..., description="事件类型")
    event_value: Optional[float] = Field(None, description="事件值")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="事件时间")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")


class ExperimentCreate(BaseModel):
    """创建实验请求"""
    name: str = Field(..., description="实验名称")
    description: Optional[str] = Field(None, description="实验描述")
    traffic_allocations: List[TrafficAllocation] = Field(..., min_items=2, description="流量分配配置")
    metrics: List[str] = Field(default_factory=lambda: ["ctr", "cvr", "gmv"], description="评估指标")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class ExperimentUpdate(BaseModel):
    """更新实验请求"""
    name: Optional[str] = Field(None, description="实验名称")
    description: Optional[str] = Field(None, description="实验描述")
    status: Optional[ExperimentStatus] = Field(None, description="实验状态")
    traffic_allocations: Optional[List[TrafficAllocation]] = Field(None, description="流量分配配置")
    metrics: Optional[List[str]] = Field(None, description="评估指标")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class ExperimentList(BaseModel):
    """实验列表响应"""
    experiments: List[ExperimentConfig] = Field(..., description="实验列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class ExperimentAnalysis(BaseModel):
    """实验分析结果"""
    experiment_id: str = Field(..., description="实验ID")
    results: List[ExperimentResult] = Field(..., description="分组结果")
    winning_group_id: Optional[str] = Field(None, description="获胜分组ID")
    winning_metric: Optional[str] = Field(None, description="获胜指标")
    improvement: Optional[float] = Field(None, description="提升百分比")
    analysis_time: datetime = Field(default_factory=datetime.utcnow, description="分析时间")
