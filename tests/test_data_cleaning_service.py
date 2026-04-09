import pytest
import pandas as pd
from datetime import datetime, timedelta
from app.services.data_cleaning_service import DataCleaningService


@pytest.fixture
def data_cleaning_service():
    """创建数据清洗服务实例"""
    return DataCleaningService()


def test_clean_user_behavior_data(data_cleaning_service):
    """测试清洗用户行为数据"""
    # 测试数据包含各种问题：缺失值、异常值、重复数据等
    test_data = [
        {
            "user_id": "user_1",
            "behavior_type": "click",
            "dish_id": "dish_1",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "user_id": "",  # 空用户ID
            "behavior_type": "view",
            "dish_id": "dish_2",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "user_id": "user_2",
            "behavior_type": "invalid_type",  # 无效行为类型
            "dish_id": "dish_3",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "user_id": "user_1",  # 重复数据
            "behavior_type": "click",
            "dish_id": "dish_1",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "user_id": "user_3",
            "behavior_type": "order",
            "dish_id": "dish_4",
            "timestamp": (datetime.utcnow() - timedelta(days=400)).isoformat()  # 过期数据
        }
    ]
    
    cleaned_data = data_cleaning_service.clean_user_behavior_data(test_data)
    
    # 应该只剩下有效的数据
    assert len(cleaned_data) == 1
    assert cleaned_data[0]["user_id"] == "user_1"
    assert cleaned_data[0]["behavior_type"] == "click"


def test_clean_dish_feature_data(data_cleaning_service):
    """测试清洗菜品特征数据"""
    test_data = [
        {
            "dish_id": "dish_1",
            "merchant_id": "merchant_1",
            "name": "宫保鸡丁",
            "price": 28.5,
            "category": "川菜",
            "sales_volume": 100,
            "rating": 4.5
        },
        {
            "dish_id": "",  # 空菜品ID
            "merchant_id": "merchant_2",
            "name": "麻婆豆腐",
            "price": 22.0,
            "category": "川菜"
        },
        {
            "dish_id": "dish_2",
            "merchant_id": "",  # 空商家ID
            "name": "水煮鱼",
            "price": 68.0,
            "category": "川菜"
        },
        {
            "dish_id": "dish_3",
            "merchant_id": "merchant_3",
            "name": "糖醋里脊",
            "price": -10.0,  # 负价格
            "category": "鲁菜"
        },
        {
            "dish_id": "dish_4",
            "merchant_id": "merchant_4",
            "name": "红烧肉",
            "price": 9999.0,  # 异常价格
            "category": "家常菜"
        },
        {
            "dish_id": "dish_5",
            "merchant_id": "merchant_5",
            "name": "鱼香肉丝",
            "price": 32.0,
            "category": "川菜",
            "rating": 6.0  # 无效评分
        }
    ]
    
    cleaned_data = data_cleaning_service.clean_dish_feature_data(test_data)
    
    # 应该只剩下有效的数据
    assert len(cleaned_data) == 1
    assert cleaned_data[0]["dish_id"] == "dish_1"
    assert cleaned_data[0]["price"] == 28.5
    assert cleaned_data[0]["rating"] == 4.5


def test_normalize_features(data_cleaning_service):
    """测试特征标准化"""
    test_data = [
        {"price": 10.0, "sales_volume": 100},
        {"price": 20.0, "sales_volume": 200},
        {"price": 30.0, "sales_volume": 300}
    ]
    
    df = pd.DataFrame(test_data)
    normalized_df = data_cleaning_service.normalize_features(df, ["price", "sales_volume"])
    
    # 验证标准化结果
    assert normalized_df["price"].mean() < 0.1  # 均值接近0
    assert normalized_df["sales_volume"].mean() < 0.1  # 均值接近0


def test_encode_categorical_features(data_cleaning_service):
    """测试分类特征编码"""
    test_data = [
        {"category": "川菜"},
        {"category": "粤菜"},
        {"category": "川菜"},
        {"category": "鲁菜"}
    ]
    
    df = pd.DataFrame(test_data)
    encoded_df = data_cleaning_service.encode_categorical_features(df, ["category"])
    
    # 验证编码结果
    assert "category" in encoded_df.columns
    assert encoded_df["category"].nunique() == 3  # 应该有3个不同的编码值