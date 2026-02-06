# -*- coding: utf-8 -*-
"""
集成分析器
统一管理所有分析模块，提供一致的接口
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .base import BaseAnalyzer, AnalysisContext, AnalyzerFactory
from ..core.parser import LogParser, ParsedData
from .soa_analyzer import SOAAnalyzer
from .trap_analyzer import TrapAnalyzer
from ..core.performance import performance_monitor, smart_cache


@dataclass
class IntegratedAnalysisResult:
    """集成分析结果"""
    parsed_data: List[ParsedData]
    analysis_statistics: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    soa_results: Optional[Dict[str, Any]] = None
    trap_results: Optional[Dict[str, Any]] = None
    charts_data: Optional[Dict[str, Any]] = None


class IntegratedAnalyzer(BaseAnalyzer):
    """集成分析器"""
    
    def __init__(self):
        super().__init__("IntegratedAnalyzer")
        
        # 初始化子分析器
        self.log_parser = LogParser()
        self.soa_analyzer = SOAAnalyzer()
        self.trap_analyzer = TrapAnalyzer()
        
        # 分析结果
        self.analysis_result: Optional[IntegratedAnalysisResult] = None
    
    def initialize(self, config: Any = None) -> bool:
        """初始化集成分析器"""
        try:
            # 初始化所有子分析器
            self.soa_analyzer.initialize(config)
            
            # 注册到工厂
            AnalyzerFactory.register("soa", SOAAnalyzer)
            AnalyzerFactory.register("trap", TrapAnalyzer)
            
            return super().initialize(config)
        except Exception as e:
            self.logger.error(f"集成分析器初始化失败: {e}")
            return False
    
    def analyze(self, data: Any, context: Optional[AnalysisContext] = None) -> IntegratedAnalysisResult:
        """执行集成分析"""
        if isinstance(data, str):
            if os.path.isfile(data):
                return self.analyze_file(data)
            elif os.path.isdir(data):
                return self.analyze_directory(data)
            else:
                raise ValueError(f"无效的输入路径: {data}")
        else:
            raise ValueError("不支持的数据类型")
    
    @performance_monitor.measure_performance("分析单个文件")
    def analyze_file(self, file_path: str) -> IntegratedAnalysisResult:
        """分析单个文件"""
        self.logger.info(f"开始分析文件: {file_path}")
        
        # 1. 解析文件
        parsed_data = self.log_parser.parse_file(file_path)
        if not parsed_data:
            self.logger.warning(f"文件解析失败: {file_path}")
            return IntegratedAnalysisResult(
                parsed_data=[],
                analysis_statistics={},
                performance_metrics={}
            )
        
        # 2. 执行各种分析
        soa_results = self._analyze_soa([parsed_data])
        trap_results = self._analyze_trap([parsed_data])
        
        # 3. 生成统计信息
        statistics = self._generate_statistics([parsed_data])
        
        # 4. 获取性能指标
        performance_metrics = performance_monitor.get_summary()
        
        # 5. 创建结果
        self.analysis_result = IntegratedAnalysisResult(
            parsed_data=[parsed_data],
            analysis_statistics=statistics,
            performance_metrics=performance_metrics,
            soa_results=soa_results,
            trap_results=trap_results
        )
        
        self.logger.info(f"文件分析完成: {file_path}")
        return self.analysis_result
    
    @performance_monitor.measure_performance("分析目录")
    def analyze_directory(self, directory: str, use_parallel: bool = True) -> IntegratedAnalysisResult:
        """分析目录"""
        self.logger.info(f"开始分析目录: {directory}")
        
        # 1. 解析目录中的所有文件
        parsed_data_list = self.log_parser.parse_directory(directory, use_parallel)
        if not parsed_data_list:
            self.logger.warning(f"目录中未找到有效文件: {directory}")
            return IntegratedAnalysisResult(
                parsed_data=[],
                analysis_statistics={},
                performance_metrics={}
            )
        
        # 2. 执行各种分析
        soa_results = self._analyze_soa(parsed_data_list)
        trap_results = self._analyze_trap(parsed_data_list)
        
        # 3. 生成统计信息
        statistics = self._generate_statistics(parsed_data_list)
        
        # 4. 获取性能指标
        performance_metrics = performance_monitor.get_summary()
        
        # 5. 创建结果
        self.analysis_result = IntegratedAnalysisResult(
            parsed_data=parsed_data_list,
            analysis_statistics=statistics,
            performance_metrics=performance_metrics,
            soa_results=soa_results,
            trap_results=trap_results
        )
        
        self.logger.info(f"目录分析完成: {directory}, 处理了 {len(parsed_data_list)} 个文件")
        return self.analysis_result
    
    def _analyze_soa(self, parsed_data_list: List[ParsedData]) -> Optional[Dict[str, Any]]:
        """分析SOA数据"""
        try:
            # 尝试加载Topic列表
            if parsed_data_list:
                first_file_dir = os.path.dirname(parsed_data_list[0].file_path)
                fixed_summary_path = r"D:\github\lixiang\telescope\log\Summary_Report.json"
                summary_report_path = fixed_summary_path if os.path.exists(fixed_summary_path) else os.path.join(first_file_dir, "Summary_Report.json")
                
                if os.path.exists(summary_report_path):
                    self.soa_analyzer.load_topic_list(summary_report_path)
                    
                    # 解析所有文件的SOA数据
                    total_soa_data = 0
                    for data in parsed_data_list:
                        total_soa_data += self.soa_analyzer.parse_log_file(data.file_path)
                    
                    if total_soa_data > 0:
                        self.soa_analyzer.process_soa_data()
                        return {
                            "statistics": self.soa_analyzer.generate_statistics(),
                            "topic_charts": self.soa_analyzer.generate_topic_charts_data(),
                            "summary_chart": self.soa_analyzer.generate_summary_chart_data(),
                            "log_details": self.soa_analyzer.get_log_details()
                        }
            
            return None
        except Exception as e:
            self.logger.error(f"SOA分析失败: {e}")
            return None
    
    def _analyze_trap(self, parsed_data_list: List[ParsedData]) -> Optional[Dict[str, Any]]:
        """分析TRAP数据"""
        try:
            all_trap_infos = []
            for data in parsed_data_list:
                if data.trap_infos:
                    all_trap_infos.extend(data.trap_infos)
            
            if all_trap_infos:
                # 统计TRAP信息
                trap_types = set()
                trap_functions = set()
                
                for trap_info in all_trap_infos:
                    if trap_info.rest_type:
                        trap_types.add(trap_info.rest_type)
                    if trap_info.function_name:
                        trap_functions.add(trap_info.function_name)
                
                return {
                    "total_count": len(all_trap_infos),
                    "trap_types": list(trap_types),
                    "trap_functions": list(trap_functions),
                    "details": [
                        {
                            "rest_type": t.rest_type,
                            "deadd_address": t.deadd_address,
                            "function_name": t.function_name,
                            "restart_reason": t.restart_reason
                        }
                        for t in all_trap_infos
                    ]
                }
            
            return None
        except Exception as e:
            self.logger.error(f"TRAP分析失败: {e}")
            return None
    
    def _generate_statistics(self, parsed_data_list: List[ParsedData]) -> Dict[str, Any]:
        """生成统计信息"""
        valid_data = [data for data in parsed_data_list if data.core_loads]
        
        statistics = {
            "total_files": len(parsed_data_list),
            "valid_files": len(valid_data),
            "projects": list(set(data.project_name for data in valid_data if data.project_name)),
            "baseline_versions": list(set(data.baseline_version for data in valid_data if data.baseline_version))
        }
        
        if valid_data:
            # CPU负载统计
            all_loads = [data.core_loads for data in valid_data if data.core_loads]
            if all_loads:
                core_count = max(len(loads) for loads in all_loads)
                avg_loads = []
                max_loads = []
                min_loads = []
                
                for core_idx in range(core_count):
                    core_loads = [loads[core_idx] for loads in all_loads if core_idx < len(loads)]
                    if core_loads:
                        avg_loads.append(round(sum(core_loads) / len(core_loads), 2))
                        max_loads.append(max(core_loads))
                        min_loads.append(min(core_loads))
                
                statistics.update({
                    "core_count": core_count,
                    "avg_loads": avg_loads,
                    "max_loads": max_loads,
                    "min_loads": min_loads
                })
        
        return statistics
    
    def get_results(self) -> Dict[str, Any]:
        """获取分析结果"""
        if self.analysis_result:
            return {
                "analysis_statistics": self.analysis_result.analysis_statistics,
                "performance_metrics": self.analysis_result.performance_metrics,
                "soa_results": self.analysis_result.soa_results,
                "trap_results": self.analysis_result.trap_results,
                "total_files": len(self.analysis_result.parsed_data)
            }
        return {}
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return smart_cache.get_stats()
    
    def clear_cache(self) -> None:
        """清空缓存"""
        smart_cache.clear()
        self.logger.info("缓存已清空")
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "use_parallel": True,
            "max_workers": 4,
            "cache_enabled": True,
            "performance_monitoring": True
        }


# 全局集成分析器实例
integrated_analyzer = IntegratedAnalyzer()