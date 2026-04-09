import logging
import time
import asyncio
from typing import Dict, Any, Optional
import functools
import threading
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceService:
    """性能优化服务"""
    
    def __init__(self):
        self.metrics = {
            'request_count': 0,
            'error_count': 0,
            'total_latency': 0,
            'latency_distribution': deque(maxlen=1000),
            'concurrent_requests': 0
        }
        self.metrics_lock = threading.Lock()
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.timeout_config = {
            'recommendation': 0.1,  # 100ms
            'feature_calculation': 0.05,  # 50ms
            'database_query': 0.03  # 30ms
        }
    
    def measure_performance(self, func):
        """性能测量装饰器"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            self._increment_concurrent_requests()
            
            try:
                result = func(*args, **kwargs)
                latency = (time.time() - start_time) * 1000  # 转换为毫秒
                
                # 更新性能指标
                with self.metrics_lock:
                    self.metrics['request_count'] += 1
                    self.metrics['total_latency'] += latency
                    self.metrics['latency_distribution'].append(latency)
                
                # 记录延迟警告
                if latency > self.timeout_config.get(func.__name__, 100):
                    logger.warning(f"High latency detected in {func.__name__}: {latency:.2f}ms")
                
                return result
                
            except Exception as e:
                with self.metrics_lock:
                    self.metrics['error_count'] += 1
                logger.error(f"Error in {func.__name__}: {e}")
                raise
                
            finally:
                self._decrement_concurrent_requests()
        
        return wrapper
    
    def async_measure_performance(self, func):
        """异步性能测量装饰器"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            self._increment_concurrent_requests()
            
            try:
                result = await func(*args, **kwargs)
                latency = (time.time() - start_time) * 1000  # 转换为毫秒
                
                # 更新性能指标
                with self.metrics_lock:
                    self.metrics['request_count'] += 1
                    self.metrics['total_latency'] += latency
                    self.metrics['latency_distribution'].append(latency)
                
                # 记录延迟警告
                if latency > self.timeout_config.get(func.__name__, 100):
                    logger.warning(f"High latency detected in {func.__name__}: {latency:.2f}ms")
                
                return result
                
            except Exception as e:
                with self.metrics_lock:
                    self.metrics['error_count'] += 1
                logger.error(f"Error in {func.__name__}: {e}")
                raise
                
            finally:
                self._decrement_concurrent_requests()
        
        return wrapper
    
    def get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self.cache_lock:
            if key in self.cache:
                cached_data = self.cache[key]
                if time.time() < cached_data['expire_time']:
                    return cached_data['value']
                else:
                    # 过期数据清理
                    del self.cache[key]
        return None
    
    def set_cache(self, key: str, value: Any, ttl: int = 300):
        """设置缓存"""
        with self.cache_lock:
            self.cache[key] = {
                'value': value,
                'expire_time': time.time() + ttl,
                'created_at': datetime.now()
            }
    
    def clear_cache(self, key: Optional[str] = None):
        """清理缓存"""
        with self.cache_lock:
            if key:
                if key in self.cache:
                    del self.cache[key]
            else:
                self.cache.clear()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self.metrics_lock:
            metrics = self.metrics.copy()
            
            # 计算额外指标
            if metrics['request_count'] > 0:
                metrics['avg_latency'] = metrics['total_latency'] / metrics['request_count']
            else:
                metrics['avg_latency'] = 0
            
            # 计算延迟分布
            if metrics['latency_distribution']:
                latencies = list(metrics['latency_distribution'])
                metrics['p95_latency'] = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
                metrics['p99_latency'] = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
            else:
                metrics['p95_latency'] = 0
                metrics['p99_latency'] = 0
            
            # 计算错误率
            metrics['error_rate'] = metrics['error_count'] / max(metrics['request_count'], 1)
            
            return metrics
    
    def _increment_concurrent_requests(self):
        """增加并发请求计数"""
        with self.metrics_lock:
            self.metrics['concurrent_requests'] += 1
    
    def _decrement_concurrent_requests(self):
        """减少并发请求计数"""
        with self.metrics_lock:
            self.metrics['concurrent_requests'] = max(0, self.metrics['concurrent_requests'] - 1)
    
    def check_system_health(self) -> Dict[str, Any]:
        """检查系统健康状态"""
        metrics = self.get_performance_metrics()
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }
        
        # 健康检查规则
        if metrics['error_rate'] > 0.01:
            health_status['status'] = 'degraded'
            health_status['warning'] = 'High error rate detected'
        
        if metrics['avg_latency'] > 100:
            health_status['status'] = 'degraded'
            health_status['warning'] = 'High average latency detected'
        
        if metrics['concurrent_requests'] > 100:
            health_status['status'] = 'warning'
            health_status['warning'] = 'High concurrent requests'
        
        return health_status
    
    def optimize_recommendation(self, recommendation_func):
        """推荐优化装饰器"""
        @functools.wraps(recommendation_func)
        def wrapper(*args, **kwargs):
            # 获取缓存键
            user_id = kwargs.get('user_id') or (args[1] if len(args) > 1 else None)
            if user_id:
                cache_key = f"recommendation:{user_id}:{kwargs.get('algorithm', 'hybrid')}"
                cached_result = self.get_cache(cache_key)
                if cached_result:
                    return cached_result
            
            # 执行推荐
            result = recommendation_func(*args, **kwargs)
            
            # 缓存结果
            if user_id:
                self.set_cache(cache_key, result, ttl=60)  # 缓存1分钟
            
            return result
        
        return wrapper
    
    def batch_process(self, items, process_func, batch_size=100):
        """批量处理优化"""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = [process_func(item) for item in batch]
            results.extend(batch_results)
        return results
    
    async def async_batch_process(self, items, process_func, batch_size=100):
        """异步批量处理优化"""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_tasks = [process_func(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        return results
    
    def limit_concurrency(self, max_concurrent=50):
        """并发限制装饰器"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                async with semaphore:
                    return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def timeout(self, seconds):
        """超时控制装饰器"""
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
                except asyncio.TimeoutError:
                    logger.warning(f"Function {func.__name__} timed out after {seconds} seconds")
                    raise
            return wrapper
        return decorator
