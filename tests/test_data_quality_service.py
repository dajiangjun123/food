import pytest
from datetime import datetime
from app.services.data_quality_service import DataQualityService


@pytest.fixture
def data_quality_service():
    """创建数据质量服务实例"""
    return DataQualityService()


def test_calculate_data_quality_metrics_user_behavior(data_quality_service):
    """测试计算用户行为数据质量指标"""
    test_data = [
        {
            "user_id": "user_1",
            "behavior_type": "click",
            "dish_id": "dish_1",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "user_id": "user_2",
            "behavior_type": "order",
            "dish_id": "dish_2",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "user_id": "",  # 缺失用户ID
            "behavior_type": "view",
            "dish_id": "dish_3",
            "timestamp": datetime.utcnow().isoformat()
        }
    ]
    
    metrics = data_quality_service.calculate_data_quality_metrics(test_data, "user_behavior")
    
    assert metrics["data_type"] == "user_behavior"
    assert metrics["record_count"] == 3
    assert abs(metrics["completeness"] - 0.6667)< 0.0001  # 2/3 的记录有完整的必填字段
    assert metrics["accuracy"] == 1.0  # 所有行为类型都是有效的
    assert metrics["error_count"] == 1  # 有1条记录有错误（缺失user_id）


def test_calculate_data_quality_metrics_dish_feature(data_quality_service):
    """测试计算菜品特征数据质量指标"""
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
            "dish_id": "dish_2",
            "merchant_id": "merchant_2",
            "name": "麻婆豆腐",
            "price": -10.0,  # 负价格
            "category": "川菜"
        },
        {
            "dish_id": "dish_3",
            "merchant_id": "merchant_3",
            "name": "水煮鱼",
            "price": 68.0,
            "category": "",  # 空分类
            "rating": 6.0  # 无效评分
        }
    ]
    
    metrics = data_quality_service.calculate_data_quality_metrics(test_data, "dish_feature")
    
    assert metrics["data_type"] == "dish_feature"
    assert metrics["record_count"] == 3
    assert metrics["accuracy"]< 1.0  # 有数据准确性问题
    assert metrics["consistency"] <1.0  # 有数据一致性问题
    assert metrics["error_count"] >= 2  # 至少有2条记录有错误


def test_assess_quality_level():
    """测试质量等级评估"""
    # 优秀质量
    excellent_metrics = {
        "completeness": 0.98,
        "accuracy": 0.99,
        "consistency": 0.97,
        "timeliness": 0.96
    }
    excellent_level = DataQualityService._assess_quality_level(excellent_metrics)
    assert excellent_level == "excellent"
    
    # 良好质量
    good_metrics = {
        "completeness": 0.92,
        "accuracy": 0.93,
        "consistency": 0.91,
        "timeliness": 0.90
    }
    good_level = DataQualityService._assess_quality_level(good_metrics)
    assert good_level == "good"
    
    # 一般质量
    fair_metrics = {
        "completeness": 0.85,
        "accuracy": 0.84,
        "consistency": 0.83,
        "timeliness": 0.82
    }
    fair_level = DataQualityService._assess_quality_level(fair_metrics)
    assert fair_level == "fair"
    
    # 较差质量
    poor_metrics = {
        "completeness": 0.75,
        "accuracy": 0.74,
        "consistency": 0.73,
        "timeliness": 0.72
    }
    poor_level = DataQualityService._assess_quality_level(poor_metrics)
    assert poor_level == "poor"
    
    # 严重质量问题
    critical_metrics = {
        "completeness": 0.65,
        "accuracy": 0.64,
        "consistency": 0.63,
        "timeliness": 0.62
    }
    critical_level = DataQualityService._assess_quality_level(critical_metrics)
    assert critical_level == "critical"


def test_calculate_field_statistics():
    """测试字段统计信息计算"""
    test_data = [
        {"price": 10.0, "category": "川菜"},
        {"price": 20.0, "category": "粤菜"},
        {"price": 30.0, "category": "川菜"}
    ]
    
    import pandas as pd
    df = pd.DataFrame(test_data)
    
    statistics = DataQualityService._calculate_field_statistics(df)
    
    assert "price" in statistics
    assert "category" in statistics
    assert statistics["price"]["mean"] == 20.0
    assert statistics["price"]["min"] == 10.0
    assert statistics["price"]["max"] == 30.0
    assert statistics["category"]["unique_count"] == 2