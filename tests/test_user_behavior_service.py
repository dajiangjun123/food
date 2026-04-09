import pytest
from datetime import datetime
from app.models.user_behavior import UserBehaviorCreate
from app.services.user_behavior_service import UserBehaviorService


@pytest.fixture
def user_behavior_service():
    """创建用户行为服务实例"""
    service = UserBehaviorService()
    yield service
    service.close()


def test_collect_behavior(user_behavior_service):
    """测试采集单个用户行为"""
    behavior = UserBehaviorCreate(
        user_id="test_user_123",
        behavior_type="click",
        dish_id="dish_456",
        merchant_id="merchant_789",
        timestamp=datetime.utcnow(),
        context={"device": "mobile", "location": "beijing"}
    )
    
    result = user_behavior_service.collect_behavior(behavior)
    
    assert result.id is not None
    assert result.user_id == "test_user_123"
    assert result.behavior_type == "click"
    assert result.dish_id == "dish_456"


def test_collect_batch_behaviors(user_behavior_service):
    """测试批量采集用户行为"""
    behaviors = [
        UserBehaviorCreate(
            user_id="test_user_123",
            behavior_type="click",
            dish_id="dish_456",
            timestamp=datetime.utcnow()
        ),
        UserBehaviorCreate(
            user_id="test_user_123",
            behavior_type="view",
            dish_id="dish_789",
            timestamp=datetime.utcnow()
        )
    ]
    
    results = user_behavior_service.collect_batch_behaviors(behaviors)
    
    assert len(results) == 2
    assert results[0].behavior_type == "click"
    assert results[1].behavior_type == "view"


def test_get_user_behaviors(user_behavior_service):
    """测试获取用户行为历史"""
    # 先插入测试数据
    behavior = UserBehaviorCreate(
        user_id="test_user_456",
        behavior_type="order",
        dish_id="dish_123",
        timestamp=datetime.utcnow()
    )
    user_behavior_service.collect_behavior(behavior)
    
    # 获取用户行为
    behaviors = user_behavior_service.get_user_behaviors("test_user_456")
    
    assert len(behaviors) >= 1
    assert behaviors[0].user_id == "test_user_456"
    assert behaviors[0].behavior_type == "order"