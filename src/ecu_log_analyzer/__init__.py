# -*- coding: utf-8 -*-
"""
ECU日志分析系统
提供ECU日志文件解析、分析和报告生成功能
"""

__version__ = "2.0.0"
__author__ = "ECU Log Analyzer Team"
__description__ = "ECU日志分析系统 - 专业的汽车电子控制单元日志分析工具"

# 延迟导入以避免循环引用
def get_log_parser():
    """Lazy import LogParser"""
    from .core.parser import LogParser
    return LogParser

def get_parsed_data():
    """Lazy import ParsedData"""
    from .core.parser import ParsedData
    return ParsedData

def get_soa_analyzer():
    """Lazy import SOAAnalyzer"""
    from .analyzers.soa_analyzer import SOAAnalyzer
    return SOAAnalyzer

def get_trap_analyzer():
    """Lazy import TrapAnalyzer"""
    from .analyzers.trap_analyzer import TrapAnalyzer
    return TrapAnalyzer

def get_report_generator():
    """Lazy import ReportGenerator"""
    from .reports.generator import ReportGenerator
    return ReportGenerator

def get_safe_file_handler():
    """Lazy import SafeFileHandler"""
    from .utils.file_utils import SafeFileHandler
    return SafeFileHandler

def get_config():
    """Lazy import Config"""
    from .config.settings import Config
    return Config

# 保持版本兼容性
def _lazy_import():
    """延迟导入所有类"""
    global LogParser, ParsedData, SOAAnalyzer, TrapAnalyzer, ReportGenerator, SafeFileHandler, Config
    
    LogParser = get_log_parser()
    ParsedData = get_parsed_data()
    SOAAnalyzer = get_soa_analyzer() 
    TrapAnalyzer = get_trap_analyzer()
    ReportGenerator = get_report_generator()
    SafeFileHandler = get_safe_file_handler()
    Config = get_config()

__all__ = [
    'get_log_parser',
    'get_parsed_data', 
    'get_soa_analyzer',
    'get_trap_analyzer',
    'get_report_generator',
    'get_safe_file_handler',
    'get_config',
    '_lazy_import'
]