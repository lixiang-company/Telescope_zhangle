# -*- coding: utf-8 -*-
"""
分析器基类
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Type
from dataclasses import dataclass

@dataclass
class AnalysisContext:
    """分析上下文"""
    file_path: str = ""
    line_number: int = 0
    extra_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}

class BaseAnalyzer(ABC):
    """分析器基类"""
    
    def __init__(self, analyzer_name: str):
        self.analyzer_name = analyzer_name
        self.logger = logging.getLogger(f"{__name__}.{analyzer_name}")
        self.config = None
        
    def initialize(self, config: Any = None) -> bool:
        """初始化分析器"""
        self.config = config
        return True
        
    @abstractmethod
    def analyze(self, data: Any, context: Optional[AnalysisContext] = None) -> Any:
        """分析数据"""
        pass
        
    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        pass

class AnalyzerFactory:
    """分析器工厂"""
    
    _analyzers: Dict[str, Type[BaseAnalyzer]] = {}
    
    @classmethod
    def register(cls, name: str, analyzer_class: Type[BaseAnalyzer]):
        """注册分析器"""
        cls._analyzers[name] = analyzer_class
    
    @classmethod
    def create(cls, name: str, *args, **kwargs) -> BaseAnalyzer:
        """创建分析器实例"""
        if name not in cls._analyzers:
            raise ValueError(f"未知的分析器类型: {name}")
        return cls._analyzers[name](*args, **kwargs)
    
    @classmethod
    def get_available_analyzers(cls) -> list:
        """获取可用的分析器列表"""
        return list(cls._analyzers.keys())