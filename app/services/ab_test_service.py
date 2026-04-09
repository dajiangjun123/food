import logging
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import uuid
from app.models.ab_test import (
    ExperimentConfig, ExperimentStatus, TrafficAllocation,
    UserAssignment, ExperimentEvent, ExperimentResult,
    ExperimentAnalysis
)
from app.core.database import mongo_db
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)


class ABTestService:
    """A/B测试服务"""
    
    def __init__(self):
        self.experiments_collection = mongo_db['experiments'] if mongo_db else None
        self.assignments_collection = mongo_db['user_assignments'] if mongo_db else None
        self.events_collection = mongo_db['experiment_events'] if mongo_db else None
        self.use_mongo = mongo_db is not None
        
        # 内存存储（用于测试环境）
        self.memory_experiments = {}
        self.memory_assignments = {}
        self.memory_events = []
    
    def create_experiment(self, experiment_data: Dict[str, Any], created_by: str) -> ExperimentConfig:
        """创建实验"""
        try:
            experiment_id = str(uuid.uuid4())
            
            experiment = ExperimentConfig(
                experiment_id=experiment_id,
                name=experiment_data['name'],
                description=experiment_data.get('description'),
                start_time=experiment_data.get('start_time', datetime.utcnow()),
                end_time=experiment_data.get('end_time'),
                status=ExperimentStatus.DRAFT,
                traffic_allocations=experiment_data['traffic_allocations'],
                metrics=experiment_data.get('metrics', ["ctr", "cvr", "gmv"]),
                created_by=created_by
            )
            
            if self.use_mongo:
                experiment_dict = experiment.model_dump()
                experiment_dict['_id'] = ObjectId()
                self.experiments_collection.insert_one(experiment_dict)
            else:
                self.memory_experiments[experiment_id] = experiment
            
            return experiment
            
        except Exception as e:
            logger.error(f"创建实验失败: {e}")
            raise
    
    def get_experiment(self, experiment_id: str) -> Optional[ExperimentConfig]:
        """获取实验配置"""
        try:
            if self.use_mongo:
                experiment_dict = self.experiments_collection.find_one({"experiment_id": experiment_id})
                if experiment_dict:
                    experiment_dict['experiment_id'] = str(experiment_dict['experiment_id'])
                    del experiment_dict['_id']
                    return ExperimentConfig(**experiment_dict)
            else:
                return self.memory_experiments.get(experiment_id)
                
            return None
            
        except Exception as e:
            logger.error(f"获取实验失败: {e}")
            raise
    
    def update_experiment(self, experiment_id: str, update_data: Dict[str, Any]) -> Optional[ExperimentConfig]:
        """更新实验"""
        try:
            experiment = self.get_experiment(experiment_id)
            if not experiment:
                return None
            
            # 更新字段
            if 'name' in update_data:
                experiment.name = update_data['name']
            if 'description' in update_data:
                experiment.description = update_data['description']
            if 'status' in update_data:
                experiment.status = update_data['status']
            if 'traffic_allocations' in update_data:
                experiment.traffic_allocations = update_data['traffic_allocations']
            if 'metrics' in update_data:
                experiment.metrics = update_data['metrics']
            if 'end_time' in update_data:
                experiment.end_time = update_data['end_time']
            
            experiment.updated_at = datetime.utcnow()
            
            if self.use_mongo:
                self.experiments_collection.update_one(
                    {"experiment_id": experiment_id},
                    {"$set": experiment.model_dump()}
                )
            else:
                self.memory_experiments[experiment_id] = experiment
            
            return experiment
            
        except Exception as e:
            logger.error(f"更新实验失败: {e}")
            raise
    
    def list_experiments(self, page: int = 1, page_size: int = 10, 
                        status: Optional[ExperimentStatus] = None) -> Dict[str, Any]:
        """列出实验"""
        try:
            experiments = []
            
            if self.use_mongo:
                query = {}
                if status:
                    query['status'] = status
                
                total = self.experiments_collection.count_documents(query)
                cursor = self.experiments_collection.find(query).skip(
                    (page - 1) * page_size
                ).limit(page_size)
                
                for experiment_dict in cursor:
                    experiment_dict['experiment_id'] = str(experiment_dict['experiment_id'])
                    del experiment_dict['_id']
                    experiments.append(ExperimentConfig(**experiment_dict))
            else:
                all_experiments = list(self.memory_experiments.values())
                if status:
                    all_experiments = [e for e in all_experiments if e.status == status]
                
                total = len(all_experiments)
                start = (page - 1) * page_size
                end = start + page_size
                experiments = all_experiments[start:end]
            
            return {
                'experiments': experiments,
                'total': total,
                'page': page,
                'page_size': page_size
            }
            
        except Exception as e:
            logger.error(f"列出实验失败: {e}")
            raise
    
    def assign_user(self, user_id: str, experiment_id: str) -> Optional[UserAssignment]:
        """用户分组分配"""
        try:
            experiment = self.get_experiment(experiment_id)
            if not experiment or experiment.status != ExperimentStatus.RUNNING:
                return None
            
            # 检查是否已经分配
            assignment = self.get_user_assignment(user_id, experiment_id)
            if assignment:
                return assignment
            
            # 根据流量分配进行分组
            group_id = self._determine_group(user_id, experiment.traffic_allocations)
            group = next(g for g in experiment.traffic_allocations if g.group_id == group_id)
            
            assignment = UserAssignment(
                user_id=user_id,
                experiment_id=experiment_id,
                group_id=group_id,
                group_name=group.group_name,
                strategy_id=group.strategy_id
            )
            
            if self.use_mongo:
                self.assignments_collection.insert_one(assignment.model_dump())
            else:
                key = f"{user_id}:{experiment_id}"
                self.memory_assignments[key] = assignment
            
            return assignment
            
        except Exception as e:
            logger.error(f"用户分组分配失败: {e}")
            raise
    
    def get_user_assignment(self, user_id: str, experiment_id: str) -> Optional[UserAssignment]:
        """获取用户分组分配"""
        try:
            if self.use_mongo:
                assignment_dict = self.assignments_collection.find_one({
                    "user_id": user_id,
                    "experiment_id": experiment_id
                })
                if assignment_dict:
                    return UserAssignment(**assignment_dict)
            else:
                key = f"{user_id}:{experiment_id}"
                return self.memory_assignments.get(key)
                
            return None
            
        except Exception as e:
            logger.error(f"获取用户分组失败: {e}")
            raise
    
    def track_event(self, event: ExperimentEvent):
        """跟踪实验事件"""
        try:
            if self.use_mongo:
                self.events_collection.insert_one(event.model_dump())
            else:
                self.memory_events.append(event)
                
        except Exception as e:
            logger.error(f"跟踪事件失败: {e}")
            raise
    
    def analyze_experiment(self, experiment_id: str) -> ExperimentAnalysis:
        """分析实验结果"""
        try:
            experiment = self.get_experiment(experiment_id)
            if not experiment:
                raise ValueError(f"实验不存在: {experiment_id}")
            
            # 获取所有分组的结果
            results = []
            for group in experiment.traffic_allocations:
                group_result = self._calculate_group_metrics(experiment_id, group.group_id)
                results.append(group_result)
            
            # 确定获胜分组
            winning_group_id, winning_metric, improvement = self._determine_winning_group(results)
            
            return ExperimentAnalysis(
                experiment_id=experiment_id,
                results=results,
                winning_group_id=winning_group_id,
                winning_metric=winning_metric,
                improvement=improvement
            )
            
        except Exception as e:
            logger.error(f"分析实验失败: {e}")
            raise
    
    def _determine_group(self, user_id: str, allocations: List[TrafficAllocation]) -> str:
        """根据用户ID和流量分配确定分组"""
        # 使用哈希算法确保相同用户总是分配到相同分组
        hash_key = f"{user_id}"
        hash_value = int(hashlib.md5(hash_key.encode()).hexdigest(), 16) % 100
        
        cumulative = 0
        for allocation in allocations:
            cumulative += allocation.traffic_percentage
            if hash_value < cumulative:
                return allocation.group_id
        
        # 默认返回最后一个分组
        return allocations[-1].group_id
    
    def _calculate_group_metrics(self, experiment_id: str, group_id: str) -> ExperimentResult:
        """计算分组指标"""
        try:
            # 获取分组配置
            experiment = self.get_experiment(experiment_id)
            group = next(g for g in experiment.traffic_allocations if g.group_id == group_id)
            
            # 统计事件数据（模拟）
            if self.use_mongo:
                # 实际应该从数据库查询
                pass
            else:
                # 模拟数据
                metrics = {
                    "ctr": random.uniform(0.02, 0.08),
                    "cvr": random.uniform(0.05, 0.15),
                    "gmv": random.uniform(50, 200)
                }
                sample_size = random.randint(1000, 10000)
            
            # 计算置信区间（简化版）
            confidence_interval = {}
            for metric, value in metrics.items():
                margin = value * 0.1  # 10% margin
                confidence_interval[metric] = [value - margin, value + margin]
            
            # 计算p值（简化版）
            p_value = random.uniform(0.01, 0.1)
            is_significant = p_value < 0.05
            
            return ExperimentResult(
                experiment_id=experiment_id,
                group_id=group_id,
                group_name=group.group_name,
                metrics=metrics,
                sample_size=sample_size,
                confidence_interval=confidence_interval,
                p_value=p_value,
                is_significant=is_significant
            )
            
        except Exception as e:
            logger.error(f"计算分组指标失败: {e}")
            raise
    
    def _determine_winning_group(self, results: List[ExperimentResult]) -> tuple:
        """确定获胜分组"""
        if not results:
            return None, None, None
        
        # 按CTR指标比较
        ctr_results = [(r.group_id, r.metrics.get('ctr', 0)) for r in results]
        winning_group_id = max(ctr_results, key=lambda x: x[1])[0]
        
        winning_group = next(r for r in results if r.group_id == winning_group_id)
        baseline_group = next(r for r in results if r.group_id != winning_group_id)
        
        winning_metric = 'ctr'
        improvement = ((winning_group.metrics['ctr'] - baseline_group.metrics['ctr']) / 
                      baseline_group.metrics['ctr'] * 100)
        
        return winning_group_id, winning_metric, improvement
    
    def start_experiment(self, experiment_id: str) -> bool:
        """启动实验"""
        try:
            return self.update_experiment(experiment_id, {"status": ExperimentStatus.RUNNING}) is not None
        except Exception as e:
            logger.error(f"启动实验失败: {e}")
            return False
    
    def pause_experiment(self, experiment_id: str) -> bool:
        """暂停实验"""
        try:
            return self.update_experiment(experiment_id, {"status": ExperimentStatus.PAUSED}) is not None
        except Exception as e:
            logger.error(f"暂停实验失败: {e}")
            return False
    
    def complete_experiment(self, experiment_id: str) -> bool:
        """完成实验"""
        try:
            return self.update_experiment(experiment_id, {"status": ExperimentStatus.COMPLETED}) is not None
        except Exception as e:
            logger.error(f"完成实验失败: {e}")
            return False
    
    def get_experiment_stats(self, experiment_id: str) -> Dict[str, Any]:
        """获取实验统计信息"""
        try:
            experiment = self.get_experiment(experiment_id)
            if not experiment:
                return {}
            
            # 统计每个分组的用户数量
            group_stats = {}
            for group in experiment.traffic_allocations:
                if self.use_mongo:
                    user_count = self.assignments_collection.count_documents({
                        "experiment_id": experiment_id,
                        "group_id": group.group_id
                    })
                else:
                    user_count = sum(1 for a in self.memory_assignments.values() 
                                   if a.experiment_id == experiment_id and a.group_id == group.group_id)
                
                group_stats[group.group_id] = {
                    "group_name": group.group_name,
                    "user_count": user_count,
                    "traffic_percentage": group.traffic_percentage
                }
            
            return {
                "experiment_id": experiment_id,
                "status": experiment.status,
                "start_time": experiment.start_time,
                "end_time": experiment.end_time,
                "group_stats": group_stats,
                "total_users": sum(g["user_count"] for g in group_stats.values())
            }
            
        except Exception as e:
            logger.error(f"获取实验统计信息失败: {e}")
            raise
