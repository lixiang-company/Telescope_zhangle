# -*- coding: utf-8 -*-
"""
抽象基类和接口定义
为系统各模块提供统一的基础架构
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass, field
import logging


@dataclass
class AnalysisContext:
    """分析上下文信息"""
    file_path: str = ""
    project_name: Optional[str] = None
    baseline_version: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Analyzer(ABC):
    """分析器抽象基类"""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        self._initialized = False
    
    @abstractmethod
    def initialize(self, config: Any = None) -> bool:
        """初始化分析器"""
        pass
    
    @abstractmethod
    def analyze(self, data: Any, context: Optional[AnalysisContext] = None) -> Any:
        """执行分析"""
        pass
    
    @abstractmethod
    def get_results(self) -> Dict[str, Any]:
        """获取分析结果"""
        pass
    
    def reset(self) -> None:
        """重置分析器状态"""
        self.logger.info(f"重置分析器: {self.name}")
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    def validate_input(self, data: Any) -> bool:
        """验证输入数据"""
        return data is not None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "analyzer_name": self.name,
            "initialized": self._initialized
        }


class DataProcessor(ABC):
    """数据处理器抽象基类"""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    @abstractmethod
    def process(self, data: Any, **kwargs) -> Any:
        """处理数据"""
        pass
    
    def preprocess(self, data: Any) -> Any:
        """预处理数据"""
        return data
    
    def postprocess(self, data: Any) -> Any:
        """后处理数据"""
        return data
    
    def validate_data(self, data: Any) -> bool:
        """验证数据"""
        return data is not None


class ReportGenerator(ABC):
    """报告生成器抽象基类"""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    @abstractmethod
    def generate(self, data: Any, output_path: str, **kwargs) -> str:
        """生成报告"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的格式"""
        pass
    
    def validate_output_path(self, output_path: str) -> bool:
        """验证输出路径"""
        import os
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            return True
        except:
            return False


class ConfigurableComponent(ABC):
    """可配置组件抽象基类"""
    
    def __init__(self):
        self.config = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def load_config(self, config: Dict[str, Any]) -> None:
        """加载配置"""
        pass
    
    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        pass
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """更新配置"""
        self.config.update(updates)
        self.logger.debug(f"配置已更新: {updates}")
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)


# 协议定义（用于类型检查）
class ParserProtocol(Protocol):
    """解析器协议"""
    
    def parse_file(self, file_path: str) -> Any:
        """解析文件"""
        pass
    
    def parse_directory(self, directory: str) -> List[Any]:
        """解析目录"""
        pass


class AnalyzerProtocol(Protocol):
    """分析器协议"""
    
    def analyze_data(self, data: Any) -> Any:
        """分析数据"""
        pass
    
    def get_results(self) -> Dict[str, Any]:
        """获取结果"""
        pass


# 基础实现类
class BaseAnalyzer(Analyzer, ConfigurableComponent):
    """基础分析器实现"""
    
    def __init__(self, name: str = None):
        Analyzer.__init__(self, name)
        ConfigurableComponent.__init__(self)
        self.results = {}
    
    def initialize(self, config: Any = None) -> bool:
        """初始化分析器"""
        try:
            if config:
                self.load_config(config)
            else:
                self.config = self.get_default_config()
            
            self._initialized = True
            self.logger.info(f"分析器初始化成功: {self.name}")
            return True
        except Exception as e:
            self.logger.error(f"分析器初始化失败: {e}")
            return False
    
    def get_results(self) -> Dict[str, Any]:
        """获取分析结果"""
        return self.results.copy()
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {}
    
    def load_config(self, config: Dict[str, Any]) -> None:
        """加载配置"""
        self.config = config.copy()


class BaseDataProcessor(DataProcessor, ConfigurableComponent):
    """基础数据处理器实现"""
    
    def __init__(self, name: Optional[str] = None):
        DataProcessor.__init__(self, name)
        ConfigurableComponent.__init__(self)
    
    def process(self, data: Any, **kwargs) -> Any:
        """处理数据的模板方法"""
        if not self.validate_data(data):
            raise ValueError("输入数据验证失败")
        
        # 预处理
        preprocessed_data = self.preprocess(data)
        
        # 主要处理逻辑（子类实现）
        processed_data = self._do_process(preprocessed_data, **kwargs)
        
        # 后处理
        result = self.postprocess(processed_data)
        
        return result
    
    @abstractmethod
    def _do_process(self, data: Any, **kwargs) -> Any:
        """具体的处理逻辑（子类实现）"""
        pass
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {}
    
    def load_config(self, config: Dict[str, Any]) -> None:
        """加载配置"""
        self.config = config.copy()


# 工厂类
class AnalyzerFactory:
    """分析器工厂"""
    
    _analyzers = {}
    
    @classmethod
    def register(cls, name: str, analyzer_class: type):
        """注册分析器"""
        cls._analyzers[name] = analyzer_class
    
    @classmethod
    def create(cls, name: str, **kwargs) -> Analyzer:
        """创建分析器实例"""
        if name not in cls._analyzers:
            raise ValueError(f"未知的分析器类型: {name}")
        
        analyzer_class = cls._analyzers[name]
        return analyzer_class(**kwargs)
    
    @classmethod
    def get_available_analyzers(cls) -> List[str]:
        """获取可用的分析器列表"""
        return list(cls._analyzers.keys())


# 异常类
class AnalysisError(Exception):
    """分析异常"""
    pass

class ConfigurationError(Exception):
    """配置异常"""
    pass

class DataValidationError(Exception):
    """数据验证异常"""
    pass