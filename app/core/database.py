import redis
from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .settings import settings
from .logging_config import logger


# Redis连接
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    logger.info("Redis connection successful")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None


# MongoDB连接
try:
    mongo_client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    mongo_db = mongo_client.get_database()
    logger.info("MongoDB connection successful")
except Exception as e:
    logger.warning(f"MongoDB connection failed: {e}")
    mongo_client = None
    mongo_db = None


# SQLAlchemy配置
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connections():
    """测试数据库连接"""
    try:
        # 测试Redis连接
        redis_client.ping()
        logger.info("Redis connection successful")
        
        # 测试MongoDB连接
        mongo_client.admin.command('ping')
        logger.info("MongoDB connection successful")
        
        # 测试PostgreSQL连接
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("PostgreSQL connection successful")
        
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False