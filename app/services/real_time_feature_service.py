import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import numpy as np
import redis
from app.core.settings import settings
from app.models.user_behavior import UserBehavior
from app.models.user_profile import UserProfile
from app.models.dish_feature import DishFeature

logger = logging.getLogger(__name__)


class RealTimeFeatureService:
    """实时特征计算服务"""
    
    def __init__(self):
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            self.redis_client = None
    
    def calculate_real_time_features(self, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """计算实时特征"""
        features = {}
        
        # 计算时间特征
        features.update(self._calculate_time_features())
        
        # 计算用户活跃度特征
        features.update(self._calculate_user_activity_features(user_id))
        
        # 计算上下文特征
        features.update(self._calculate_context_features(context))
        
        # 计算会话特征
        features.update(self._calculate_session_features(user_id))
        
        return features
    
    def _calculate_time_features(self) -> Dict[str, Any]:
        """计算时间相关特征"""
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()
        
        # 时间特征
        time_features = {
            'hour': hour,
            'is_weekend': day_of_week >= 5,
            'is_morning': 6 <= hour < 12,
            'is_afternoon': 12 <= hour < 18,
            'is_evening': 18 <= hour < 22,
            'is_night': hour >= 22 or hour < 6
        }
        
        return time_features
    
    def _calculate_user_activity_features(self, user_id: str) -> Dict[str, Any]:
        """计算用户活跃度特征"""
        activity_features = {
            'recent_order_count': 0,
            'recent_view_count': 0,
            'avg_order_interval': 0,
            'is_active_today': False
        }
        
        if not self.redis_client:
            return activity_features
        
        try:
            # 获取最近24小时的订单数
            order_key = f"user:{user_id}:orders:24h"
            activity_features['recent_order_count'] = int(self.redis_client.get(order_key) or 0)
            
            # 获取最近24小时的浏览数
            view_key = f"user:{user_id}:views:24h"
            activity_features['recent_view_count'] = int(self.redis_client.get(view_key) or 0)
            
            # 检查今天是否活跃
            today_key = f"user:{user_id}:active:today"
            activity_features['is_active_today'] = self.redis_client.exists(today_key) > 0
            
        except Exception as e:
            logger.error(f"计算用户活跃度特征失败: {e}")
        
        return activity_features
    
    def _calculate_context_features(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """计算上下文特征"""
        context_features = {}
        
        # 位置特征
        if 'location' in context:
            location = context['location']
            if isinstance(location, dict):
                context_features['location_city'] = location.get('city', '')
                context_features['location_district'] = location.get('district', '')
            elif isinstance(location, str):
                context_features['location_city'] = location
                context_features['location_district'] = ''
        
        # 设备特征
        if 'device' in context:
            device = context['device']
            if isinstance(device, dict):
                context_features['device_type'] = device.get('type', '')
                context_features['device_os'] = device.get('os', '')
        
        # 网络特征
        if 'network' in context:
            network = context['network']
            if isinstance(network, dict):
                context_features['network_type'] = network.get('type', '')
        
        # 时间特征（字符串格式）
        if 'time' in context:
            time_str = context['time']
            if isinstance(time_str, str):
                context_features['time_of_day'] = time_str
        
        return context_features
    
    def _calculate_session_features(self, user_id: str) -> Dict[str, Any]:
        """计算会话特征"""
        session_features = {
            'session_duration': 0,
            'session_action_count': 0,
            'last_action_time': 0
        }
        
        if not self.redis_client:
            return session_features
        
        try:
            # 获取会话时长
            session_key = f"user:{user_id}:session"
            session_data = self.redis_client.hgetall(session_key)
            
            if session_data:
                start_time = float(session_data.get('start_time', 0))
                session_features['session_duration'] = time.time() - start_time
                session_features['session_action_count'] = int(session_data.get('action_count', 0))
                session_features['last_action_time'] = float(session_data.get('last_action_time', 0))
        
        except Exception as e:
            logger.error(f"计算会话特征失败: {e}")
        
        return session_features
    
    def update_user_behavior(self, behavior: UserBehavior):
        """更新用户行为数据到Redis"""
        if not self.redis_client:
            return
        
        try:
            user_id = behavior.user_id
            
            # 更新今日活跃状态
            today_key = f"user:{user_id}:active:today"
            self.redis_client.set(today_key, 1, ex=86400)  # 24小时过期
            
            # 更新最近24小时的行为计数
            if behavior.behavior_type == 'order':
                order_key = f"user:{user_id}:orders:24h"
                self.redis_client.incr(order_key)
                self.redis_client.expire(order_key, 86400)
            elif behavior.behavior_type == 'view':
                view_key = f"user:{user_id}:views:24h"
                self.redis_client.incr(view_key)
                self.redis_client.expire(view_key, 86400)
            
            # 更新会话信息
            session_key = f"user:{user_id}:session"
            pipe = self.redis_client.pipeline()
            
            # 如果会话不存在，创建新会话
            if not self.redis_client.exists(session_key):
                pipe.hset(session_key, 'start_time', time.time())
                pipe.hset(session_key, 'action_count', 1)
                pipe.expire(session_key, 3600)  # 1小时过期
            else:
                pipe.hincrby(session_key, 'action_count', 1)
            
            pipe.hset(session_key, 'last_action_time', time.time())
            pipe.execute()
            
        except Exception as e:
            logger.error(f"更新用户行为失败: {e}")
    
    def get_user_realtime_features(self, user_id: str) -> Dict[str, Any]:
        """获取用户实时特征"""
        if not self.redis_client:
            return {}
        
        try:
            features_key = f"user:{user_id}:features"
            features = self.redis_client.hgetall(features_key)
            
            # 将字符串转换为正确的类型
            result = {}
            for key, value in features.items():
                try:
                    # 尝试转换为数字
                    if '.' in value:
                        result[key] = float(value)
                    else:
                        result[key] = int(value)
                except (ValueError, TypeError):
                    # 如果转换失败，保持字符串类型
                    result[key] = value
            
            return result
            
        except Exception as e:
            logger.error(f"获取用户实时特征失败: {e}")
            return {}
    
    def update_user_realtime_features(self, user_id: str, features: Dict[str, Any]):
        """更新用户实时特征到Redis"""
        if not self.redis_client:
            return
        
        try:
            features_key = f"user:{user_id}:features"
            pipe = self.redis_client.pipeline()
            
            for key, value in features.items():
                pipe.hset(features_key, key, value)
            
            # 设置过期时间为7天
            pipe.expire(features_key, 604800)
            pipe.execute()
            
        except Exception as e:
            logger.error(f"更新用户实时特征失败: {e}")
    
    def calculate_dish_popularity_score(self, dish_id: str) -> float:
        """计算菜品实时流行度分数"""
        if not self.redis_client:
            return 0.0
        
        try:
            # 获取最近1小时的订单数
            hourly_orders = int(self.redis_client.get(f"dish:{dish_id}:orders:1h") or 0)
            
            # 获取最近24小时的订单数
            daily_orders = int(self.redis_client.get(f"dish:{dish_id}:orders:24h") or 0)
            
            # 计算流行度分数（加权平均）
            popularity_score = (hourly_orders * 0.7 + daily_orders * 0.3) / max(daily_orders + 1, 10)
            
            return min(popularity_score, 1.0)
            
        except Exception as e:
            logger.error(f"计算菜品流行度分数失败: {e}")
            return 0.0
    
    def update_dish_statistics(self, dish_id: str, order_count: int = 1):
        """更新菜品统计数据"""
        if not self.redis_client:
            return
        
        try:
            # 更新最近1小时的订单数
            hourly_key = f"dish:{dish_id}:orders:1h"
            self.redis_client.incrby(hourly_key, order_count)
            self.redis_client.expire(hourly_key, 3600)
            
            # 更新最近24小时的订单数
            daily_key = f"dish:{dish_id}:orders:24h"
            self.redis_client.incrby(daily_key, order_count)
            self.redis_client.expire(daily_key, 86400)
            
        except Exception as e:
            logger.error(f"更新菜品统计数据失败: {e}")
