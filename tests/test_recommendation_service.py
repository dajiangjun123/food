import pytest
from app.services.recommendation_service import RecommendationService
from app.models.recommendation import RecommendationRequest, AlgorithmMetrics


@pytest.fixture
def recommendation_service():
    """创建推荐服务实例"""
    return RecommendationService()


def test_recommend_hybrid(recommendation_service):
    """测试混合推荐算法"""
    request = RecommendationRequest(
        user_id="test_user",
        request_id="test_request",
        filters={"algorithm": "hybrid"},
        limit=5
    )
    
    response = recommendation_service.recommend(request)
    
    assert response.request_id == "test_request"
    assert response.user_id == "test_user"
    assert response.algorithm == "hybrid"
    assert len(response.items) == 5
    assert response.latency >= 0


def test_recommend_collaborative_filtering(recommendation_service):
    """测试协同过滤推荐算法"""
    request = RecommendationRequest(
        user_id="test_user",
        request_id="test_request",
        filters={"algorithm": "collaborative_filtering"},
        limit=3
    )
    
    response = recommendation_service.recommend(request)
    
    assert response.request_id == "test_request"
    assert response.user_id == "test_user"
    assert response.algorithm == "collaborative_filtering"
    assert len(response.items) == 3


def test_recommend_content_based(recommendation_service):
    """测试基于内容的推荐算法"""
    request = RecommendationRequest(
        user_id="test_user",
        request_id="test_request",
        filters={"algorithm": "content_based"},
        limit=4
    )
    
    response = recommendation_service.recommend(request)
    
    assert response.request_id == "test_request"
    assert response.user_id == "test_user"
    assert response.algorithm == "content_based"
    assert len(response.items) == 4


def test_apply_filters(recommendation_service):
    """测试过滤功能"""
    # 获取混合推荐结果
    request = RecommendationRequest(
        user_id="test_user",
        request_id="test_request",
        filters={"algorithm": "hybrid"},
        limit=10
    )
    
    response = recommendation_service.recommend(request)
    items_before_filter = response.items
    
    # 添加商家过滤
    filtered_request = RecommendationRequest(
        user_id="test_user",
        request_id="test_request_filtered",
        filters={
            "algorithm": "hybrid",
            "merchant_ids": ["merchant_101", "merchant_102"]
        },
        limit=10
    )
    
    filtered_response = recommendation_service.recommend(filtered_request)
    items_after_filter = filtered_response.items
    
    # 验证过滤后结果数量减少或保持不变
    assert len(items_after_filter) <= len(items_before_filter)


def test_train_model(recommendation_service):
    """测试模型训练功能"""
    training_data = {"user_behaviors": [], "dish_features": []}
    
    result = recommendation_service.train_model("collaborative_filtering", training_data)
    
    assert result.model_name == "collaborative_filtering"
    assert result.version is not None
    assert "precision" in result.metrics
    assert "recall" in result.metrics
    assert result.training_time >= 0


def test_evaluate_algorithm(recommendation_service):
    """测试算法评估功能"""
    test_data = {"test_samples": []}
    
    metrics = recommendation_service.evaluate_algorithm("hybrid", test_data)
    
    assert isinstance(metrics, AlgorithmMetrics)
    assert 0 <= metrics.precision <= 1
    assert 0 <= metrics.recall <= 1
    assert 0 <= metrics.f1_score <= 1
    assert 0 <= metrics.ndcg <= 1
    assert 0 <= metrics.coverage <= 1
    assert 0 <= metrics.diversity <= 1


def test_update_model_parameters(recommendation_service):
    """测试更新模型参数"""
    parameters = {"collaborative_weight": 0.7, "content_weight": 0.3}
    
    success = recommendation_service.update_model_parameters("hybrid", parameters)
    
    assert success is True
    
    # 验证参数已更新
    model_info = recommendation_service.get_model_info("hybrid")
    assert model_info["parameters"]["collaborative_weight"] == 0.7
    assert model_info["parameters"]["content_weight"] == 0.3


def test_get_model_info(recommendation_service):
    """测试获取模型信息"""
    # 获取单个模型信息
    model_info = recommendation_service.get_model_info("hybrid")
    
    assert model_info["name"] == "hybrid"
    assert model_info["type"] == "ensemble"
    
    # 获取所有模型信息
    all_models = recommendation_service.get_model_info()
    
    assert "collaborative_filtering" in all_models
    assert "content_based" in all_models
    assert "hybrid" in all_models


def test_recommend_with_context(recommendation_service):
    """测试带上下文的推荐"""
    request = RecommendationRequest(
        user_id="test_user",
        request_id="test_request",
        context={"time": "dinner", "location": "beijing"},
        limit=5
    )
    
    response = recommendation_service.recommend(request)
    
    assert response.request_id == "test_request"
    assert response.user_id == "test_user"
    assert len(response.items) == 5


def test_recommend_with_invalid_algorithm(recommendation_service):
    """测试无效算法参数（应该回退到混合推荐）"""
    request = RecommendationRequest(
        user_id="test_user",
        request_id="test_request",
        filters={"algorithm": "invalid_algorithm"},
        limit=5
    )
    
    response = recommendation_service.recommend(request)
    
    # 应该回退到混合推荐
    assert response.algorithm == "hybrid"
    assert len(response.items) == 5
