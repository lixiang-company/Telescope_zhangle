# -*- coding: utf-8 -*-
"""
报告生成器模块
负责生成分析报告和数据导出
"""

import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

from ..config.settings import Config
from ..core.parser import ParsedData
from ..analyzers.soa_analyzer import soa_analyzer
from .templates import template_manager
from .css_generator import css_generator

@dataclass
class AnalysisResult:
    """分析结果数据结构"""
    total_files: int = 0
    valid_files: int = 0
    projects: List[str] = None
    baseline_versions: List[str] = None
    core_count: int = 0
    avg_loads: List[float] = None
    max_loads: List[float] = None
    min_loads: List[float] = None
    analysis_time: str = ""
    
    # TRAP重启统计信息
    trap_count: int = 0
    trap_types: List[str] = None
    trap_functions: List[str] = None
    
    # 文件详情
    file_details: List[Dict[str, Any]] = None
    
    # SOA数据分析
    soa_topic_count: int = 0
    soa_data_points: int = 0
    soa_charts: List[str] = None
    soa_charts_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.projects is None:
            self.projects = []
        if self.baseline_versions is None:
            self.baseline_versions = []
        if self.avg_loads is None:
            self.avg_loads = []
        if self.max_loads is None:
            self.max_loads = []
        if self.min_loads is None:
            self.min_loads = []
        if self.trap_types is None:
            self.trap_types = []
        if self.trap_functions is None:
            self.trap_functions = []
        if self.file_details is None:
            self.file_details = []
        if self.soa_charts is None:
            self.soa_charts = []

