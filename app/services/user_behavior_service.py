import json
import uuid
from datetime import datetime
from typing import List
from kafka import KafkaProducer
from app.core.settings import settings
from app.core.logging_config import logger
from app.core.database import redis_client, mongo_db
from app.models.user_behavior import UserBehaviorCreate, UserBehavior


class UserBehaviorService:
    """用户行为数据采集服务"""
    
    def __init__(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            self.use_kafka = True
        except Exception as e:
            logger.warning(f"Kafka连接失败，将跳过Kafka消息发送: {e}")
            self.producer = None
            self.use_kafka = False
        self.collection = mongo_db['user_behavior'] if mongo_db else None
        self.use_mongo = mongo_db is not None
    
    def collect_behavior(self, behavior: UserBehaviorCreate) -> UserBehavior:
        """采集单个用户行为"""
        try:
            # 生成唯一ID
            behavior_id = str(uuid.uuid4())
            
            # 构建行为记录
            behavior_data = behavior.model_dump()
            behavior_data['id'] = behavior_id
            behavior_data['timestamp'] = behavior.timestamp.isoformat()
            
            # 保存到MongoDB（如果可用）
            if self.use_mongo:
                self.collection.insert_one(behavior_data)
            
            # 发送到Kafka（如果可用）
            if self.use_kafka:
                self.producer.send(
                    settings.KAFKA_TOPIC_USER_BEHAVIOR,
                    value=behavior_data
                )
            
            # 更新Redis缓存（可选，用于实时统计）
            self._update_redis_cache(behavior)
            
            logger.info(f"Collected user behavior: {behavior_id}")
            return UserBehavior(**behavior_data)
            
        except Exception as e:
            logger.error(f"Failed to collect user behavior: {e}")
            raise
    
    def collect_batch_behaviors(self, behaviors: List[UserBehaviorCreate]) -> List[UserBehavior]:
        """批量采集用户行为"""
        results = []
        for behavior in behaviors:
            try:
                result = self.collect_behavior(behavior)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to collect behavior for user {behavior.user_id}: {e}")
        return results
    
    def _update_redis_cache(self, behavior: UserBehaviorCreate):
        """更新Redis缓存"""
        try:
            if redis_client:
                # 更新用户最近行为
                user_key = f"user:recent_behaviors:{behavior.user_id}"
                behavior_data = {
                    "behavior_type": behavior.behavior_type,
                    "dish_id": behavior.dish_id,
                    "timestamp": behavior.timestamp.isoformat()
                }
                
                redis_client.lpush(user_key, json.dumps(behavior_data))
                redis_client.ltrim(user_key, 0, 99)  # 保留最近100条
            
            # 更新行为计数
            if redis_client:
                behavior_key = f"behavior:count:{behavior.behavior_type}"
                redis_client.incr(behavior_key)
            
        except Exception as e:
            logger.warning(f"Failed to update Redis cache: {e}")
    
    def get_user_behaviors(self, user_id: str, limit: int = 100) -> List[UserBehavior]:
        """获取用户行为历史"""
        try:
            if not self.use_mongo:
                logger.warning("MongoDB not available, returning empty behavior list")
                return []
                
            behaviors = self.collection.find(
                {"user_id": user_id},
                limit=limit
            ).sort("timestamp", -1)
            
            return [UserBehavior(**doc) for doc in behaviors]
            
        except Exception as e:
            logger.error(f"Failed to get user behaviors: {e}")
            return []
    
    def close(self):
        """关闭资源"""
        if self.use_kafka:
            self.producer.close()


# 创建全局服务实例
user_behavior_service = UserBehaviorService()