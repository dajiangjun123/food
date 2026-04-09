import pytest
from app.models.dish_feature import DishFeatureCreate
from app.services.dish_feature_service import DishFeatureService


@pytest.fixture
def dish_feature_service():
    """创建菜品特征服务实例"""
    service = DishFeatureService()
    yield service
    service.close()


def test_create_dish_feature(dish_feature_service):
    """测试创建菜品特征"""
    feature = DishFeatureCreate(
        dish_id="test_dish_123",
        merchant_id="test_merchant_456",
        name="宫保鸡丁",
        price=28.5,
        category="川菜",
        tags=["麻辣", "经典"],
        description="正宗川菜，麻辣鲜香",
        image_url="http://example.com/dish123.jpg",
        sales_volume=100,
        rating=4.5,
        review_count=50
    )
    
    result = dish_feature_service.create_dish_feature(feature)
    
    assert result.id is not None
    assert result.dish_id == "test_dish_123"
    assert result.name == "宫保鸡丁"
    assert result.price == 28.5
    assert result.category == "川菜"
    assert "麻辣" in result.tags
    assert result.text_features is not None
    assert result.image_features is not None


def test_create_batch_features(dish_feature_service):
    """测试批量创建菜品特征"""
    features = [
        DishFeatureCreate(
            dish_id="test_dish_123",
            merchant_id="test_merchant_456",
            name="宫保鸡丁",
            price=28.5,
            category="川菜"
        ),
        DishFeatureCreate(
            dish_id="test_dish_456",
            merchant_id="test_merchant_456",
            name="麻婆豆腐",
            price=22.0,
            category="川菜"
        )
    ]
    
    results = dish_feature_service.create_batch_features(features)
    
    assert len(results) == 2
    assert results[0].name == "宫保鸡丁"
    assert results[1].name == "麻婆豆腐"


def test_get_dish_feature(dish_feature_service):
    """测试获取菜品特征"""
    # 先创建测试数据
    feature = DishFeatureCreate(
        dish_id="test_dish_789",
        merchant_id="test_merchant_123",
        name="水煮鱼",
        price=68.0,
        category="川菜"
    )
    dish_feature_service.create_dish_feature(feature)
    
    # 获取菜品特征
    result = dish_feature_service.get_dish_feature("test_dish_789")
    
    assert result.dish_id == "test_dish_789"
    assert result.name == "水煮鱼"
    assert result.price == 68.0


def test_extract_text_features(dish_feature_service):
    """测试文本特征提取"""
    feature = DishFeatureCreate(
        dish_id="test_dish_999",
        merchant_id="test_merchant_999",
        name="糖醋里脊",
        price=38.0,
        category="鲁菜",
        tags=["酸甜", "经典"],
        description="传统鲁菜，酸甜可口"
    )
    
    text_features = dish_feature_service.extract_text_features(feature)
    
    assert isinstance(text_features, dict)
    # 验证关键词是否被提取
    has_keywords = any(keyword in text_features for keyword in ["糖醋", "里脊", "鲁菜", "酸甜", "经典"])
    assert has_keywords