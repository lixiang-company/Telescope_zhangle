# -*- coding: utf-8 -*-
"""
通用工具模块
提供文件操作、内存管理和通用功能
"""

import os
import logging
import gc
import threading
from typing import Iterator, Optional, Any, Callable, Dict
from contextlib import contextmanager
from pathlib import Path

class FileOperationError(Exception):
    """文件操作异常"""
    pass

class MemoryManager:
    """内存管理器"""
    
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_mb = max_memory_mb
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def memory_monitor(self, operation_name: str = "Operation"):
        """内存监控上下文管理器"""
        try:
            import psutil
            process = psutil.Process()
            
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            self.logger.debug(f"{operation_name} 开始 - 内存使用: {start_memory:.2f}MB")
            
            try:
                yield
            finally:
                # 强制垃圾回收
                gc.collect()
                
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_diff = end_memory - start_memory
                
                self.logger.debug(f"{operation_name} 完成 - 内存使用: {end_memory:.2f}MB (变化: {memory_diff:+.2f}MB)")
                
                if end_memory > self.max_memory_mb:
                    self.logger.warning(f"内存使用超过限制 {self.max_memory_mb}MB: {end_memory:.2f}MB")
        
        except ImportError:
            # 没有psutil库时的备用方案
            self.logger.debug(f"{operation_name} 开始 (无内存监控)")
            try:
                yield
            finally:
                gc.collect()
                self.logger.debug(f"{operation_name} 完成 (无内存监控)")

class SafeFileHandler:
    """安全文件处理器"""
    
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def safe_open(self, file_path: str, mode: str = 'r', **kwargs):
        """安全打开文件的上下文管理器"""
        file_handle = None
        try:
            if not os.path.exists(file_path) and 'r' in mode:
                raise FileOperationError(f"文件不存在: {file_path}")
            
            # 确保父目录存在（对于写入模式）
            if 'w' in mode or 'a' in mode:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            file_handle = open(file_path, mode, encoding=self.encoding, errors='ignore', **kwargs)
            yield file_handle
            
        except Exception as e:
            self.logger.error(f"文件操作失败 {file_path}: {e}")
            raise FileOperationError(f"文件操作失败: {e}")
        finally:
            if file_handle:
                try:
                    file_handle.close()
                except Exception as e:
                    self.logger.warning(f"关闭文件失败 {file_path}: {e}")
    
    def read_file_lines(self, file_path: str, chunk_size: int = 8192) -> Iterator[str]:
        """逐行读取文件，支持大文件"""
        try:
            with self.safe_open(file_path, 'r') as f:
                while True:
                    lines = f.readlines(chunk_size)
                    if not lines:
                        break
                    for line in lines:
                        yield line.strip()
        except Exception as e:
            self.logger.error(f"逐行读取文件失败 {file_path}: {e}")
            raise
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'size_mb': stat.st_size / 1024 / 1024,
                'modified': stat.st_mtime,
                'exists': True
            }
        except Exception:
            return {'exists': False}

class CacheManager:
    """简单缓存管理器"""
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.access_order = []
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self.cache:
                # 更新访问顺序
                self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            # 如果缓存已满，删除最少使用的项
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]
            
            self.cache[key] = value
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self.cache.clear()
            self.access_order.clear()

class ValidationUtils:
    """验证工具类"""
    
    @staticmethod
    def validate_file_path(file_path: str, check_exists: bool = True) -> bool:
        """验证文件路径"""
        if not file_path or not isinstance(file_path, str):
            return False
        
        if check_exists:
            return os.path.exists(file_path) and os.path.isfile(file_path)
        
        return True
    
    @staticmethod
    def validate_directory(directory: str, check_exists: bool = True) -> bool:
        """验证目录路径"""
        if not directory or not isinstance(directory, str):
            return False
        
        if check_exists:
            return os.path.exists(directory) and os.path.isdir(directory)
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名，移除非法字符"""
        import re
        # 移除或替换非法字符
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除前后空格
        sanitized = sanitized.strip()
        # 确保不为空
        if not sanitized:
            sanitized = "unnamed_file"
        return sanitized

# 全局实例
memory_manager = MemoryManager()
file_handler = SafeFileHandler()
cache_manager = CacheManager()