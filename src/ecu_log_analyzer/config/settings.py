# -*- coding: utf-8 -*-
"""
配置管理模块
支持从文件和环境变量加载配置
在未安装 PyYAML 时优雅回退到默认配置
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml  # 可选依赖
except Exception:
    yaml = None

@dataclass
class LogPatterns:
    """日志模式配置"""
    project_pattern: str = r'RMR:([^;:,\s]+)'
    baseline_pattern: str = r'SWVerNum\s*:\s*([0-9a-fA-Fx]+)'
    core_load_pattern: str = r'\[CPU_LOAD\]:core\s+load:\s*([\d.,\s]+)'
    cpu_load_pattern: str = r'core\s+load:\s*([\d.,\s]+)'
    # 兼容旧实现所需的附加模式
    filename_project_pattern: str = r'([A-Z]+[A-Z0-9_]*)-[0-9]+'
    soc_version_pattern: str = r'soc\s+version:\s*([^\n\r]+)'
    mcu_version_pattern: str = r'mcu\s+version:\s*([^\n\r]+)'
    # TRAP相关
    trap_rst_pattern: str = r'\{TRAP-RST\}:Reset Info:'
    trap_reset_type_pattern: str = r'\{TRAP-RST\}:Reset Type:\s*(\d+)'
    trap_deadd_pattern: str = r'\{TRAP-RST\}:DEADD:\s*([0-9a-fA-F]+)'
    trap_func_pattern: str = r'\{TRAP-RST\}:Func(\d+):\s*0x([0-9a-fA-F]+)'

@dataclass
class SystemConfig:
    """系统配置"""
    log_extensions: List[str] = field(default_factory=lambda: ['.log', '.txt', '.out'])
    output_dir: str = 'output'
    verbose: bool = True
    max_file_size_mb: int = 100
    file_encoding: str = 'utf-8'
    max_memory_mb: int = 500
    
    # TRAP分析配置
    trap_analysis_enabled: bool = True
    trap_symbol_cache_size: int = 10000
    trap_range_search_limit: int = 0x1000  # 4KB
    trap_parse_timeout: int = 30  # 秒
    
    # 性能优化配置
    parallel_processing_threshold_mb: float = 1.0  # 大于此大小的文件使用并行处理
    max_parallel_workers: int = 4  # 最大并行工作线程数
    cache_cleanup_threshold: int = 8000  # 缓存清理阈值
    enable_performance_monitoring: bool = True  # 启用性能监控
    
    # Map文件搜索配置
    map_file_search_depth: int = 3  # 递归搜索深度
    map_file_search_timeout: int = 10  # 搜索超时时间（秒）
    enable_smart_map_search: bool = True  # 启用智能搜索

class Config:
    """主配置类"""
    
    def __init__(self):
        self.log_patterns = LogPatterns()
        self.system = SystemConfig()
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # 系统配置
        if 'ECU_MAX_FILE_SIZE_MB' in os.environ:
            self.system.max_file_size_mb = int(os.environ['ECU_MAX_FILE_SIZE_MB'])
        
        if 'ECU_FILE_ENCODING' in os.environ:
            self.system.file_encoding = os.environ['ECU_FILE_ENCODING']
        
        if 'ECU_OUTPUT_DIR' in os.environ:
            self.system.output_dir = os.environ['ECU_OUTPUT_DIR']
        
        if 'ECU_MAX_MEMORY_MB' in os.environ:
            self.system.max_memory_mb = int(os.environ['ECU_MAX_MEMORY_MB'])
        
        if 'ECU_VERBOSE' in os.environ:
            self.system.verbose = os.environ['ECU_VERBOSE'].lower() in ['true', '1', 'yes']
    
    @classmethod
    def from_file(cls, file_path: str) -> 'Config':
        """从文件加载配置"""
        if not os.path.exists(file_path):
            return cls()
        # 未安装yaml库时，直接返回默认配置
        if yaml is None:
            return cls()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f) or {}
            
            config = cls()
            
            # 更新系统配置
            if 'system' in config_dict:
                system_config = config_dict['system']
                if 'max_file_size_mb' in system_config:
                    config.system.max_file_size_mb = system_config['max_file_size_mb']
                if 'file_encoding' in system_config:
                    config.system.file_encoding = system_config['file_encoding']
                if 'output_dir' in system_config:
                    config.system.output_dir = system_config['output_dir']
                if 'verbose' in system_config:
                    config.system.verbose = system_config['verbose']
                if 'max_memory_mb' in system_config:
                    config.system.max_memory_mb = system_config['max_memory_mb']
                if 'log_extensions' in system_config:
                    config.system.log_extensions = system_config['log_extensions']
            
            # 更新日志模式配置
            if 'log_patterns' in config_dict:
                patterns = config_dict['log_patterns']
                if 'project_pattern' in patterns:
                    config.log_patterns.project_pattern = patterns['project_pattern']
                if 'baseline_pattern' in patterns:
                    config.log_patterns.baseline_pattern = patterns['baseline_pattern']
                if 'core_load_pattern' in patterns:
                    config.log_patterns.core_load_pattern = patterns['core_load_pattern']
                if 'cpu_load_pattern' in patterns:
                    config.log_patterns.cpu_load_pattern = patterns['cpu_load_pattern']
            
            return config
            
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return cls()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            'system': {
                'max_file_size_mb': self.system.max_file_size_mb,
                'file_encoding': self.system.file_encoding,
                'output_dir': self.system.output_dir,
                'verbose': self.system.verbose,
                'max_memory_mb': self.system.max_memory_mb,
                'log_extensions': self.system.log_extensions,
            },
            'log_patterns': {
                'project_pattern': self.log_patterns.project_pattern,
                'baseline_pattern': self.log_patterns.baseline_pattern,
                'core_load_pattern': self.log_patterns.core_load_pattern,
                'cpu_load_pattern': self.log_patterns.cpu_load_pattern,
            }
        }

    # ===== 兼容旧实现的工具方法 =====
    def validate_directory(self, directory: str) -> bool:
        return os.path.exists(directory) and os.path.isdir(directory)

    def create_output_directory(self) -> str:
        out_dir = self.system.output_dir
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def create_timestamp_directory(self, timestamp: str) -> str:
        base_output_dir = self.create_output_directory()
        timestamp_dir = os.path.join(base_output_dir, timestamp)
        if not os.path.exists(timestamp_dir):
            os.makedirs(timestamp_dir, exist_ok=True)
        # 创建 static 子目录
        static_dir = self.get_static_directory(timestamp_dir)
        if not os.path.exists(static_dir):
            os.makedirs(static_dir, exist_ok=True)
        return timestamp_dir

    def get_static_directory(self, timestamp_dir: str) -> str:
        return os.path.join(timestamp_dir, 'static')

    def copy_static_files(self, timestamp_dir: str) -> None:
        """复制静态文件到输出 static 目录（echarts.min.js 及可能的主样式）"""
        import shutil
        # 工程根目录: src/ecu_log_analyzer/config/settings.py 向上四级
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        source_static_dir = os.path.join(project_root, 'resources', 'static')
        target_static_dir = self.get_static_directory(timestamp_dir)
        
        if not os.path.exists(target_static_dir):
            os.makedirs(target_static_dir, exist_ok=True)
        
        # 复制 echarts.min.js
        echarts_source = os.path.join(source_static_dir, 'echarts.min.js')
        echarts_target = os.path.join(target_static_dir, 'echarts.min.js')
        
        if os.path.exists(echarts_source):
            try:
                shutil.copy2(echarts_source, echarts_target)
                print(f"✅ 成功复制echarts.min.js到输出目录")
            except Exception as e:
                print(f"❌ 复制echarts.min.js失败: {e}")
        else:
            print(f"⚠️  警告: echarts.min.js未在{source_static_dir}中找到")
