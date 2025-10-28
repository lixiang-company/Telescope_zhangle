# -*- coding: utf-8 -*-
"""
性能优化模块
提供并行处理、异步操作和性能监控功能
"""

import concurrent.futures
import multiprocessing
import time
import logging
from typing import List, Callable, Any, Dict, Optional
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    """性能指标"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    memory_peak: Optional[float] = None
    items_processed: int = 0
    
    @property
    def throughput(self) -> float:
        """吞吐量 (items/second)"""
        if self.duration > 0:
            return self.items_processed / self.duration
        return 0.0

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics: List[PerformanceMetrics] = []
    
    @contextmanager
    def measure_performance(self, operation_name: str, items_count: int = 0):
        """性能测量上下文管理器"""
        start_time = time.time()
        memory_before = self._get_memory_usage()
        
        try:
            yield
        finally:
            end_time = time.time()
            memory_after = self._get_memory_usage()
            duration = end_time - start_time
            
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                memory_before=memory_before,
                memory_after=memory_after,
                items_processed=items_count
            )
            
            self.metrics.append(metrics)
            self._log_performance(metrics)
    
    def _get_memory_usage(self) -> Optional[float]:
        """获取当前内存使用量(MB)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return None
    
    def _log_performance(self, metrics: PerformanceMetrics):
        """记录性能日志"""
        self.logger.info(
            f"性能监控 - {metrics.operation_name}: "
            f"耗时 {metrics.duration:.2f}s, "
            f"处理 {metrics.items_processed} 项, "
            f"吞吐量 {metrics.throughput:.2f} items/s"
        )
        
        if metrics.memory_before and metrics.memory_after:
            memory_diff = metrics.memory_after - metrics.memory_before
            self.logger.debug(
                f"内存使用: {metrics.memory_before:.2f}MB -> "
                f"{metrics.memory_after:.2f}MB (变化: {memory_diff:+.2f}MB)"
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.metrics:
            return {}
        
        total_duration = sum(m.duration for m in self.metrics)
        total_items = sum(m.items_processed for m in self.metrics)
        avg_throughput = total_items / total_duration if total_duration > 0 else 0
        
        return {
            "total_operations": len(self.metrics),
            "total_duration": total_duration,
            "total_items_processed": total_items,
            "average_throughput": avg_throughput,
            "operations": [
                {
                    "name": m.operation_name,
                    "duration": m.duration,
                    "items": m.items_processed,
                    "throughput": m.throughput
                }
                for m in self.metrics
            ]
        }

class ParallelProcessor:
    """并行处理器"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 8)
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()
    
    def process_files_parallel(self, 
                             file_paths: List[str], 
                             process_func: Callable[[str], Any],
                             chunk_size: int = 1) -> List[Any]:
        """并行处理文件列表"""
        if not file_paths:
            return []
        
        start_time = time.time()
        results = []
        
        self.logger.info(f"开始并行处理 {len(file_paths)} 个文件，使用 {self.max_workers} 个线程")
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_file = {
                    executor.submit(process_func, file_path): file_path 
                    for file_path in file_paths
                }
                
                # 收集结果
                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"处理文件失败 {file_path}: {e}")
                        # 可以选择添加一个错误结果或跳过
                        results.append(None)
        
        except Exception as e:
            self.logger.error(f"并行处理失败: {e}")
            # 回退到串行处理
            self.logger.info("回退到串行处理...")
            return self._process_files_serial(file_paths, process_func)
        
        duration = time.time() - start_time
        self.logger.info(f"并行处理完成: {len(results)} 个结果，耗时 {duration:.2f}s")
        
        return results
    
    def _process_files_serial(self, 
                            file_paths: List[str], 
                            process_func: Callable[[str], Any]) -> List[Any]:
        """串行处理文件（回退方案）"""
        results = []
        for file_path in file_paths:
            try:
                result = process_func(file_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"串行处理文件失败 {file_path}: {e}")
                results.append(None)
        return results
    
    def process_data_chunks(self, 
                          data_list: List[Any], 
                          process_func: Callable[[List[Any]], Any],
                          chunk_size: int = 100) -> List[Any]:
        """并行处理数据块"""
        if not data_list:
            return []
        
        # 将数据分块
        chunks = [data_list[i:i + chunk_size] for i in range(0, len(data_list), chunk_size)]
        
        self.logger.info(f"将 {len(data_list)} 个数据项分为 {len(chunks)} 个块进行并行处理")
        
        return self.process_files_parallel(chunks, process_func)

class SmartCache:
    """智能缓存系统"""
    
    def __init__(self, max_memory_mb: int = 100, ttl_seconds: int = 3600):
        self.max_memory_mb = max_memory_mb
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    def get_cache_key(self, file_path: str) -> str:
        """生成缓存键"""
        import hashlib
        import os
        
        # 使用文件路径和修改时间生成键
        try:
            mtime = os.path.getmtime(file_path)
            key_string = f"{file_path}_{mtime}"
            return hashlib.md5(key_string.encode()).hexdigest()
        except:
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def get(self, file_path: str) -> Optional[Any]:
        """从缓存获取数据"""
        cache_key = self.get_cache_key(file_path)
        
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            
            # 检查TTL
            current_time = time.time()
            if current_time - cache_entry['timestamp'] < self.ttl_seconds:
                self.logger.debug(f"缓存命中: {file_path}")
                return cache_entry['data']
            else:
                # 缓存过期
                del self.cache[cache_key]
                self.logger.debug(f"缓存过期: {file_path}")
        
        return None
    
    def set(self, file_path: str, data: Any) -> None:
        """设置缓存数据"""
        cache_key = self.get_cache_key(file_path)
        
        # 检查内存使用
        self._cleanup_if_needed()
        
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time(),
            'file_path': file_path
        }
        
        self.logger.debug(f"缓存设置: {file_path}")
    
    def _cleanup_if_needed(self) -> None:
        """必要时清理缓存"""
        # 简单的清理策略：如果缓存项太多，删除最老的
        if len(self.cache) > 1000:  # 最大缓存项数
            # 找到最老的缓存项
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
            self.logger.debug("缓存清理: 删除最老的缓存项")
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.logger.info("缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "cache_size": len(self.cache),
            "max_memory_mb": self.max_memory_mb,
            "ttl_seconds": self.ttl_seconds
        }

# 全局实例
performance_monitor = PerformanceMonitor()
parallel_processor = ParallelProcessor()
smart_cache = SmartCache()