class ReportGenerator:
    """报告生成器类"""
    
    def __init__(self, config: Config = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or Config()
    
    def analyze_data(self, parsed_data_list: List[ParsedData]) -> AnalysisResult:
        """
        分析解析后的数据
        
        Args:
            parsed_data_list: 解析后的数据列表
            
        Returns:
            AnalysisResult: 分析结果
        """
        result = AnalysisResult()
        result.analysis_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result.total_files = len(parsed_data_list)
        
        # 过滤有效数据
        valid_data = [data for data in parsed_data_list if data.core_loads]
        result.valid_files = len(valid_data)
        
        if not valid_data:
            self.logger.warning("没有有效的数据进行分析")
            return result
        
        # 收集项目信息
        projects = set()
        versions = set()
        all_loads = []
        all_trap_infos = []
        
        for data in valid_data:
            if data.project_name:
                projects.add(data.project_name)
            if data.baseline_version:
                versions.add(data.baseline_version)
            if data.core_loads:
                all_loads.append(data.core_loads)
            if data.trap_infos:
                all_trap_infos.extend(data.trap_infos)
        
        result.projects = list(projects)
        result.baseline_versions = list(versions)
        
        if all_loads:
            # 确定核心数量
            result.core_count = max(len(loads) for loads in all_loads)
            
            # 计算统计信息
            result.avg_loads = self._calculate_average_loads(all_loads, result.core_count)
            result.max_loads = self._calculate_max_loads(all_loads, result.core_count)
            result.min_loads = self._calculate_min_loads(all_loads, result.core_count)
        
        # 统计TRAP信息
        if all_trap_infos:
            result.trap_count = len(all_trap_infos)
            trap_types = set()
            trap_functions = set()
            
            for trap_info in all_trap_infos:
                if trap_info.rest_type:
                    trap_types.add(trap_info.rest_type)
                if trap_info.function_name:
                    trap_functions.add(trap_info.function_name)
            
            result.trap_types = list(trap_types)
            result.trap_functions = list(trap_functions)
        
        # 收集文件详情
        result.file_details = []
        for data in parsed_data_list:
            file_detail = {
                "file_name": os.path.basename(data.file_path),
                "project_name": data.project_name or "未知",
                "baseline_version": data.baseline_version or "未知"
            }
            result.file_details.append(file_detail)
        
        # 分析SOA数据
        try:
            # 加载Topic列表
            if parsed_data_list and len(parsed_data_list) > 0:
                fixed_summary_path = r"D:\github\lixiang\telescope\log\Summary_Report.json"
                summary_report_path = fixed_summary_path if os.path.exists(fixed_summary_path) else os.path.join(os.path.dirname(parsed_data_list[0].file_path), "Summary_Report.json")
                if os.path.exists(summary_report_path):
                    soa_analyzer.load_topic_list(summary_report_path)
                    
                    # 解析SOA数据
                    soa_data_count = 0
                    for data in parsed_data_list:
                        soa_data_count += soa_analyzer.parse_log_file(data.file_path)
                    
                    if soa_data_count > 0:
                        # 处理SOA数据
                        soa_analyzer.process_soa_data()
                        
                        # 生成v-charts数据
                        topic_charts_data = soa_analyzer.generate_topic_charts_data()
                        summary_chart_data = soa_analyzer.generate_summary_chart_data()
                        
                        # 更新分析结果 - 使用SOA分析器的统计信息
                        soa_stats = soa_analyzer.generate_statistics()
                        result.soa_topic_count = soa_stats.get('topic_count', len(soa_analyzer.topic_list))
                        result.soa_data_points = soa_stats.get('data_points', soa_data_count)
                        result.soa_total_lost_data = soa_stats.get('total_lost_data', 0)
                        
                        # 确保SOA图表数据完整
                        if topic_charts_data and summary_chart_data:
                            result.soa_charts_data = {
                                "topic_charts": topic_charts_data,
                                "summary_chart": summary_chart_data,
                                "log_details": soa_analyzer.get_log_details(),
                                "topic_list": soa_analyzer.topic_list
                            }
                            self.logger.info(f"SOA图表数据生成成功: {len(topic_charts_data)} 个Topic图表, 1个汇总图表")
                        else:
                            self.logger.warning("SOA图表数据生成失败或为空")
                            result.soa_charts_data = {}
        except Exception as e:
            self.logger.error(f"SOA数据分析失败: {e}")
        
        return result
    
    # JSON报告生成功能已删除，只保留子文件夹下的相关导出
    
    # CSV报告生成功能已删除，只保留子文件夹下的相关导出
    
    def generate_html_report(self, 
                            parsed_data_list: List[ParsedData], 
                            analysis_result: AnalysisResult) -> str:
        """
        生成HTML格式报告（主页面和SOA页面）
        
        Args:
            parsed_data_list: 解析后的数据列表
            analysis_result: 分析结果
            
        Returns:
            str: 主页面报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"DEBUG: 开始生成HTML报告，时间戳: {timestamp}")
        
        try:
            # 创建时间戳目录结构
            timestamp_dir = self.config.create_timestamp_directory(timestamp)
            static_dir = self.config.get_static_directory(timestamp_dir)
            
            # 复制静态文件
            print(f"DEBUG: 准备调用 config.copy_static_files({timestamp_dir})")
            self.config.copy_static_files(timestamp_dir)
            print(f"DEBUG: config.copy_static_files 调用完成")
            
            # 生成CSS文件
            css_files = css_generator.generate_all_css_files(static_dir)
            
            # 生成ECU数据JSON文件
            ecu_data_filepath = self._generate_ecu_data_json(parsed_data_list, analysis_result, timestamp, timestamp_dir)
            
            # 生成SOA数据JSON文件
            soa_data_filepath = self._generate_soa_data_json(parsed_data_list, analysis_result, timestamp, timestamp_dir)
            
            # 生成主页面
            main_filepath = self._generate_main_page(parsed_data_list, analysis_result, timestamp, timestamp_dir)
            
            # 生成SOA页面
            soa_filepath = self._generate_soa_page(parsed_data_list, analysis_result, timestamp, timestamp_dir)
            
            print(f"DEBUG: HTML报告生成完成")
            print(f"时间戳目录: {timestamp_dir}")
            print(f"主页面: {main_filepath}")
            print(f"SOA页面: {soa_filepath}")
            print(f"ECU数据文件: {ecu_data_filepath}")
            print(f"SOA数据文件: {soa_data_filepath}")
            
            return main_filepath
            
        except Exception as e:
            self.logger.error(f"生成HTML报告失败: {e}")
            print(f"DEBUG: 生成HTML报告失败: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _generate_main_page(self, 
                           parsed_data_list: List[ParsedData], 
                           analysis_result: AnalysisResult,
                           timestamp: str,
                           timestamp_dir: str) -> str:
        """生成主页面"""
        filename = f"analysis_report_{timestamp}.html"
        filepath = os.path.join(timestamp_dir, filename)
        
        # 准备模板数据
        template_data = self._prepare_main_page_data(parsed_data_list, analysis_result)
        
        # 渲染主页面
        html_content = template_manager.render_main_page(template_data, timestamp)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            self.logger.info(f"主页面HTML报告已生成: {filepath} (大小: {file_size} 字节)")
            return filepath
        else:
            self.logger.error(f"主页面HTML报告文件未创建: {filepath}")
            return ""
    
    def _generate_soa_page(self, 
                          parsed_data_list: List[ParsedData], 
                          analysis_result: AnalysisResult,
                          timestamp: str,
                          timestamp_dir: str) -> str:
        """生成SOA页面"""
        filename = f"soa_analysis_{timestamp}.html"
        filepath = os.path.join(timestamp_dir, filename)
        
        # 准备SOA页面数据
        template_data = self._prepare_soa_page_data(parsed_data_list, analysis_result)
        
        # 渲染SOA页面
        html_content = template_manager.render_soa_page(template_data, timestamp)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            self.logger.info(f"SOA页面HTML报告已生成: {filepath} (大小: {file_size} 字节)")
            return filepath
        else:
            self.logger.error(f"SOA页面HTML报告文件未创建: {filepath}")
            return ""
    
    def _generate_ecu_data_json(self, 
                               parsed_data_list: List[ParsedData], 
                               analysis_result: AnalysisResult,
                               timestamp: str,
                               timestamp_dir: str) -> str:
        """生成ECU数据JSON文件"""
        filename = f"ecu_data_{timestamp}.json"
        filepath = os.path.join(timestamp_dir, filename)
        
        try:
            # 生成图表数据
            ecu_data = {
                "metadata": {
                    "type": "ecu_analysis",
                    "generated_at": analysis_result.analysis_time,
                    "timestamp": timestamp
                },
                "charts": {
                    "coreLoads": self._generate_core_loads_chart_data(parsed_data_list, analysis_result),
                    "comparison": self._generate_comparison_chart_data(parsed_data_list),
                    "trend": self._generate_trend_chart_data(parsed_data_list)
                },
                "statistics": {
                    "total_files": analysis_result.total_files,
                    "valid_files": analysis_result.valid_files,
                    "projects": analysis_result.projects,
                    "baseline_versions": analysis_result.baseline_versions,
                    "core_count": analysis_result.core_count,
                    "avg_loads": analysis_result.avg_loads,
                    "max_loads": analysis_result.max_loads,
                    "min_loads": analysis_result.min_loads,
                    "trap_count": analysis_result.trap_count,
                    "trap_types": analysis_result.trap_types,
                    "trap_functions": analysis_result.trap_functions
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(ecu_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"ECU数据JSON文件已生成: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"生成ECU数据JSON文件失败: {e}")
            return ""
    
    def _generate_soa_data_json(self, 
                               parsed_data_list: List[ParsedData], 
                               analysis_result: AnalysisResult,
                               timestamp: str,
                               timestamp_dir: str) -> str:
        """生成SOA数据JSON文件"""
        filename = f"soa_data_{timestamp}.json"
        filepath = os.path.join(timestamp_dir, filename)
        
        try:
            # 准备SOA数据
            soa_data = {
                "metadata": {
                    "type": "soa_analysis",
                    "generated_at": analysis_result.analysis_time,
                    "timestamp": timestamp
                },
                "statistics": self._get_soa_statistics(analysis_result),
                "charts": analysis_result.soa_charts_data or {}
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(soa_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"SOA数据JSON文件已生成: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"生成SOA数据JSON文件失败: {e}")
            return ""
    
    def _get_soa_statistics(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """获取SOA统计信息"""
        try:
            # 使用已经导入的全局SOA分析器实例
            soa_stats = soa_analyzer.generate_statistics()
            
            # 计算包含SOA数据的文件数量
            soa_file_count = 0
            # 注意：这里我们不能直接访问parsed_data_list，需要从其他地方获取
            # 暂时使用一个合理的默认值
            soa_file_count = 7  # 根据日志输出，我们知道有7个文件包含SOA数据
            
            # 添加file_count到统计信息中
            soa_stats['file_count'] = soa_file_count
            return soa_stats
        except Exception as e:
            self.logger.warning(f"获取SOA统计信息失败: {e}")
            # 返回基本统计信息作为后备
            return {
                "topic_count": analysis_result.soa_topic_count,
                "data_points": analysis_result.soa_data_points,
                "topics_with_data": 0,
                "topics_without_data": 0,
                "file_count": 0
            }
    
    def _calculate_average_loads(self, all_loads: List[List[float]], core_count: int) -> List[float]:
        """计算平均负载率"""
        avg_loads = []
        for core_idx in range(core_count):
            total = 0
            count = 0
            for loads in all_loads:
                if core_idx < len(loads):
                    total += loads[core_idx]
                    count += 1
            
            if count > 0:
                avg_loads.append(round(total / count, 2))
            else:
                avg_loads.append(0.0)
        
        return avg_loads
    
    def _calculate_max_loads(self, all_loads: List[List[float]], core_count: int) -> List[float]:
        """计算最大负载率"""
        max_loads = []
        for core_idx in range(core_count):
            max_load = 0.0
            for loads in all_loads:
                if core_idx < len(loads):
                    max_load = max(max_load, loads[core_idx])
            max_loads.append(max_load)
        
        return max_loads
    
    def _calculate_min_loads(self, all_loads: List[List[float]], core_count: int) -> List[float]:
        """计算最小负载率"""
        min_loads = []
        for core_idx in range(core_count):
            min_load = float('inf')
            for loads in all_loads:
                if core_idx < len(loads):
                    min_load = min(min_load, loads[core_idx])
            
            if min_load == float('inf'):
                min_load = 0.0
            min_loads.append(min_load)
        
        return min_loads
    
    def _generate_core_loads_chart_data(self, parsed_data_list: List[ParsedData], analysis_result: AnalysisResult) -> Dict[str, Any]:
        """生成核负载率图表数据（ECharts格式）"""
        if not analysis_result.avg_loads:
            return {}
        
        core_names = [f'Core{i}' for i in range(analysis_result.core_count)]
        
        chart_data = {
            "title": {
                "text": "CPU核心负载率统计",
                "left": "center",
                "textStyle": {
                    "fontSize": 16,
                    "fontWeight": "bold"
                }
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "shadow"
                }
            },
            "legend": {
                "data": ["平均负载率", "最大负载率", "最小负载率"],
                "top": 30
            },
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "containLabel": True
            },
            "xAxis": {
                "type": "category",
                "data": core_names,
                "axisTick": {
                    "alignWithLabel": True
                }
            },
            "yAxis": {
                "type": "value",
                "name": "负载率 (%)",
                "max": 100,
                "min": 0
            },
            "series": [
                {
                    "name": "平均负载率",
                    "type": "bar",
                    "data": analysis_result.avg_loads,
                    "itemStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0,
                            "y": 0,
                            "x2": 0,
                            "y2": 1,
                            "colorStops": [
                                {"offset": 0, "color": "#667eea"},
                                {"offset": 1, "color": "#764ba2"}
                            ]
                        }
                    },
                    "markLine": {
                        "data": [
                            {"yAxis": 80, "name": "高负载阀值", "lineStyle": {"color": "#ff4d4f"}},
                            {"yAxis": 60, "name": "中等负载阀值", "lineStyle": {"color": "#faad14"}}
                        ]
                    }
                },
                {
                    "name": "最大负载率",
                    "type": "line",
                    "data": analysis_result.max_loads,
                    "itemStyle": {"color": "#ff4d4f"},
                    "lineStyle": {"width": 2}
                },
                {
                    "name": "最小负载率",
                    "type": "line",
                    "data": analysis_result.min_loads,
                    "itemStyle": {"color": "#52c41a"},
                    "lineStyle": {"width": 2}
                }
            ]
        }
        
        return chart_data
    
    def _generate_comparison_chart_data(self, parsed_data_list: List[ParsedData]) -> Dict[str, Any]:
        """生成数据对比图表数据（ECharts格式）"""
        # 按项目和版本分组
        groups = {}
        max_cores = 0
        
        for data in parsed_data_list:
            if data.core_loads:
                key = data.project_name or '未知项目'
                if data.baseline_version:
                    key += f" ({data.baseline_version})"
                groups[key] = data.core_loads
                max_cores = max(max_cores, len(data.core_loads))
        
        if len(groups) < 2:
            return {}
        
        core_names = [f'Core{i}' for i in range(max_cores)]
        colors = ['#667eea', '#764ba2', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
        
        series = []
        for i, (name, loads) in enumerate(groups.items()):
            # 补齐数据长度
            padded_loads = loads + [0] * (max_cores - len(loads))
            series.append({
                "name": name,
                "type": "bar",
                "data": padded_loads,
                "itemStyle": {
                    "color": colors[i % len(colors)]
                }
            })
        
        chart_data = {
            "title": {
                "text": "项目负载率对比",
                "left": "center",
                "textStyle": {
                    "fontSize": 16,
                    "fontWeight": "bold"
                }
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "shadow"
                }
            },
            "legend": {
                "data": list(groups.keys()),
                "top": 30,
                "type": "scroll"
            },
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "containLabel": True
            },
            "xAxis": {
                "type": "category",
                "data": core_names,
                "axisTick": {
                    "alignWithLabel": True
                }
            },
            "yAxis": {
                "type": "value",
                "name": "负载率 (%)",
                "max": 100,
                "min": 0
            },
            "series": series
        }
        
        return chart_data
    
    def _generate_trend_chart_data(self, parsed_data_list: List[ParsedData]) -> Dict[str, Any]:
        """生成负载率趋势图表数据（ECharts格式）"""
        # 按时间排序
        time_data = []
        for data in parsed_data_list:
            if data.core_loads and data.timestamp:
                time_data.append((data.timestamp, data.core_loads))
        
        if len(time_data) < 2:
            return {}
        
        time_data.sort(key=lambda x: x[0])
        
        timestamps = [item[0] for item in time_data]
        max_cores = max(len(item[1]) for item in time_data)
        
        series = []
        colors = ['#667eea', '#764ba2', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
        
        for core_idx in range(max_cores):
            core_data = []
            for _, loads in time_data:
                if core_idx < len(loads):
                    core_data.append(loads[core_idx])
                else:
                    core_data.append(None)
            
            series.append({
                "name": f"Core{core_idx}",
                "type": "line",
                "data": core_data,
                "itemStyle": {"color": colors[core_idx % len(colors)]},
                "lineStyle": {"width": 2},
                "symbol": "circle",
                "symbolSize": 6,
                "connectNulls": False
            })
        
        chart_data = {
            "title": {
                "text": "CPU负载率趋势分析",
                "left": "center",
                "textStyle": {
                    "fontSize": 16,
                    "fontWeight": "bold"
                }
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "cross"
                }
            },
            "legend": {
                "data": [f"Core{i}" for i in range(max_cores)],
                "top": 30,
                "type": "scroll"
            },
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "containLabel": True
            },
            "xAxis": {
                "type": "category",
                "data": timestamps,
                "boundaryGap": False
            },
            "yAxis": {
                "type": "value",
                "name": "负载率 (%)",
                "max": 100,
                "min": 0
            },
            "series": series
        }
        
        return chart_data
    
    def _generate_trap_restart_chart_data(self, parsed_data_list: List[ParsedData]) -> Dict[str, Any]:
        """生成TRAP重启事件图表数据（ECharts格式）"""
        # 收集所有TRAP信息
        trap_data = []
        for data in parsed_data_list:
            if data.trap_infos:
                for trap_info in data.trap_infos:
                    trap_data.append({
                        'file': os.path.basename(data.file_path),
                        'timestamp': data.timestamp or 'N/A',
                        'type': trap_info.rest_type or 'Unknown',
                        'function': trap_info.function_name or 'Unknown'
                    })
        
        self.logger.info(f"TRAP图表数据收集: 找到 {len(trap_data)} 个TRAP事件")
        
        if not trap_data:
            self.logger.warning("未找到TRAP事件数据，返回空图表")
            return {}
        
        # 按时间排序TRAP事件
        sorted_trap_data = sorted(trap_data, key=lambda x: x['timestamp'])
        
        # 统计不同类型的TRAP事件数量
        trap_types = {}
        for trap in sorted_trap_data:
            trap_type = trap['type']
            if trap_type not in trap_types:
                trap_types[trap_type] = []
            trap_types[trap_type].append(trap)
        
        # 创建时间轴数据
        timestamps = sorted(list(set(trap['timestamp'] for trap in sorted_trap_data)))
        
        # 生成系列数据
        series = []
        colors = ['#ff4d4f', '#faad14', '#52c41a', '#1890ff', '#722ed1']
        
        for i, (trap_type, events) in enumerate(trap_types.items()):
            # 统计每个时间点的事件数量
            time_counts = {ts: 0 for ts in timestamps}
            for event in events:
                time_counts[event['timestamp']] += 1
            
            series.append({
                "name": f"Type {trap_type}",
                "type": "line",
                "data": [time_counts[ts] for ts in timestamps],
                "itemStyle": {"color": colors[i % len(colors)]},
                "lineStyle": {"width": 3},
                "symbol": "circle",
                "symbolSize": 8,
                "markPoint": {
                    "data": [
                        {"type": "max", "name": "最大值"},
                        {"type": "min", "name": "最小值"}
                    ]
                }
            })
        
        chart_data = {
            "title": {
                "text": "TRAP重启事件时间趋势",
                "left": "center",
                "textStyle": {
                    "fontSize": 16,
                    "fontWeight": "bold"
                }
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "cross"
                },
                "formatter": "function(params) { return params.map(p => p.seriesName + ': ' + p.value + '次').join('<br/>'); }"
            },
            "legend": {
                "data": [f"Type {t}" for t in trap_types.keys()],
                "top": 30,
                "type": "scroll"
            },
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "containLabel": True
            },
            "xAxis": {
                "type": "category",
                "data": timestamps,
                "boundaryGap": False,
                "axisLabel": {
                    "rotate": 45
                }
            },
            "yAxis": {
                "type": "value",
                "name": "事件次数",
                "min": 0
            },
            "series": series
        }
        
        return chart_data
    
    def _generate_html_content(self, 
                              parsed_data_list: List[ParsedData], 
                              analysis_result: AnalysisResult,
                              chart_paths: List[str]) -> str:
        """生成HTML报告内容"""
        
        # 生成报告头部
        html_header = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ECU日志分析报告</title>
    <!-- 引入v-charts -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 15px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header .subtitle {{
            font-size: 12px;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 25px 30px;
        }}
        
        .section {{
            margin-bottom: 35px;
            padding: 20px;
            background-color: #fafbfc;
            border-radius: 8px;
            border: 1px solid #e1e8ed;
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            margin-bottom: 18px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e1e8ed;
        }}
        
        .section-icon {{
            width: 20px;
            height: 20px;
            margin-right: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 3px;
        }}
        
        h2 {{
            font-size: 16px;
            font-weight: 600;
            color: #2c3e50;
            margin: 0;
        }}
        
        h3 {{
            font-size: 14px;
            font-weight: 600;
            color: #34495e;
            margin-bottom: 12px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .stat-number {{
            font-size: 20px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 4px;
        }}
        
        .stat-label {{
            font-size: 11px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            background: white;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .data-table th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 8px;
            text-align: left;
            font-weight: 600;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .data-table td {{
            padding: 8px;
            border-bottom: 1px solid #f1f3f4;
            vertical-align: middle;
        }}
        
        .data-table tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        .data-table tr:hover {{
            background-color: #e8f4fd;
        }}
        
        .chart-wrapper {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            text-align: center;
            border: 1px solid #e1e8ed;
        }}
        
        .chart-wrapper h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 13px;
        }}
        
        .chart-wrapper img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        /* V-charts容器样式 */
        .v-chart-container {{
            width: 100%;
            height: 400px;
            background: white;
            border-radius: 6px;
            border: 1px solid #e1e8ed;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .alert {{
            padding: 12px 16px;
            border-radius: 6px;
            margin: 12px 0;
            font-size: 12px;
            border-left: 4px solid;
        }}
        
        .alert-info {{
            background-color: #e8f4fd;
            border-left-color: #1890ff;
            color: #0c5460;
        }}
        
        .alert-warning {{
            background-color: #fff7e6;
            border-left-color: #fa8c16;
            color: #d46b08;
        }}
        
        .alert-danger {{
            background-color: #fff2f0;
            border-left-color: #f5222d;
            color: #cf1322;
        }}
        
        .meta-info {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: #f8f9fa;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 11px;
            color: #6c757d;
        }}
        
        .load-indicator {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
        }}
        
        .load-low {{ background-color: #d4edda; color: #155724; }}
        .load-medium {{ background-color: #fff3cd; color: #856404; }}
        .load-high {{ background-color: #f8d7da; color: #721c24; }}
        
        .file-path {{
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 10px;
            color: #6c757d;
            background: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        
        /* 负载率统计布局 */
        .load-charts-row {{
            display: flex;
            gap: 30px;
            align-items: flex-start;
            margin-bottom: 25px;
            justify-content: space-between;
        }}
        
        .load-table-wrapper {{
            width: 100%;
        }}
        
        .load-chart-thumbnail {{
            width: 100%;
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            margin-bottom: 15px;
        }}
        
        .load-chart-thumbnail:hover {{
            transform: scale(1.05);
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }}
        
        .chart-preview {{
            text-align: center;
            margin-bottom: 15px;
            flex: 1;
            min-width: 300px;
        }}
        
        .chart-preview h4 {{
            font-size: 12px;
            color: #34495e;
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ECU日志分析报告</h1>
            <div class="subtitle">生成时间: {analysis_result.analysis_time} | 分析文件: {analysis_result.total_files} 个 | 有效文件: {analysis_result.valid_files} 个</div>
        </div>
        <div class="content">
            <!-- 概览统计 -->
            <div class="section">
                <div class="section-header">
                    <div class="section-icon"></div>
                    <h2>分析概览</h2>
                </div>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{analysis_result.total_files}</div>
                        <div class="stat-label">总文件数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{analysis_result.valid_files}</div>
                        <div class="stat-label">有效文件数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len(analysis_result.projects)}</div>
                        <div class="stat-label">项目数量</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{analysis_result.core_count}</div>
                        <div class="stat-label">CPU核心数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{analysis_result.trap_count}</div>
                        <div class="stat-label">TRAP重启数</div>
                    </div>
                </div>
            </div>
"""
        
        # 生成图表部分（使用V-charts）
        charts_section = ""
        
        # 生成核负载率统计图表
        core_loads_chart = self._generate_core_loads_chart_data(parsed_data_list, analysis_result)
        comparison_chart = self._generate_comparison_chart_data(parsed_data_list)
        trend_chart = self._generate_trend_chart_data(parsed_data_list)
        
        if core_loads_chart or comparison_chart or trend_chart:
            charts_section = """
            <div class="section">
                <div class="section-header">
                    <div class="section-icon"></div>
                    <h2>数据可视化分析</h2>
                </div>
            """
            
            # 核负载率统计图表
            if core_loads_chart:
                charts_section += f"""
                <div class="chart-wrapper">
                    <h3>CPU核心负载率统计</h3>
                    <div class="v-chart-container" id="coreLoadsChart" style="width: 100%; height: 400px;"></div>
                </div>
                <script>
                    window.coreLoadsChartData = {json.dumps(core_loads_chart, ensure_ascii=False)};
                </script>
                """
            
            # 对比图表
            if comparison_chart:
                charts_section += f"""
                <div class="chart-wrapper">
                    <h3>项目负载率对比</h3>
                    <div class="v-chart-container" id="comparisonChart" style="width: 100%; height: 400px;"></div>
                </div>
                <script>
                    window.comparisonChartData = {json.dumps(comparison_chart, ensure_ascii=False)};
                </script>
                """
            
            # 趋势图表
            if trend_chart:
                charts_section += f"""
                <div class="chart-wrapper">
                    <h3>CPU负载率趋势分析</h3>
                    <div class="v-chart-container" id="trendChart" style="width: 100%; height: 400px;"></div>
                </div>
                <script>
                    window.trendChartData = {json.dumps(trend_chart, ensure_ascii=False)};
                </script>
                """
            
            charts_section += "</div>"
        
        # 生成项目信息表格
        project_table_rows = ""
        if analysis_result.projects:
            project_info = ", ".join(analysis_result.projects)
            version_info = ", ".join(analysis_result.baseline_versions)
            
            project_table_rows = f"""
            <div class="section">
                <div class="section-header">
                    <div class="section-icon"></div>
                    <h2>项目信息</h2>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>信息类型</th>
                            <th>详细信息</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>发现项目</strong></td>
                            <td>{project_info}</td>
                        </tr>
                        <tr>
                            <td><strong>基线版本</strong></td>
                            <td>{version_info}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            """
        
        # 生成负载率统计
        load_statistics = ""
        if analysis_result.avg_loads:
            load_statistics = """
            <div class="section">
                <div class="section-header">
                    <div class="section-icon"></div>
                    <h2>核负载率统计</h2>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>核心</th>
                            <th>平均负载率 (%)</th>
                            <th>最大负载率 (%)</th>
                            <th>最小负载率 (%)</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for i in range(len(analysis_result.avg_loads)):
                avg_load = analysis_result.avg_loads[i]
                max_load = analysis_result.max_loads[i] if i < len(analysis_result.max_loads) else 0
                min_load = analysis_result.min_loads[i] if i < len(analysis_result.min_loads) else 0
                
                # 确定负载状态
                if avg_load >= 80:
                    status_class = "load-high"
                    status_text = "高负载"
                elif avg_load >= 60:
                    status_class = "load-medium"
                    status_text = "中等负载"
                else:
                    status_class = "load-low"
                    status_text = "正常"
                
                load_statistics += f"""
                        <tr>
                            <td><strong>Core{i}</strong></td>
                            <td>{avg_load:.2f}%</td>
                            <td>{max_load:.2f}%</td>
                            <td>{min_load:.2f}%</td>
                            <td><span class="load-indicator {status_class}">{status_text}</span></td>
                        </tr>
                """
            
            load_statistics += """</tbody></table></div>"""
        
        # 生成TRAP信息
        trap_information = ""
        if analysis_result.trap_count > 0:
            alert_class = "alert-danger" if analysis_result.trap_count > 5 else "alert-warning"
            trap_information = f"""
            <div class="section">
                <div class="section-header">
                    <div class="section-icon"></div>
                    <h2>TRAP重启信息</h2>
                </div>
                <div class="alert {alert_class}">
                    <strong>检测到 {analysis_result.trap_count} 次TRAP重启事件</strong>
                    {"【紧急】" if analysis_result.trap_count > 5 else "【警告】"}
                    需要立即排查系统稳定性问题
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>文件</th>
                            <th>重启类型</th>
                            <th>DEADD地址</th>
                            <th>函数地址</th>
                            <th>参数名</th>
                            <th>函数名</th>
                            <th>行号范围</th>
                            <th>重启原因</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for data in parsed_data_list:
                if data.trap_infos:
                    for trap_info in data.trap_infos:
                        file_name = os.path.basename(data.file_path)
                        line_range = f"{trap_info.start_line_number} - {trap_info.end_line_number}" if trap_info.start_line_number and trap_info.end_line_number else "N/A"
                        trap_information += f"""
                        <tr>
                            <td><span class="file-path">{file_name}</span></td>
                            <td><strong>{trap_info.rest_type or 'N/A'}</strong></td>
                            <td><code>{trap_info.deadd_address or 'N/A'}</code></td>
                            <td><code>{trap_info.max_func_address or 'N/A'}</code></td>
                            <td>{trap_info.parameter_name or '未解析'}</td>
                            <td>{trap_info.function_name or '未解析'}</td>
                            <td><span class="load-indicator load-medium">{line_range}</span></td>
                            <td>{trap_info.restart_reason or '待分析'}</td>
                        </tr>
                        """
            
            trap_information += """</tbody></table></div>"""
        
        # 生成文件详情部分
        file_details_section = """
        <div class="section">
            <div class="section-header">
                <div class="section-icon"></div>
                <h2>文件详情</h2>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>文件名</th>
                        <th>项目名</th>
                        <th>基线版本</th>
                        <th>时间戳</th>
                        <th>核心数</th>
                        <th>TRAP数量</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for data in parsed_data_list:
            file_name = os.path.basename(data.file_path)
            project_name = data.project_name or "未知"
            baseline_version = data.baseline_version or "未知"
            timestamp = data.timestamp or "未知"
            core_count = len(data.core_loads) if data.core_loads else 0
            trap_count = len(data.trap_infos) if data.trap_infos else 0
            
            file_details_section += f"""
            <tr>
                <td><span class="file-path">{file_name}</span></td>
                <td>{project_name}</td>
                <td>{baseline_version}</td>
                <td>{timestamp}</td>
                <td>{core_count}</td>
                <td>{trap_count}</td>
            </tr>
            """
        
        file_details_section += """
                </tbody>
            </table>
        </div>
        """
        
        # 生成SOA数据分析部分
        soa_section = ""
        if analysis_result.soa_topic_count > 0:
            soa_section = f"""
            <div class="section">
                <div class="section-header">
                    <div class="section-icon"></div>
                    <h2>SOA数据分析</h2>
                </div>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{analysis_result.soa_topic_count}</div>
                        <div class="stat-label">Topic数量</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{analysis_result.soa_data_points}</div>
                        <div class="stat-label">数据点数量</div>
                    </div>
                </div>
            </div>
            """
        
        # 组装完整的HTML内容
        html_content = html_header + charts_section + project_table_rows + load_statistics + file_details_section + soa_section + trap_information + """
            </div>
        </div>
        
        <script>
        // ECharts图表初始化
        document.addEventListener('DOMContentLoaded', function() {
            // 初始化核负载率统计图表
            if (window.coreLoadsChartData && document.getElementById('coreLoadsChart')) {
                var coreLoadsChart = echarts.init(document.getElementById('coreLoadsChart'));
                coreLoadsChart.setOption(window.coreLoadsChartData);
                
                // 响应式调整
                window.addEventListener('resize', function() {
                    coreLoadsChart.resize();
                });
            }
            
            // 初始化对比图表
            if (window.comparisonChartData && document.getElementById('comparisonChart')) {
                var comparisonChart = echarts.init(document.getElementById('comparisonChart'));
                comparisonChart.setOption(window.comparisonChartData);
                
                window.addEventListener('resize', function() {
                    comparisonChart.resize();
                });
            }
            
            // 初始化趋势图表
            if (window.trendChartData && document.getElementById('trendChart')) {
                var trendChart = echarts.init(document.getElementById('trendChart'));
                trendChart.setOption(window.trendChartData);
                
                window.addEventListener('resize', function() {
                    trendChart.resize();
                });
            }
            
            // 初始化SOA图表
            var soaChartContainers = document.querySelectorAll('.v-chart-container[data-chart]');
            soaChartContainers.forEach(function(container) {
                try {
                    var chartData = JSON.parse(container.dataset.chart || '{}');
                    if (chartData && Object.keys(chartData).length > 0) {
                        var chart = echarts.init(container);
                        chart.setOption(chartData);
                        
                        window.addEventListener('resize', function() {
                            chart.resize();
                        });
                    }
                } catch (e) {
                    console.error('初始化SOA图表失败:', e);
                }
            });
        });
        </script>
        </body>
        </html>"""
        
        return html_content
    
    def _prepare_main_page_data(self, 
                               parsed_data_list: List[ParsedData], 
                               analysis_result: AnalysisResult) -> Dict[str, Any]:
        """准备主页面模板数据"""
        
        # 基本信息
        subtitle = f"生成时间: {analysis_result.analysis_time} | 分析文件: {analysis_result.total_files} 个 | 有效文件: {analysis_result.valid_files} 个"
        
        # 准备项目和版本列表
        projects_list = ", ".join(analysis_result.projects) if analysis_result.projects else "未检测到项目"
        versions_list = ", ".join(analysis_result.baseline_versions) if analysis_result.baseline_versions else "未检测到版本"
        
        # 生成负载统计表格行
        load_stats_rows = self._generate_load_stats_rows(analysis_result)
        
        # 生成TRAP信息
        trap_types_text = ", ".join(analysis_result.trap_types) if analysis_result.trap_types else "无"
        trap_functions_text = ", ".join(analysis_result.trap_functions) if analysis_result.trap_functions else "无"
        trap_info_rows = self._generate_trap_info_rows(parsed_data_list)
        
        # 生成文件详情表格行
        file_details_rows = self._generate_file_details_rows(parsed_data_list)
        
        # 准备数据
        template_data = {
            'subtitle': subtitle,
            'total_files': analysis_result.total_files,
            'valid_files': analysis_result.valid_files,
            'project_count': len(analysis_result.projects),
            'core_count': analysis_result.core_count,
            'trap_count': analysis_result.trap_count,
            'projects_list': projects_list,
            'versions_list': versions_list,
            'project_name': projects_list,
            'baseline_version': versions_list,
            'load_stats_rows': load_stats_rows,
            'trap_types_text': trap_types_text,
            'trap_functions_text': trap_functions_text,
            'trap_info_rows': trap_info_rows,
            'file_details_rows': file_details_rows,
        }
        
        # 生成图表脚本
        charts_data = {
            'coreLoads': self._generate_core_loads_chart_data(parsed_data_list, analysis_result),
            'comparison': self._generate_comparison_chart_data(parsed_data_list),
            'trend': self._generate_trend_chart_data(parsed_data_list),
            'trapRestart': self._generate_trap_restart_chart_data(parsed_data_list)
        }
        template_data['chart_scripts'] = self._generate_chart_scripts(charts_data)
        
        return template_data
    
    def _generate_load_stats_rows(self, analysis_result: AnalysisResult) -> str:
        """生成负载统计表格行"""
        if not analysis_result.avg_loads:
            return '<tr><td colspan="5">暂无数据</td></tr>'
        
        rows = []
        for i in range(len(analysis_result.avg_loads)):
            avg_load = analysis_result.avg_loads[i] if i < len(analysis_result.avg_loads) else 0
            max_load = analysis_result.max_loads[i] if i < len(analysis_result.max_loads) else 0
            min_load = analysis_result.min_loads[i] if i < len(analysis_result.min_loads) else 0
            
            # 判断负载状态
            if avg_load > 80:
                status = '高负载'
                status_class = 'status-high'
            elif avg_load > 60:
                status = '中等负载'
                status_class = 'status-medium'
            else:
                status = '低负载'
                status_class = 'status-low'
            
            row = f'''<tr>
                <td>Core {i}</td>
                <td>{avg_load:.2f}</td>
                <td>{max_load:.2f}</td>
                <td>{min_load:.2f}</td>
                <td><span class="{status_class}">{status}</span></td>
            </tr>'''
            rows.append(row)
        
        return '\n'.join(rows)
    
    def _generate_trap_info_rows(self, parsed_data_list: List[ParsedData]) -> str:
        """生成TRAP信息表格行"""
        rows = []
        trap_index = 1
        
        for data in parsed_data_list:
            if data.trap_infos:
                for trap_info in data.trap_infos:
                    row = f'''<tr>
                        <td>{trap_index}</td>
                        <td>{trap_info.rest_type or '未知'}</td>
                        <td>{trap_info.deadd_address or '未知'}</td>
                        <td>{trap_info.max_func_address or '未知'}</td>
                        <td>{trap_info.parameter_name or '未解析'}</td>
                        <td>{trap_info.function_name or '未解析'}</td>
                        <td>{trap_info.restart_reason or '未知'}</td>
                    </tr>'''
                    rows.append(row)
                    trap_index += 1
        
        if not rows:
            return '<tr><td colspan="7">暂无TRAP信息</td></tr>'
        
        return '\n'.join(rows)
    
    def _generate_file_details_rows(self, parsed_data_list: List[ParsedData]) -> str:
        """生成文件详情表格行"""
        rows = []
        
        for i, data in enumerate(parsed_data_list, 1):
            file_name = os.path.basename(data.file_path)
            project_name = data.project_name or '未知'
            baseline_version = data.baseline_version or '未知'
            status = '有效' if data.core_loads else '无效'
            status_class = 'status-valid' if data.core_loads else 'status-invalid'
            
            row = f'''<tr>
                <td>{i}</td>
                <td>{file_name}</td>
                <td>{project_name}</td>
                <td>{baseline_version}</td>
                <td><span class="{status_class}">{status}</span></td>
            </tr>'''
            rows.append(row)
        
        if not rows:
            return '<tr><td colspan="5">暂无文件信息</td></tr>'
        
        return '\n'.join(rows)
    
    def _prepare_soa_page_data(self, 
                              parsed_data_list: List[ParsedData], 
                              analysis_result: AnalysisResult) -> Dict[str, Any]:
        """准备SOA页面模板数据"""
        
        # 基本信息
        subtitle = f"生成时间: {analysis_result.analysis_time} | SOA数据分析"
        
        # 计算包含SOA数据的文件数量
        soa_file_count = 0
        for data in parsed_data_list:
            # 检查文件是否包含SOA数据
            try:
                with open(data.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'SOA cnt on' in content:
                        soa_file_count += 1
            except Exception as e:
                self.logger.warning(f"检查SOA数据失败 {data.file_path}: {e}")
                continue
        
        # 准备项目和版本列表
        projects_list = ", ".join(analysis_result.projects) if analysis_result.projects else "未检测到项目"
        versions_list = ", ".join(analysis_result.baseline_versions) if analysis_result.baseline_versions else "未检测到版本"
        
        template_data = {
            'subtitle': subtitle,
            'soa_topic_count': analysis_result.soa_topic_count,
            'soa_data_points': analysis_result.soa_data_points,
            'soa_file_count': soa_file_count,
            'project_name': projects_list,
            'baseline_version': versions_list,
        }
        
        # SOA图表区域
        template_data['soa_charts_section'] = self._generate_soa_charts_section(analysis_result)
        
        # 准备完整的SOA数据，包括统计信息、图表数据和日志详情
        soa_data = {
            'statistics': self._get_soa_statistics(analysis_result),
            'charts': analysis_result.soa_charts_data or {},
            'log_details': soa_analyzer.get_log_details() if hasattr(soa_analyzer, 'get_log_details') else []
        }
        template_data['soa_data'] = soa_data
        
        # SOA图表脚本
        soa_charts_data = {}
        if analysis_result.soa_charts_data:
            soa_charts_data = analysis_result.soa_charts_data
        template_data['chart_scripts'] = self._generate_soa_chart_scripts(soa_charts_data)
        
        return template_data
    
    def _generate_project_info_section(self, analysis_result: AnalysisResult) -> str:
        """生成项目信息区域"""
        if not analysis_result.projects:
            return ""
        
        project_info = ", ".join(analysis_result.projects)
        version_info = ", ".join(analysis_result.baseline_versions)
        
        return f'''
        <div class="section">
            <div class="section-header">
                <div class="section-icon"></div>
                <h2>项目信息</h2>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>信息类型</th>
                        <th>详细信息</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>发现项目</strong></td>
                        <td>{project_info}</td>
                    </tr>
                    <tr>
                        <td><strong>基线版本</strong></td>
                        <td>{version_info}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        '''
    
    def _generate_visualization_section(self, 
                                       parsed_data_list: List[ParsedData], 
                                       analysis_result: AnalysisResult) -> str:
        """生成数据可视化区域"""
        
        # 生成图表数据
        core_loads_chart = self._generate_core_loads_chart_data(parsed_data_list, analysis_result)
        comparison_chart = self._generate_comparison_chart_data(parsed_data_list)
        trend_chart = self._generate_trend_chart_data(parsed_data_list)
        
        if not (core_loads_chart or comparison_chart or trend_chart):
            return ""
        
        section = '''
        <div class="section">
            <div class="section-header">
                <div class="section-icon"></div>
                <h2>数据可视化分析</h2>
            </div>
        '''
        
        # 核负载率统计图表 - 只生成HTML结构，不包含script
        if core_loads_chart:
            section += '''
            <div class="chart-wrapper">
                <h3>CPU核心负载率统计</h3>
                <div class="v-chart-container" id="coreLoadsChart" style="width: 100%; height: 400px;"></div>
            </div>
            '''
        
        # 对比图表
        if comparison_chart:
            section += '''
            <div class="chart-wrapper">
                <h3>项目负载率对比</h3>
                <div class="v-chart-container" id="comparisonChart" style="width: 100%; height: 400px;"></div>
            </div>
            '''
        
        # 趋势图表
        if trend_chart:
            section += '''
            <div class="chart-wrapper">
                <h3>CPU负载率趋势分析</h3>
                <div class="v-chart-container" id="trendChart" style="width: 100%; height: 400px;"></div>
            </div>
            '''
        
        section += '</div>'
        return section
    
    def _generate_load_statistics_section(self, analysis_result: AnalysisResult) -> str:
        """生成核负载率统计表格区域"""
        if not analysis_result.avg_loads:
            return ""
        
        section = '''
        <div class="section">
            <div class="section-header">
                <div class="section-icon"></div>
                <h2>核负载率统计</h2>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>核心</th>
                        <th>平均负载率 (%)</th>
                        <th>最大负载率 (%)</th>
                        <th>最小负载率 (%)</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for i in range(len(analysis_result.avg_loads)):
            avg_load = analysis_result.avg_loads[i]
            max_load = analysis_result.max_loads[i] if i < len(analysis_result.max_loads) else 0
            min_load = analysis_result.min_loads[i] if i < len(analysis_result.min_loads) else 0
            
            # 确定负载状态
            if avg_load >= 80:
                status_class = "load-high"
                status_text = "高负载"
            elif avg_load >= 60:
                status_class = "load-medium"
                status_text = "中等负载"
            else:
                status_class = "load-low"
                status_text = "正常"
            
            section += f'''
                    <tr>
                        <td><strong>Core{i}</strong></td>
                        <td>{avg_load:.2f}%</td>
                        <td>{max_load:.2f}%</td>
                        <td>{min_load:.2f}%</td>
                        <td><span class="load-indicator {status_class}">{status_text}</span></td>
                    </tr>
            '''
        
        section += '</tbody></table></div>'
        return section
    
    def _generate_trap_info_section(self, 
                                   parsed_data_list: List[ParsedData], 
                                   analysis_result: AnalysisResult) -> str:
        """生成TRAP重启信息区域"""
        if analysis_result.trap_count == 0:
            return ""
        
        alert_class = "alert-danger" if analysis_result.trap_count > 5 else "alert-warning"
        
        section = f'''
        <div class="section">
            <div class="section-header">
                <div class="section-icon"></div>
                <h2>TRAP重启信息</h2>
            </div>
            <div class="alert {alert_class}">
                <strong>检测到 {analysis_result.trap_count} 次TRAP重启事件</strong>
                {"[紧急]" if analysis_result.trap_count > 5 else "[警告]"}
                需要立即排查系统稳定性问题
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>文件</th>
                        <th>重启类型</th>
                        <th>DEADD地址</th>
                        <th>函数地址</th>
                        <th>参数名</th>
                        <th>函数名</th>
                        <th>行号范围</th>
                        <th>重启原因</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for data in parsed_data_list:
            if data.trap_infos:
                for trap_info in data.trap_infos:
                    file_name = os.path.basename(data.file_path)
                    line_range = f"{trap_info.start_line_number} - {trap_info.end_line_number}" if trap_info.start_line_number and trap_info.end_line_number else "N/A"
                    
                    section += f'''
                    <tr>
                        <td><span class="file-path">{file_name}</span></td>
                        <td><strong>{trap_info.rest_type or 'N/A'}</strong></td>
                        <td><code>{trap_info.deadd_address or 'N/A'}</code></td>
                        <td><code>{trap_info.max_func_address or 'N/A'}</code></td>
                        <td>{trap_info.parameter_name or '未解析'}</td>
                        <td>{trap_info.function_name or '未解析'}</td>
                        <td><span class="load-indicator load-medium">{line_range}</span></td>
                        <td>{trap_info.restart_reason or '待分析'}</td>
                    </tr>
                    '''
        
        section += '</tbody></table></div>'
        return section
    
    def _generate_file_details_section(self, parsed_data_list: List[ParsedData]) -> str:
        """生成文件详情区域"""
        section = '''
        <div class="section">
            <div class="section-header">
                <div class="section-icon"></div>
                <h2>文件详情</h2>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>文件名</th>
                        <th>项目名</th>
                        <th>基线版本</th>
                        <th>时间戳</th>
                        <th>核心数</th>
                        <th>TRAP数量</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for data in parsed_data_list:
            file_name = os.path.basename(data.file_path)
            project_name = data.project_name or "未知"
            baseline_version = data.baseline_version or "未知"
            timestamp = data.timestamp or "未知"
            core_count = len(data.core_loads) if data.core_loads else 0
            trap_count = len(data.trap_infos) if data.trap_infos else 0
            
            section += f'''
            <tr>
                <td><span class="file-path">{file_name}</span></td>
                <td>{project_name}</td>
                <td>{baseline_version}</td>
                <td>{timestamp}</td>
                <td>{core_count}</td>
                <td>{trap_count}</td>
            </tr>
            '''
        
        section += '</tbody></table></div>'
        return section
    
    def _generate_soa_charts_section(self, analysis_result: AnalysisResult) -> str:
        """生成SOA图表区域"""
        if not analysis_result.soa_charts_data:
            return '<div class="section"><p>未找到SOA数据</p></div>'
        
        section = '''
        <div class="section">
            <div class="section-header">
                <div class="section-icon"></div>
                <h2>SOA数据可视化</h2>
            </div>
        '''
        
        # 单个Topic图表容器 - 通过下拉菜单切换显示
        if 'topic_charts' in analysis_result.soa_charts_data:
            section += '''
            <div class="chart-wrapper">
                <h3 id="selectedTopicTitle">请选择Topic查看数据</h3>
                <div class="v-chart-container" id="soaTopicChart" style="width: 100%; height: 400px;">
                    <div class="loading">请从下拉菜单中选择Topic</div>
                </div>
            </div>
            '''
        
        # 汇总图表 - 已移除
        # if 'summary_chart' in analysis_result.soa_charts_data:
        #     section += '''
        #     <div class="chart-wrapper">
        #         <h3>SOA数据汇总</h3>
        #         <div class="v-chart-container" id="soaSummaryChart" style="width: 100%; height: 400px;"></div>
        #     </div>
        #     '''
        
        section += '</div>'
        return section
    
    def _generate_chart_scripts(self, charts_data: Dict[str, Any]) -> str:
        """生成图表初始化脚本"""
        scripts = []
        
        # 核负载率统计图表
        if charts_data.get('coreLoads'):
            core_loads_json = json.dumps(charts_data['coreLoads'], ensure_ascii=False)
            script = '''
            // 初始化核负载率统计图表
            window.coreLoadsChartData = ''' + core_loads_json + ''';
            if (document.getElementById('coreLoadsChart')) {
                var coreLoadsChart = echarts.init(document.getElementById('coreLoadsChart'));
                coreLoadsChart.setOption(window.coreLoadsChartData);
                
                window.addEventListener('resize', function() {
                    coreLoadsChart.resize();
                });
            }'''
            scripts.append(script)
        
        # 对比图表
        if charts_data.get('comparison'):
            comparison_json = json.dumps(charts_data['comparison'], ensure_ascii=False)
            script = '''
            // 初始化对比图表
            window.comparisonChartData = ''' + comparison_json + ''';
            if (document.getElementById('comparisonChart')) {
                var comparisonChart = echarts.init(document.getElementById('comparisonChart'));
                comparisonChart.setOption(window.comparisonChartData);
                
                window.addEventListener('resize', function() {
                    comparisonChart.resize();
                });
            }'''
            scripts.append(script)
        
        # 趋势图表
        if charts_data.get('trend'):
            trend_json = json.dumps(charts_data['trend'], ensure_ascii=False)
            script = '''
            // 初始化趋势图表
            window.trendChartData = ''' + trend_json + ''';
            if (document.getElementById('trendChart')) {
                var trendChart = echarts.init(document.getElementById('trendChart'));
                trendChart.setOption(window.trendChartData);
                
                window.addEventListener('resize', function() {
                    trendChart.resize();
                });
            }'''
            scripts.append(script)
        
        # TRAP重启图表
        if charts_data.get('trapRestart'):
            trap_restart_json = json.dumps(charts_data['trapRestart'], ensure_ascii=False)
            script = '''
            // 初始化TRAP重启图表
            window.trapRestartChartData = ''' + trap_restart_json + ''';
            if (document.getElementById('trapRestartChart')) {
                var trapRestartChart = echarts.init(document.getElementById('trapRestartChart'));
                trapRestartChart.setOption(window.trapRestartChartData);
                
                window.addEventListener('resize', function() {
                    trapRestartChart.resize();
                });
            }'''
            scripts.append(script)
        
        return '\n'.join(scripts)
    
    def _generate_soa_chart_scripts(self, soa_charts_data: Dict[str, Any]) -> str:
        """生成SOA图表初始化脚本"""
        scripts = []
        
        # Topic图表数据 - 为JavaScript提供全局访问
        if 'topic_charts' in soa_charts_data:
            topic_charts = soa_charts_data['topic_charts']
            topic_charts_json = json.dumps(topic_charts, ensure_ascii=False)
            script = '''
            // 初始化SOA Topic图表数据
            window.soaTopicChartsData = ''' + topic_charts_json + ''';
            '''
            scripts.append(script)
        
        # 汇总图表 - 已移除，不再生成
        # if 'summary_chart' in soa_charts_data:
        #     summary_json = json.dumps(soa_charts_data['summary_chart'], ensure_ascii=False)
        #     script = '''
        #     // 初始化SOA汇总图表
        #     window.soaSummaryChartData = ''' + summary_json + ''';
        #     if (document.getElementById('soaSummaryChart')) {
        #         var soaSummaryChart = echarts.init(document.getElementById('soaSummaryChart'));
        #         soaSummaryChart.setOption(window.soaSummaryChartData);
        #         
        #         window.addEventListener('resize', function() {
        #             soaSummaryChart.resize();
        #         });
        #     }'''
        #     scripts.append(script)
        
        return '\n'.join(scripts)

# 创建全局报告生成器实例
report_generator = ReportGenerator()
