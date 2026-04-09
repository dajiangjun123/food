import logging
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from app.models.recommendation import (
    RecommendationRequest, RecommendationResponse, RecommendationItem,
    ModelConfig, TrainingResult, AlgorithmMetrics
)
from app.models.user_profile import UserProfile, UserPreferenceProfile
from app.models.dish_feature import DishFeature
from app.models.user_behavior import UserBehavior
from app.services.real_time_feature_service import RealTimeFeatureService
from app.services.performance_service import PerformanceService

logger = logging.getLogger(__name__)


class RecommendationService:
    """推荐算法服务"""
    
    def __init__(self):
        self.models = {}
        self.item_features = {}
        self.user_profiles = {}
        self.real_time_feature_service = RealTimeFeatureService()
        self.performance_service = PerformanceService()
        self._initialize_models()
    
    def _initialize_models(self):
        """初始化推荐模型"""
        # 协同过滤模型配置
        self.models['collaborative_filtering'] = {
            'name': 'collaborative_filtering',
            'type': 'user_based',
            'parameters': {'similarity_threshold': 0.3},
            'trained': False
        }
        
        # 内容推荐模型配置
        self.models['content_based'] = {
            'name': 'content_based',
            'type': 'feature_based',
            'parameters': {'feature_weight': 0.7},
            'trained': False
        }
        
        # 混合推荐模型配置
        self.models['hybrid'] = {
            'name': 'hybrid',
            'type': 'ensemble',
            'parameters': {'collaborative_weight': 0.6, 'content_weight': 0.4},
            'trained': True
        }
    
    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        """执行推荐"""
        # 使用性能优化装饰器
        return self._recommend_with_performance(request)
    
    def _recommend_with_performance(self, request: RecommendationRequest) -> RecommendationResponse:
        """带性能优化的推荐方法"""
        # 尝试从缓存获取结果
        cache_key = f"recommendation:{request.user_id}:{request.filters.get('algorithm', 'hybrid')}"
        cached_result = self.performance_service.get_cache(cache_key)
        if cached_result:
            return cached_result
        
        start_time = datetime.now()
        
        # 计算实时特征
        real_time_features = self.real_time_feature_service.calculate_real_time_features(
            request.user_id, request.context
        )
        
        # 获取用户画像
        user_profile = self._get_user_profile(request.user_id)
        
        # 根据算法类型选择推荐策略
        algorithm = request.filters.get('algorithm', 'hybrid')
        
        # 验证算法类型，无效算法回退到混合推荐
        if algorithm not in ['collaborative_filtering', 'content_based', 'hybrid']:
            algorithm = 'hybrid'
        
        # 根据实时特征调整推荐策略
        if real_time_features.get('is_active_today'):
            # 活跃用户使用更个性化的推荐
            if algorithm == 'hybrid':
                self.models['hybrid']['parameters']['collaborative_weight'] = 0.7
                self.models['hybrid']['parameters']['content_weight'] = 0.3
        
        if algorithm == 'collaborative_filtering':
            items = self._collaborative_filtering_recommend(request, user_profile)
        elif algorithm == 'content_based':
            items = self._content_based_recommend(request, user_profile)
        else:  # hybrid
            items = self._hybrid_recommend(request, user_profile)
        
        # 应用实时特征调整分数
        items = self._adjust_scores_with_real_time_features(items, real_time_features)
        
        # 应用过滤条件
        items = self._apply_filters(items, request.filters)
        
        # 限制返回数量
        items = items[:request.limit]
        
        # 计算延迟
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        response = RecommendationResponse(
            request_id=request.request_id,
            user_id=request.user_id,
            items=items,
            algorithm=algorithm,
            latency=latency
        )
        
        # 缓存结果（短期缓存，1分钟）
        self.performance_service.set_cache(cache_key, response, ttl=60)
        
        return response
    
    def _adjust_scores_with_real_time_features(self, items: List[RecommendationItem], 
                                            real_time_features: Dict[str, Any]) -> List[RecommendationItem]:
        """使用实时特征调整推荐分数"""
        adjusted_items = []
        
        # 根据时间特征调整分数
        if real_time_features.get('is_morning'):
            # 早餐时段提高早餐类菜品分数
            for item in items:
                adjusted_score = item.score * 1.1  # 提高10%
                adjusted_items.append(RecommendationItem(
                    dish_id=item.dish_id,
                    merchant_id=item.merchant_id,
                    score=min(adjusted_score, 1.0),
                    rank=item.rank,
                    reason=f"{item.reason}（早餐时段推荐）",
                    features=item.features
                ))
        elif real_time_features.get('is_evening'):
            # 晚餐时段提高晚餐类菜品分数
            for item in items:
                adjusted_score = item.score * 1.05  # 提高5%
                adjusted_items.append(RecommendationItem(
                    dish_id=item.dish_id,
                    merchant_id=item.merchant_id,
                    score=min(adjusted_score, 1.0),
                    rank=item.rank,
                    reason=f"{item.reason}（晚餐时段推荐）",
                    features=item.features
                ))
        else:
            adjusted_items = items
        
        # 根据用户活跃度调整分数
        if real_time_features.get('is_active_today'):
            # 活跃用户提高多样性
            for i, item in enumerate(adjusted_items):
                if i < len(adjusted_items) // 2:
                    # 前50%保持高分
                    pass
                else:
                    # 后50%提高分数以增加多样性
                    adjusted_score = item.score * 1.15
                    adjusted_items[i] = RecommendationItem(
                        dish_id=item.dish_id,
                        merchant_id=item.merchant_id,
                        score=min(adjusted_score, 1.0),
                        rank=item.rank,
                        reason=f"{item.reason}（多样性推荐）",
                        features=item.features
                    )
        
        return adjusted_items
    
    def _collaborative_filtering_recommend(self, request: RecommendationRequest, 
                                         user_profile: Optional[UserProfile]) -> List[RecommendationItem]:
        """协同过滤推荐"""
        items = []
        
        # 模拟协同过滤推荐逻辑
        # 实际实现应该基于用户-物品交互矩阵进行协同过滤
        mock_dishes = [
            {'dish_id': 'dish_101', 'merchant_id': 'merchant_101', 'score': 0.92},
            {'dish_id': 'dish_102', 'merchant_id': 'merchant_102', 'score': 0.87},
            {'dish_id': 'dish_103', 'merchant_id': 'merchant_103', 'score': 0.81},
            {'dish_id': 'dish_104', 'merchant_id': 'merchant_104', 'score': 0.75},
            {'dish_id': 'dish_105', 'merchant_id': 'merchant_105', 'score': 0.69}
        ]
        
        for i, dish in enumerate(mock_dishes, 1):
            items.append(RecommendationItem(
                dish_id=dish['dish_id'],
                merchant_id=dish['merchant_id'],
                score=dish['score'],
                rank=i,
                reason="基于协同过滤算法推荐"
            ))
        
        return items
    
    def _content_based_recommend(self, request: RecommendationRequest, 
                              user_profile: Optional[UserProfile]) -> List[RecommendationItem]:
        """基于内容的推荐"""
        items = []
        
        # 模拟基于内容的推荐逻辑
        # 实际实现应该基于菜品特征和用户偏好进行匹配
        mock_dishes = [
            {'dish_id': 'dish_201', 'merchant_id': 'merchant_201', 'score': 0.88},
            {'dish_id': 'dish_202', 'merchant_id': 'merchant_202', 'score': 0.83},
            {'dish_id': 'dish_203', 'merchant_id': 'merchant_203', 'score': 0.79},
            {'dish_id': 'dish_204', 'merchant_id': 'merchant_204', 'score': 0.74},
            {'dish_id': 'dish_205', 'merchant_id': 'merchant_205', 'score': 0.68}
        ]
        
        for i, dish in enumerate(mock_dishes, 1):
            items.append(RecommendationItem(
                dish_id=dish['dish_id'],
                merchant_id=dish['merchant_id'],
                score=dish['score'],
                rank=i,
                reason="基于内容相似性推荐"
            ))
        
        return items
    
    def _hybrid_recommend(self, request: RecommendationRequest, 
                        user_profile: Optional[UserProfile]) -> List[RecommendationItem]:
        """混合推荐"""
        # 获取不同算法的推荐结果
        cf_items = self._collaborative_filtering_recommend(request, user_profile)
        cb_items = self._content_based_recommend(request, user_profile)
        
        # 合并结果并重新排序
        combined_scores = {}
        
        # 应用权重
        collaborative_weight = self.models['hybrid']['parameters']['collaborative_weight']
        content_weight = self.models['hybrid']['parameters']['content_weight']
        
        # 合并协同过滤结果
        for item in cf_items:
            combined_scores[item.dish_id] = item.score * collaborative_weight
        
        # 合并内容推荐结果
        for item in cb_items:
            if item.dish_id in combined_scores:
                combined_scores[item.dish_id] += item.score * content_weight
            else:
                combined_scores[item.dish_id] = item.score * content_weight
        
        # 转换为推荐项列表并排序
        items = []
        for dish_id, score in sorted(combined_scores.items(), key=lambda x: x[1], reverse=True):
            # 获取商家ID（实际应该从数据库查询）
            merchant_id = f"merchant_{dish_id.split('_')[1]}"
            items.append(RecommendationItem(
                dish_id=dish_id,
                merchant_id=merchant_id,
                score=min(score, 1.0),  # 确保分数在0-1之间
                rank=len(items) + 1,
                reason="基于混合推荐算法"
            ))
        
        return items
    
    def _apply_filters(self, items: List[RecommendationItem], filters: Dict[str, Any]) -> List[RecommendationItem]:
        """应用过滤条件"""
        filtered_items = items
        
        # 价格过滤
        if 'min_price' in filters or 'max_price' in filters:
            # 实际应该查询菜品价格信息
            pass
        
        # 分类过滤
        if 'categories' in filters:
            # 实际应该查询菜品分类信息
            pass
        
        # 商家过滤
        if 'merchant_ids' in filters:
            filtered_items = [item for item in filtered_items 
                           if item.merchant_id in filters['merchant_ids']]
        
        # 重新排序
        for i, item in enumerate(filtered_items, 1):
            item.rank = i
        
        return filtered_items
    
    def _get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        # 实际应该从数据库查询
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        return None
    
    def train_model(self, model_name: str, data: Dict[str, Any]) -> TrainingResult:
        """训练推荐模型"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        start_time = datetime.now()
        
        # 模拟模型训练
        # 实际实现应该基于真实数据进行训练
        metrics = {
            'precision': 0.85,
            'recall': 0.78,
            'f1_score': 0.81,
            'ndcg': 0.88,
            'coverage': 0.72,
            'diversity': 0.65
        }
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # 更新模型状态
        self.models[model_name]['trained'] = True
        
        return TrainingResult(
            model_name=model_name,
            version=f"v{datetime.now().timestamp()}",
            metrics=metrics,
            training_time=training_time
        )
    
    def evaluate_algorithm(self, algorithm: str, test_data: Dict[str, Any]) -> AlgorithmMetrics:
        """评估算法性能"""
        # 模拟算法评估
        # 实际实现应该基于测试数据计算真实指标
        metrics = AlgorithmMetrics(
            precision=0.82,
            recall=0.76,
            f1_score=0.79,
            ndcg=0.86,
            coverage=0.70,
            diversity=0.63
        )
        
        return metrics
    
    def update_model_parameters(self, model_name: str, parameters: Dict[str, Any]) -> bool:
        """更新模型参数"""
        if model_name not in self.models:
            return False
        
        self.models[model_name]['parameters'].update(parameters)
        return True
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """获取模型信息"""
        if model_name:
            if model_name not in self.models:
                return {}
            return self.models[model_name]
        return self.models
