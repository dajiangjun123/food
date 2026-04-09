import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.models.user_profile import UserProfile, UserProfileCreate, UserProfileUpdate, UserPreferenceProfile, UserSegment
from app.models.user_behavior import UserBehavior
from app.models.dish_feature import DishFeature
from app.core.database import mongo_db
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)


class UserProfileService:
    """用户画像服务"""
    
    def __init__(self):
        self.collection = mongo_db['user_profiles'] if mongo_db else None
        self.use_mongo = mongo_db is not None
    
    def create_profile(self, profile_data: UserProfileCreate) -> UserProfile:
        """创建用户画像"""
        try:
            if not self.use_mongo:
                logger.warning("MongoDB not available, cannot create profile")
                return self._create_in_memory_profile(profile_data)
            
            # 创建用户画像
            profile_dict = profile_data.model_dump()
            profile_dict['_id'] = ObjectId()
            
            result = self.collection.insert_one(profile_dict)
            profile_dict['id'] = str(result.inserted_id)
            del profile_dict['_id']
            
            return UserProfile(**profile_dict)
        except Exception as e:
            logger.error(f"创建用户画像失败: {e}")
            raise
    
    def get_profile(self, user_id: str, profile_type: Optional[str] = None) -> Optional[UserProfile]:
        """获取用户画像"""
        try:
            if not self.use_mongo:
                logger.warning("MongoDB not available, cannot get profile")
                return None
            
            query = {"user_id": user_id}
            if profile_type:
                query["profile_type"] = profile_type
            
            profile_dict = self.collection.find_one(query)
            if profile_dict:
                profile_dict['id'] = str(profile_dict['_id'])
                del profile_dict['_id']
                return UserProfile(**profile_dict)
            return None
        except Exception as e:
            logger.error(f"获取用户画像失败: {e}")
            raise
    
    def update_profile(self, user_id: str, profile_update: UserProfileUpdate) -> Optional[UserProfile]:
        """更新用户画像"""
        try:
            if not self.use_mongo:
                logger.warning("MongoDB not available, cannot update profile")
                return None
            
            update_data = profile_update.model_dump(exclude_unset=True)
            update_data['updated_at'] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return self.get_profile(user_id)
            return None
        except Exception as e:
            logger.error(f"更新用户画像失败: {e}")
            raise
    
    def build_preference_profile(self, user_id: str, user_behaviors: List[UserBehavior]) -> UserPreferenceProfile:
        """基于用户行为数据构建偏好画像"""
        try:
            # 统计菜品偏好
            food_preferences = self._calculate_food_preferences(user_behaviors)
            
            # 计算价格敏感度
            price_sensitivity = self._calculate_price_sensitivity(user_behaviors)
            
            # 分析口味偏好
            taste_preferences = self._calculate_taste_preferences(user_behaviors)
            
            # 计算就餐频率
            dining_frequency = self._calculate_dining_frequency(user_behaviors)
            
            # 提取喜爱的菜品分类
            favorite_categories = self._extract_favorite_categories(user_behaviors)
            
            # 构建标签体系
            tags = self._build_user_tags(food_preferences, price_sensitivity, dining_frequency)
            
            profile = UserPreferenceProfile(
                id=str(ObjectId()),
                user_id=user_id,
                profile_type="preference",
                tags=tags,
                food_preferences=food_preferences,
                price_sensitivity=price_sensitivity,
                taste_preferences=taste_preferences,
                dining_frequency=dining_frequency,
                favorite_categories=favorite_categories,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            if self.use_mongo:
                profile_dict = profile.model_dump()
                profile_dict['_id'] = ObjectId(profile.id)
                del profile_dict['id']
                self.collection.insert_one(profile_dict)
            
            return profile
        except Exception as e:
            logger.error(f"构建用户偏好画像失败: {e}")
            raise
    
    def segment_users(self, profiles: List[UserProfile]) -> List[UserSegment]:
        """用户分群"""
        try:
            segments = []
            
            # 基于就餐频率分群
            high_frequency_users = [p for p in profiles if p.tags.get('high_frequency', 0) > 0.7]
            mid_frequency_users = [p for p in profiles if 0.3 <= p.tags.get('high_frequency', 0) <= 0.7]
            low_frequency_users = [p for p in profiles if p.tags.get('high_frequency', 0) < 0.3]
            
            # 基于价格敏感度分群
            price_sensitive_users = []
            mid_price_users = []
            price_insensitive_users = []
            
            for p in profiles:
                if hasattr(p, 'price_sensitivity'):
                    if p.price_sensitivity > 0.7:
                        price_sensitive_users.append(p)
                    elif 0.3 <= p.price_sensitivity <= 0.7:
                        mid_price_users.append(p)
                    else:
                        price_insensitive_users.append(p)
                elif 'price_sensitivity' in p.tags and isinstance(p.tags['price_sensitivity'], (int, float)):
                    if p.tags['price_sensitivity'] > 0.7:
                        price_sensitive_users.append(p)
                    elif 0.3 <= p.tags['price_sensitivity'] <= 0.7:
                        mid_price_users.append(p)
                    else:
                        price_insensitive_users.append(p)
                elif 'price_sensitive' in p.tags and isinstance(p.tags['price_sensitive'], (int, float)):
                    if p.tags['price_sensitive'] > 0.7:
                        price_sensitive_users.append(p)
                    elif 0.3 <= p.tags['price_sensitive'] <= 0.7:
                        mid_price_users.append(p)
                    else:
                        price_insensitive_users.append(p)
            
            # 创建分群
            segments.append(UserSegment(
                segment_id="high_frequency",
                segment_name="高频用户",
                segment_description="每周下单次数超过5次的用户",
                user_count=len(high_frequency_users),
                characteristics={"behavioral": "high_engagement"}
            ))
            
            segments.append(UserSegment(
                segment_id="price_sensitive",
                segment_name="价格敏感用户",
                segment_description="对价格非常敏感的用户",
                user_count=len(price_sensitive_users),
                characteristics={"economic": "price_conscious"}
            ))
            
            return segments
        except Exception as e:
            logger.error(f"用户分群失败: {e}")
            raise
    
    def update_profile_batch(self, user_profiles: List[Dict[str, Any]]) -> int:
        """批量更新用户画像"""
        try:
            if not self.use_mongo:
                logger.warning("MongoDB not available, cannot update profiles in batch")
                return 0
            
            updated_count = 0
            for profile_data in user_profiles:
                user_id = profile_data.get('user_id')
                if user_id:
                    update_data = {k: v for k, v in profile_data.items() if k != 'user_id'}
                    update_data['updated_at'] = datetime.utcnow()
                    
                    result = self.collection.update_one(
                        {"user_id": user_id},
                        {"$set": update_data},
                        upsert=True
                    )
                    if result.modified_count > 0 or result.upserted_id:
                        updated_count += 1
            
            return updated_count
        except Exception as e:
            logger.error(f"批量更新用户画像失败: {e}")
            raise
    
    def _calculate_food_preferences(self, behaviors: List[UserBehavior]) -> Dict[str, float]:
        """计算菜品偏好"""
        preferences = {}
        behavior_count = len(behaviors)
        
        if behavior_count == 0:
            return preferences
        
        # 统计每个菜品的行为次数
        for behavior in behaviors:
            if behavior.dish_id:
                preferences[behavior.dish_id] = preferences.get(behavior.dish_id, 0) + 1
        
        # 归一化偏好权重
        for dish_id in preferences:
            preferences[dish_id] = preferences[dish_id] / behavior_count
        
        return preferences
    
    def _calculate_price_sensitivity(self, behaviors: List[UserBehavior]) -> float:
        """计算价格敏感度"""
        if not behaviors:
            return 0.5
        
        # 简化的价格敏感度计算（实际应该结合菜品价格信息）
        # 这里使用行为频率作为代理
        recent_behaviors = [b for b in behaviors if b.timestamp > datetime.utcnow() - timedelta(days=30)]
        if not recent_behaviors:
            return 0.5
        
        # 假设订单频率与价格敏感度负相关
        frequency_score = min(len(recent_behaviors) / 10, 1.0)
        return 1.0 - frequency_score
    
    def _calculate_taste_preferences(self, behaviors: List[UserBehavior]) -> Dict[str, float]:
        """计算口味偏好"""
        # 实际应该结合菜品特征数据
        # 这里简化处理
        preferences = {"spicy": 0.0, "sweet": 0.0, "salty": 0.0, "sour": 0.0}
        return preferences
    
    def _calculate_dining_frequency(self, behaviors: List[UserBehavior]) -> float:
        """计算就餐频率"""
        if not behaviors:
            return 0.0
        
        # 计算最近30天的行为次数
        recent_behaviors = [b for b in behaviors if b.timestamp > datetime.utcnow() - timedelta(days=30)]
        return len(recent_behaviors) / 30.0
    
    def _extract_favorite_categories(self, behaviors: List[UserBehavior]) -> List[str]:
        """提取喜爱的菜品分类"""
        # 实际应该结合菜品特征数据
        # 这里返回空列表
        return []
    
    def _build_user_tags(self, food_preferences: Dict[str, float], 
                       price_sensitivity: float, 
                       dining_frequency: float) -> Dict[str, float]:
        """构建用户标签体系"""
        tags = {}
        
        # 频率标签
        if dining_frequency > 0.5:
            tags['high_frequency'] = 1.0
        elif dining_frequency > 0.2:
            tags['mid_frequency'] = 1.0
        else:
            tags['low_frequency'] = 1.0
        
        # 价格敏感度标签
        if price_sensitivity > 0.7:
            tags['price_sensitive'] = 1.0
        elif price_sensitivity > 0.3:
            tags['mid_price'] = 1.0
        else:
            tags['price_insensitive'] = 1.0
        
        # 活跃度标签
        if len(food_preferences) > 10:
            tags['active_explorer'] = 1.0
        elif len(food_preferences) > 3:
            tags['moderate_explorer'] = 1.0
        else:
            tags['conservative'] = 1.0
        
        return tags
    
    def _create_in_memory_profile(self, profile_data: UserProfileCreate) -> UserProfile:
        """在内存中创建用户画像（用于测试）"""
        return UserProfile(
            id="in_memory_profile",
            **profile_data.model_dump()
        )
