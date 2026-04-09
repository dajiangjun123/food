import pytest
from datetime import datetime
from app.services.ab_test_service import ABTestService
from app.models.ab_test import ExperimentStatus, TrafficAllocation


class TestABTestService:
    """A/B测试服务测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.ab_test_service = ABTestService()
    
    def test_create_experiment(self):
        """测试创建实验"""
        experiment_data = {
            "name": "测试实验",
            "description": "这是一个测试实验",
            "traffic_allocations": [
                {
                    "group_id": "group1",
                    "group_name": "对照组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy1"
                },
                {
                    "group_id": "group2",
                    "group_name": "实验组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy2"
                }
            ],
            "metrics": ["ctr", "cvr", "gmv"]
        }
        
        experiment = self.ab_test_service.create_experiment(experiment_data, created_by="test_user")
        
        assert experiment is not None
        assert experiment.name == "测试实验"
        assert experiment.status == ExperimentStatus.DRAFT
        assert len(experiment.traffic_allocations) == 2
        assert experiment.metrics == ["ctr", "cvr", "gmv"]
    
    def test_get_experiment(self):
        """测试获取实验"""
        # 先创建实验
        experiment_data = {
            "name": "测试实验",
            "traffic_allocations": [
                {
                    "group_id": "group1",
                    "group_name": "对照组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy1"
                },
                {
                    "group_id": "group2",
                    "group_name": "实验组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy2"
                }
            ]
        }
        
        experiment = self.ab_test_service.create_experiment(experiment_data, created_by="test_user")
        
        # 获取实验
        retrieved_experiment = self.ab_test_service.get_experiment(experiment.experiment_id)
        
        assert retrieved_experiment is not None
        assert retrieved_experiment.experiment_id == experiment.experiment_id
        assert retrieved_experiment.name == "测试实验"
    
    def test_update_experiment(self):
        """测试更新实验"""
        # 创建实验
        experiment_data = {
            "name": "测试实验",
            "traffic_allocations": [
                {
                    "group_id": "group1",
                    "group_name": "对照组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy1"
                },
                {
                    "group_id": "group2",
                    "group_name": "实验组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy2"
                }
            ]
        }
        
        experiment = self.ab_test_service.create_experiment(experiment_data, created_by="test_user")
        
        # 更新实验
        update_data = {
            "name": "更新后的实验",
            "status": ExperimentStatus.RUNNING
        }
        
        updated_experiment = self.ab_test_service.update_experiment(experiment.experiment_id, update_data)
        
        assert updated_experiment is not None
        assert updated_experiment.name == "更新后的实验"
        assert updated_experiment.status == ExperimentStatus.RUNNING
    
    def test_list_experiments(self):
        """测试列出实验"""
        # 创建多个实验
        for i in range(3):
            experiment_data = {
                "name": f"测试实验{i+1}",
                "traffic_allocations": [
                    {
                        "group_id": f"group1_{i}",
                        "group_name": "对照组",
                        "traffic_percentage": 50,
                        "strategy_id": "strategy1"
                    },
                    {
                        "group_id": f"group2_{i}",
                        "group_name": "实验组",
                        "traffic_percentage": 50,
                        "strategy_id": "strategy2"
                    }
                ]
            }
            self.ab_test_service.create_experiment(experiment_data, created_by="test_user")
        
        # 获取实验列表
        result = self.ab_test_service.list_experiments(page=1, page_size=10)
        
        assert "experiments" in result
        assert "total" in result
        assert result["total"] >= 3
    
    def test_user_assignment(self):
        """测试用户分组分配"""
        # 创建并启动实验
        experiment_data = {
            "name": "测试实验",
            "traffic_allocations": [
                {
                    "group_id": "group1",
                    "group_name": "对照组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy1"
                },
                {
                    "group_id": "group2",
                    "group_name": "实验组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy2"
                }
            ]
        }
        
        experiment = self.ab_test_service.create_experiment(experiment_data, created_by="test_user")
        self.ab_test_service.start_experiment(experiment.experiment_id)
        
        # 用户分组分配
        user_id = "test_user_123"
        assignment = self.ab_test_service.assign_user(user_id, experiment.experiment_id)
        
        assert assignment is not None
        assert assignment.user_id == user_id
        assert assignment.experiment_id == experiment.experiment_id
        assert assignment.group_id in ["group1", "group2"]
        
        # 再次分配应该返回相同的分组
        assignment2 = self.ab_test_service.assign_user(user_id, experiment.experiment_id)
        assert assignment2.group_id == assignment.group_id
    
    def test_start_experiment(self):
        """测试启动实验"""
        experiment_data = {
            "name": "测试实验",
            "traffic_allocations": [
                {
                    "group_id": "group1",
                    "group_name": "对照组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy1"
                },
                {
                    "group_id": "group2",
                    "group_name": "实验组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy2"
                }
            ]
        }
        
        experiment = self.ab_test_service.create_experiment(experiment_data, created_by="test_user")
        
        # 启动实验
        success = self.ab_test_service.start_experiment(experiment.experiment_id)
        
        assert success is True
        
        # 验证状态已更新
        updated_experiment = self.ab_test_service.get_experiment(experiment.experiment_id)
        assert updated_experiment.status == ExperimentStatus.RUNNING
    
    def test_pause_experiment(self):
        """测试暂停实验"""
        experiment_data = {
            "name": "测试实验",
            "traffic_allocations": [
                {
                    "group_id": "group1",
                    "group_name": "对照组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy1"
                },
                {
                    "group_id": "group2",
                    "group_name": "实验组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy2"
                }
            ]
        }
        
        experiment = self.ab_test_service.create_experiment(experiment_data, created_by="test_user")
        self.ab_test_service.start_experiment(experiment.experiment_id)
        
        # 暂停实验
        success = self.ab_test_service.pause_experiment(experiment.experiment_id)
        
        assert success is True
        
        # 验证状态已更新
        updated_experiment = self.ab_test_service.get_experiment(experiment.experiment_id)
        assert updated_experiment.status == ExperimentStatus.PAUSED
    
    def test_complete_experiment(self):
        """测试完成实验"""
        experiment_data = {
            "name": "测试实验",
            "traffic_allocations": [
                {
                    "group_id": "group1",
                    "group_name": "对照组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy1"
                },
                {
                    "group_id": "group2",
                    "group_name": "实验组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy2"
                }
            ]
        }
        
        experiment = self.ab_test_service.create_experiment(experiment_data, created_by="test_user")
        self.ab_test_service.start_experiment(experiment.experiment_id)
        
        # 完成实验
        success = self.ab_test_service.complete_experiment(experiment.experiment_id)
        
        assert success is True
        
        # 验证状态已更新
        updated_experiment = self.ab_test_service.get_experiment(experiment.experiment_id)
        assert updated_experiment.status == ExperimentStatus.COMPLETED
    
    def test_analyze_experiment(self):
        """测试分析实验结果"""
        experiment_data = {
            "name": "测试实验",
            "traffic_allocations": [
                {
                    "group_id": "group1",
                    "group_name": "对照组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy1"
                },
                {
                    "group_id": "group2",
                    "group_name": "实验组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy2"
                }
            ]
        }
        
        experiment = self.ab_test_service.create_experiment(experiment_data, created_by="test_user")
        
        # 分析实验
        analysis = self.ab_test_service.analyze_experiment(experiment.experiment_id)
        
        assert analysis is not None
        assert analysis.experiment_id == experiment.experiment_id
        assert len(analysis.results) == 2
    
    def test_get_experiment_stats(self):
        """测试获取实验统计信息"""
        experiment_data = {
            "name": "测试实验",
            "traffic_allocations": [
                {
                    "group_id": "group1",
                    "group_name": "对照组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy1"
                },
                {
                    "group_id": "group2",
                    "group_name": "实验组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy2"
                }
            ]
        }
        
        experiment = self.ab_test_service.create_experiment(experiment_data, created_by="test_user")
        
        # 获取统计信息
        stats = self.ab_test_service.get_experiment_stats(experiment.experiment_id)
        
        assert stats is not None
        assert stats["experiment_id"] == experiment.experiment_id
        assert "group_stats" in stats
        assert "total_users" in stats
    
    def test_inactive_experiment_assignment(self):
        """测试非运行状态实验的用户分配"""
        experiment_data = {
            "name": "测试实验",
            "traffic_allocations": [
                {
                    "group_id": "group1",
                    "group_name": "对照组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy1"
                },
                {
                    "group_id": "group2",
                    "group_name": "实验组",
                    "traffic_percentage": 50,
                    "strategy_id": "strategy2"
                }
            ]
        }
        
        experiment = self.ab_test_service.create_experiment(experiment_data, created_by="test_user")
        
        # 实验处于草稿状态，不应分配
        assignment = self.ab_test_service.assign_user("test_user", experiment.experiment_id)
        
        assert assignment is None
