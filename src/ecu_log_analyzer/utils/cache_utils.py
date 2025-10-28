# -*- coding: utf-8 -*-
"""
缓存管理工具
提供智能缓存和缓存清理功能
"""

import os
import pickle
import hashlib
from typing import Any, Optional
from pathlib import Path
import logging

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def _get_cache_key(self, key: str) -> str:
        """生成缓存键"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        cache_key = self._get_cache_key(key)
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            self.logger.warning(f"读取缓存失败: {e}")
        
        return None
    
    def set(self, key: str, value: Any) -> bool:
        """设置缓存数据"""
        cache_key = self._get_cache_key(key)
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
            return True
        except Exception as e:
            self.logger.error(f"设置缓存失败: {e}")
            return False
    
    def clear(self) -> None:
        """清理所有缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            self.logger.info("缓存清理完成")
        except Exception as e:
            self.logger.error(f"清理缓存失败: {e}")

# 全局缓存管理器实例
cache_manager = CacheManager()