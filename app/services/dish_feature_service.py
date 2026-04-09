import json
import uuid
from datetime import datetime
from typing import List, Dict
from kafka import KafkaProducer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from app.core.settings import settings
from app.core.logging_config import logger
from app.core.database import redis_client, mongo_db
from app.models.dish_feature import DishFeatureCreate, DishFeature


class DishFeatureService:
    """菜品特征提取服务"""
    
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
        self.collection = mongo_db['dish_feature'] if mongo_db else None
        self.use_mongo = mongo_db is not None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000)
    
    def extract_text_features(self, dish: DishFeatureCreate) -> Dict[str, float]:
        """提取文本特征"""
        try:
            # 组合文本信息
            text = f"{dish.name} {dish.description or ''} {' '.join(dish.tags)}"
            
            # 使用TF-IDF提取特征
            features = self.tfidf_vectorizer.fit_transform([text])
            
            # 获取特征名称和权重
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            feature_weights = features.toarray()[0]
            
            # 构建特征字典
            text_features = {}
            for name, weight in zip(feature_names, feature_weights):
                if weight > 0:
                    text_features[name] = float(weight)
            
            return text_features
            
        except Exception as e:
            logger.error(f"Failed to extract text features: {e}")
            return {}
    
    def extract_image_features(self, image_url: str) -> List[float]:
        """提取图像特征（模拟实现）"""
        try:
            # 这里应该调用真实的图像特征提取模型
            # 为了演示，返回随机特征向量
            if image_url:
                return [float(np.random.random()) for _ in range(256)]
            return []
            
        except Exception as e:
            logger.error(f"Failed to extract image features: {e}")
            return []
    
    def create_dish_feature(self, feature: DishFeatureCreate) -> DishFeature:
        """创建菜品特征"""
        try:
            # 生成唯一ID
            feature_id = str(uuid.uuid4())
            
            # 提取特征
            text_features = self.extract_text_features(feature)
            image_features = self.extract_image_features(feature.image_url)
            
            # 构建特征记录
            feature_data = feature.model_dump()
            feature_data['id'] = feature_id
            feature_data['created_at'] = datetime.utcnow().isoformat()
            feature_data['updated_at'] = datetime.utcnow().isoformat()
            feature_data['text_features'] = text_features
            feature_data['image_features'] = image_features
            
            # 保存到MongoDB（如果可用）
            if self.use_mongo:
                self.collection.insert_one(feature_data)
            
            # 发送到Kafka（如果可用）
            if self.use_kafka:
                self.producer.send(
                    settings.KAFKA_TOPIC_DISH_FEATURE,
                    value=feature_data
                )
            
            # 更新Redis缓存
            self._update_redis_cache(feature_data)
            
            logger.info(f"Created dish feature: {feature_id}")
            return DishFeature(**feature_data)
            
        except Exception as e:
            logger.error(f"Failed to create dish feature: {e}")
            raise
    
    def create_batch_features(self, features: List[DishFeatureCreate]) -> List[DishFeature]:
        """批量创建菜品特征"""
        results = []
        for feature in features:
            try:
                result = self.create_dish_feature(feature)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to create feature for dish {feature.dish_id}: {e}")
        return results
    
    def update_dish_feature(self, dish_id: str, feature: DishFeatureCreate) -> DishFeature:
        """更新菜品特征"""
        try:
            # 提取新特征
            text_features = self.extract_text_features(feature)
            image_features = self.extract_image_features(feature.image_url)
            
            # 更新数据
            update_data = feature.model_dump()
            update_data['updated_at'] = datetime.utcnow().isoformat()
            update_data['text_features'] = text_features
            update_data['image_features'] = image_features
            
            # 更新MongoDB
            result = self.collection.update_one(
                {"dish_id": dish_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise ValueError(f"Dish feature not found: {dish_id}")
            
            # 获取更新后的数据
            updated_feature = self.collection.find_one({"dish_id": dish_id})
            
            # 更新Redis缓存
            self._update_redis_cache(updated_feature)
            
            logger.info(f"Updated dish feature: {dish_id}")
            return DishFeature(**updated_feature)
            
        except Exception as e:
            logger.error(f"Failed to update dish feature: {e}")
            raise
    
    def get_dish_feature(self, dish_id: str) -> DishFeature:
        """获取菜品特征"""
        try:
            if not self.use_mongo:
                logger.warning("MongoDB not available, cannot get dish feature")
                raise ValueError(f"MongoDB not available: {dish_id}")
                
            feature = self.collection.find_one({"dish_id": dish_id})
            if not feature:
                raise ValueError(f"Dish feature not found: {dish_id}")
            return DishFeature(**feature)
            
        except Exception as e:
            logger.error(f"Failed to get dish feature: {e}")
            raise
    
    def _update_redis_cache(self, feature_data):
        """更新Redis缓存"""
        try:
            if redis_client:
                # 缓存菜品基本信息
                dish_key = f"dish:feature:{feature_data['dish_id']}"
                redis_client.hset(dish_key, mapping={
                    "name": feature_data['name'],
                    "price": str(feature_data['price']),
                    "category": feature_data['category'],
                    "sales_volume": str(feature_data['sales_volume']),
                    "rating": str(feature_data['rating'] or 0)
                })
                
                # 缓存分类索引
                category_key = f"dish:category:{feature_data['category']}"
                redis_client.sadd(category_key, feature_data['dish_id'])
            
        except Exception as e:
            logger.warning(f"Failed to update Redis cache: {e}")
    
    def close(self):
        """关闭资源"""
        if self.use_kafka:
            self.producer.close()


# 创建全局服务实例
dish_feature_service = DishFeatureService()