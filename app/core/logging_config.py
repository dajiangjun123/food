import os
from loguru import logger
from .settings import settings


def setup_logging():
    """配置日志系统"""
    
    # 创建日志目录
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志
    logger.remove()
    
    # 添加控制台日志
    logger.add(
        sink="sys.stderr",
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        enqueue=True,
    )
    
    # 添加文件日志
    logger.add(
        sink=settings.LOG_FILE,
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="100 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,
    )
    
    return logger


logger = setup_logging()