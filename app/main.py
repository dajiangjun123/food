from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import settings
from app.core.logging_config import logger
from app.api import user_behavior, dish_feature, data_processing, data_quality, user_profile, recommendation, health, ab_test

# 创建FastAPI应用
app = FastAPI(
    title="美团外卖AI推荐系统数据服务",
    description="数据采集与预处理模块API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(user_behavior.router)
app.include_router(dish_feature.router)
app.include_router(data_processing.router)
app.include_router(data_quality.router)
app.include_router(user_profile.router)
app.include_router(recommendation.router)
app.include_router(health.router)
app.include_router(ab_test.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "美团外卖AI推荐系统数据服务",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "meituan-recommendation-data-service",
        "timestamp": "2026-04-09T10:00:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.API_HOST}:{settings.API_PORT}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG
    )