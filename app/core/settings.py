from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """系统配置类"""
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/meituan_recommendation"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Kafka配置
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_USER_BEHAVIOR: str = "user_behavior"
    KAFKA_TOPIC_DISH_FEATURE: str = "dish_feature"
    
    # MongoDB配置
    MONGO_URI: str = "mongodb://localhost:27017/meituan_recommendation"
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = False
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/recommendation.log"
    
    # 数据处理配置
    DATA_PROCESSING_BATCH_SIZE: int = 1000
    DATA_PROCESSING_TIMEOUT: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()