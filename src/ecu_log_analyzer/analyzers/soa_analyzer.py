# -*- coding: utf-8 -*-
"""
SOA数据分析模块
负责分析SOA通信数据并生成可视化图表
"""

import re
import os
import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from ..config.settings import Config
from .base import BaseAnalyzer, AnalysisContext

@dataclass
class SOAData:
    """SOA数据结构"""
    timestamp: str  # 时间戳
    base_index: int  # 基础索引 (如 0, 32, 64, 96)
    counts: List[int]  # 计数值列表
    data_type: str  # 数据类型: "cnt" 或 "drop"
    file_path: str  # 文件路径
    line_number: int  # 行号
    raw_line: str  # 原始日志行
    
@dataclass
class TopicData:
    """Topic数据结构"""
    topic_name: str  # Topic名称
    topic_index: int  # Topic索引
    send_counts: List[Tuple[str, int]]  # 发送计数 [(timestamp, count), ...]
    receive_counts: List[Tuple[str, int]]  # 接收计数 [(timestamp, count), ...]
    drop_counts: List[Tuple[str, int]]  # 丢失计数 [(timestamp, count), ...]

class SOAAnalyzer(BaseAnalyzer):
    """SOA数据分析器"""
    
    def __init__(self):
        super().__init__("SOAAnalyzer")
        self.soa_data_list: List[SOAData] = []
        self.topic_list: List[str] = []
        self.topic_data_dict: Dict[str, TopicData] = {}
        
    def initialize(self, config: Any = None) -> bool:
        """初始化SOA分析器"""
        return super().initialize(config)
        
    def analyze(self, data: Any, context: Optional[AnalysisContext] = None) -> Any:
        """分析SOA数据"""
        if isinstance(data, str):  # 文件路径
            return self.parse_log_file(data)
        elif isinstance(data, list):  # 数据列表
            for item in data:
                if hasattr(item, 'file_path'):
                    self.parse_log_file(item.file_path)
            return self.process_soa_data()
        return None
        
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "max_topics": 1000,
            "enable_charts": True,
            "chart_format": "echarts"
        }
        
    def load_topic_list(self, json_path: str) -> bool:
        """从Summary_Report.json加载Topic列表"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if "TOPIC" in data:
                self.topic_list = data["TOPIC"]
                self.logger.info(f"成功加载 {len(self.topic_list)} 个Topic")
                return True
            elif "topic" in data:
                self.topic_list = data["topic"]
                self.logger.info(f"成功加载 {len(self.topic_list)} 个Topic")
                return True
            else:
                self.logger.warning(f"JSON文件中未找到TOPIC或topic字段，可用字段: {list(data.keys())}")
                return False
                
        except Exception as e:
            self.logger.error(f"加载Topic列表失败: {e}")
            return False
    
    def parse_soa_line(self, line: str, file_path: str = "", line_number: int = 0) -> Optional[SOAData]:
        """解析SOA日志行"""
        # 匹配多种格式:
        # 1. SOA cnt on: 2025-08-25 16:52:08.434 BZCU I 5ae0 SOA cnt on0:20,45109,...
        # 2. SOA ASW drop cnt on: 2025-08-20 15:12:35.947 DZCU I f2d7 SOA ASW drop cnt on0:0,0,0,...
        # 3. (ZCAN) SOA cnt on: 2026-02-02 15:10:24.573 PZCU I 4793 (ZCAN) SOA cnt on0:0,2,182426,...
        # 4. (ZCAN) SOA ASW drop cnt on: 2026-02-02 15:10:24.573 PZCU I 4794 (ZCAN) SOA ASW drop cnt on104:0,0,0,...
        
        # 匹配SOA cnt on (支持可选的 (ZCAN) 前缀)
        cnt_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}).*?(?:\(ZCAN\)\s*)?SOA cnt on(\d+):([\d,]+)'
        cnt_match = re.search(cnt_pattern, line)
        
        if cnt_match:
            timestamp = cnt_match.group(1)
            base_index = int(cnt_match.group(2))
            counts_str = cnt_match.group(3)
            counts = [int(x) for x in counts_str.split(',')]
            
            return SOAData(timestamp=timestamp, base_index=base_index, counts=counts, data_type="cnt", 
                         file_path=file_path, line_number=line_number, raw_line=line.strip())
        
        # 匹配SOA ASW drop cnt on (支持可选的 (ZCAN) 前缀)
        drop_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}).*?(?:\(ZCAN\)\s*)?SOA ASW drop cnt on(\d+):([\d,]+)'
        drop_match = re.search(drop_pattern, line)
        
        if drop_match:
            timestamp = drop_match.group(1)
            base_index = int(drop_match.group(2))
            counts_str = drop_match.group(3)
            counts = [int(x) for x in counts_str.split(',')]
            
            return SOAData(timestamp=timestamp, base_index=base_index, counts=counts, data_type="drop",
                         file_path=file_path, line_number=line_number, raw_line=line.strip())
        
        return None
    
    def parse_log_file(self, file_path: str) -> int:
        """解析日志文件中的SOA数据"""
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"文件不存在: {file_path}")
                return 0
            
            soa_count = 0
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    soa_data = self.parse_soa_line(line, file_path, line_num)
                    if soa_data:
                        self.soa_data_list.append(soa_data)
                        soa_count += 1
            
            if soa_count > 0:
                self.logger.info(f"从 {file_path} 解析到 {soa_count} 条SOA数据")
            
            return soa_count
            
        except Exception as e:
            self.logger.error(f"解析文件 {file_path} 失败: {e}")
            return 0
    
    def process_soa_data(self) -> bool:
        """处理SOA数据，生成Topic数据"""
        if not self.topic_list:
            self.logger.warning("Topic列表为空，无法处理SOA数据")
            return False
            
        if not self.soa_data_list:
            self.logger.warning("SOA数据列表为空，无法处理")
            return False
        
        # 按时间戳分组
        timestamp_groups = {}
        for soa_data in self.soa_data_list:
            if soa_data.timestamp not in timestamp_groups:
                timestamp_groups[soa_data.timestamp] = []
            timestamp_groups[soa_data.timestamp].append(soa_data)
        
        # 创建Topic名称到索引的映射
        # 注意：同一个Topic名称在列表中可能出现1次或2次
        # 第一次出现为收数据，第二次出现为发数据
        topic_name_to_indices = {}
        for i, topic_name in enumerate(self.topic_list):
            if topic_name not in topic_name_to_indices:
                topic_name_to_indices[topic_name] = []
            topic_name_to_indices[topic_name].append(i)
        
        # 初始化Topic数据字典（按唯一名称）
        for topic_name in topic_name_to_indices.keys():
            self.topic_data_dict[topic_name] = TopicData(
                topic_name=topic_name,
                topic_index=0,  # 不再使用原始索引
                send_counts=[],
                receive_counts=[],
                drop_counts=[]
            )
        
        # 处理每个时间戳的数据
        for timestamp, data_list in timestamp_groups.items():
            # 分别处理cnt和drop数据
            cnt_data = [d for d in data_list if d.data_type == "cnt"]
            drop_data = [d for d in data_list if d.data_type == "drop"]
            
            # 处理cnt数据（收发数据）
            if cnt_data:
                max_index = max((soa_data.base_index + len(soa_data.counts) for soa_data in cnt_data), default=0)
                full_counts = [0] * max_index
                
                for soa_data in cnt_data:
                    base_idx = soa_data.base_index
                    for i, count in enumerate(soa_data.counts):
                        if base_idx + i < len(full_counts):
                            full_counts[base_idx + i] = count
                
                # 为每个Topic提取收数据和发数据
                for topic_name, indices in topic_name_to_indices.items():
                    topic_data = self.topic_data_dict[topic_name]
                    
                    # 第一个索引对应收数据（第一次出现）
                    if len(indices) > 0 and indices[0] < len(full_counts):
                        receive_count = full_counts[indices[0]]
                        topic_data.receive_counts.append((timestamp, receive_count))
                    
                    # 第二个索引对应发数据（第二次出现，如果存在）
                    if len(indices) > 1 and indices[1] < len(full_counts):
                        send_count = full_counts[indices[1]]
                        topic_data.send_counts.append((timestamp, send_count))
            
            # 处理drop数据（丢失数据）
            if drop_data:
                max_index = max((soa_data.base_index + len(soa_data.counts) for soa_data in drop_data), default=0)
                full_drop_counts = [0] * max_index
                
                for soa_data in drop_data:
                    base_idx = soa_data.base_index
                    for i, count in enumerate(soa_data.counts):
                        if base_idx + i < len(full_drop_counts):
                            full_drop_counts[base_idx + i] = count
                
                # 为每个Topic提取丢失数据（只使用第一个索引，避免重复）
                for topic_name, indices in topic_name_to_indices.items():
                    topic_data = self.topic_data_dict[topic_name]
                    
                    # 只使用第一个索引对应的丢失数据（避免重复添加）
                    if len(indices) > 0 and indices[0] < len(full_drop_counts):
                        drop_count = full_drop_counts[indices[0]]
                        topic_data.drop_counts.append((timestamp, drop_count))
        
        self.logger.info(f"成功处理 {len(self.topic_data_dict)} 个Topic的SOA数据")
        return True
    
    def get_log_details(self) -> List[Dict[str, Any]]:
        """获取SOA日志详细信息"""
        log_details = []
        
        for soa_data in self.soa_data_list:
            # 提取文件名（去掉路径，只保留文件名）
            file_name = os.path.basename(soa_data.file_path) if soa_data.file_path else "未知文件"
            
            # 截断过长的日志行
            raw_line = soa_data.raw_line
            if len(raw_line) > 200:
                raw_line = raw_line[:200] + "..."
            
            log_details.append({
                "file_name": file_name,
                "line_number": soa_data.line_number,
                "raw_line": raw_line,
                "data_type": soa_data.data_type,
                "timestamp": soa_data.timestamp
            })
        
        # 按文件名和行号排序
        log_details.sort(key=lambda x: (x["file_name"], x["line_number"]))
        
        return log_details
    
    def generate_topic_charts_data(self) -> Dict[str, Dict]:
        """为每个Topic生成v-charts数据"""
        charts_data = {}
        
        # 生成所有有实际数据的Topic的图表，不再限制数量
        for topic_name, topic_data in self.topic_data_dict.items():
            # 检查是否有非零的接收数据或发送数据
            has_receive_data = any(count > 0 for _, count in topic_data.receive_counts)
            has_send_data = any(count > 0 for _, count in topic_data.send_counts)
            has_drop_data = any(count > 0 for _, count in topic_data.drop_counts)
            
            if has_receive_data or has_send_data or has_drop_data:
                # 每条折线独立，0值用null替换（但丢失数据保留0值以便显示）
                # 接收数据：0值替换为null
                recv_data = [[t, count if count > 0 else None] for t, count in topic_data.receive_counts]
                # 发送数据：0值替换为null
                send_data = [[t, count if count > 0 else None] for t, count in topic_data.send_counts]
                # 丢失数据：保留0值（不转换为null），以便在图表中显示为y=0的折线
                lost_data = [[t, count] for t, count in topic_data.drop_counts]
                
                # 生成v-charts数据
                chart_data = {
                    "title": {
                        "text": f"Topic: {topic_name} 收发数据",
                        "left": "center"
                    },
                    "tooltip": {
                        "trigger": "axis",
                        "axisPointer": {
                            "type": "cross"
                        }
                    },
                    "legend": {
                        "data": [], "top": 30
                    },
                    "xAxis": {
                        "type": "time"
                    },
                    "yAxis": {
                        "type": "value",
                        "name": "数据量"
                    },
                    "series": []
                }
                
                # 添加接收数据系列（如果有非零数据）
                if has_receive_data:
                    chart_data["series"].append({
                        "name": "接收数据",
                        "type": "line",
                        "data": recv_data,
                        "itemStyle": {"color": "#91cc75"},
                        "lineStyle": {"width": 2},
                        "symbol": "rect",
                        "connectNulls": False
                    })
                    chart_data["legend"]["data"].append("接收数据")
                
                # 添加发送数据系列（如果有非零数据）
                if has_send_data:
                    chart_data["series"].append({
                        "name": "发送数据",
                        "type": "line",
                        "data": send_data,
                        "itemStyle": {"color": "#5470c6"},
                        "lineStyle": {"width": 2},
                        "symbol": "circle",
                        "connectNulls": False
                    })
                    chart_data["legend"]["data"].append("发送数据")
                
                # 添加丢失数据系列（始终添加，即使全为0也显示y=0的折线）
                if lost_data:
                    chart_data["series"].append({
                        "name": "丢失数据",
                        "type": "line",
                        "data": lost_data,
                        "itemStyle": {"color": "#ee6666"},
                        "lineStyle": {"width": 2},
                        "symbol": "x",
                        "connectNulls": False
                    })
                    chart_data["legend"]["data"].append("丢失数据")
                
                charts_data[topic_name] = chart_data
        
        return charts_data
    
    def generate_summary_chart_data(self) -> Dict:
        """生成SOA数据汇总v-charts数据"""
        # 计算每个时间点的总发送、接收和丢失数据
        timestamps = set()
        for topic_data in self.topic_data_dict.values():
            for t, _ in topic_data.receive_counts:
                timestamps.add(t)
            for t, _ in topic_data.send_counts:
                timestamps.add(t)
            for t, _ in topic_data.drop_counts:
                timestamps.add(t)
        
        # 如果没有时间戳数据，返回空图表
        if not timestamps:
            self.logger.warning("没有找到SOA时间戳数据，无法生成汇总图表")
            return {}
        
        timestamps = sorted(list(timestamps))
        total_send = [0] * len(timestamps)
        total_recv = [0] * len(timestamps)
        total_lost = [0] * len(timestamps)
        
        for topic_data in self.topic_data_dict.values():
            # 只处理有实际数据的Topic
            has_receive_data = any(count > 0 for _, count in topic_data.receive_counts)
            has_send_data = any(count > 0 for _, count in topic_data.send_counts)
            has_drop_data = any(count > 0 for _, count in topic_data.drop_counts)
            
            if not (has_receive_data or has_send_data or has_drop_data):
                continue  # 跳过没有实际数据的Topic
                
            for i, timestamp in enumerate(timestamps):
                # 查找该时间点的接收数据
                for t, count in topic_data.receive_counts:
                    if t == timestamp:
                        total_recv[i] += count
                        break
                
                # 查找该时间点的发送数据
                for t, count in topic_data.send_counts:
                    if t == timestamp:
                        total_send[i] += count
                        break
            
            # 计算丢失数据（从日志中获取的真实丢失数据）
            for t, count in topic_data.drop_counts:
                for i, timestamp in enumerate(timestamps):
                    if t == timestamp:
                        total_lost[i] += count
                        break
        
        # 保留所有时间点（包括值为0的合法数据），仅在不存在任何数据记录时不加入时间点
        self.logger.info(f"SOA汇总图表数据生成: {len(timestamps)} 个时间点, 总接收: {sum(total_recv)}, 总发送: {sum(total_send)}, 总丢失: {sum(total_lost)}")
        
        # 生成v-charts数据
        chart_data = {
            "title": {
                "text": "SOA通信数据汇总",
                "left": "center"
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "cross"
                }
            },
            "legend": {
                "data": ["总接收数据", "总发送数据"],
                "top": 30
            },
            "xAxis": {
                "type": "category",
                "data": timestamps
            },
            "yAxis": {
                "type": "value",
                "name": "数据包数量"
            },
            "series": [
                {
                    "name": "总接收数据",
                    "type": "line",
                    "data": total_recv,
                    "itemStyle": {"color": "#91cc75"},
                    "lineStyle": {"width": 2},
                    "connectNulls": False
                },
                {
                    "name": "总发送数据",
                    "type": "line",
                    "data": total_send,
                    "itemStyle": {"color": "#5470c6"},
                    "lineStyle": {"width": 2},
                    "connectNulls": False
                }
            ]
        }
        
        # 如果有丢失数据，添加丢失数据系列
        if any(total_lost):
            chart_data["series"].append({
                "name": "总丢失数据",
                "type": "line",
                "data": total_lost,
                "itemStyle": {"color": "#ee6666"},
                "lineStyle": {"width": 2},
                "symbol": "x"
            })
            # 更新图例数据
            chart_data["legend"]["data"].append("总丢失数据")
        
        return chart_data

    def generate_statistics(self) -> Dict[str, Any]:
        """生成SOA统计信息（按Summary_Report.json中的topic列表计数，允许重复）"""
        topic_count = len(self.topic_list)
        topics_with_data = 0
        topics_without_data = 0
        total_data_points = 0
        
        # 逐个topic（按原顺序）统计是否有数据，重复也单独计数
        for topic_name in self.topic_list:
            td = self.topic_data_dict.get(topic_name)
            has_receive_data = False
            has_send_data = False
            has_drop_data = False
            if td:
                has_receive_data = any(count > 0 for _, count in td.receive_counts)
                has_send_data = any(count > 0 for _, count in td.send_counts)
                has_drop_data = any(count > 0 for _, count in td.drop_counts)
                # 数据点数量（不去重，累计唯一topic的数据点）
                total_data_points += len(td.receive_counts)
                total_data_points += len(td.send_counts)
                total_data_points += len(td.drop_counts)
            
            if has_receive_data or has_send_data or has_drop_data:
                topics_with_data += 1
            else:
                topics_without_data += 1
        
        # 总丢失数据按唯一topic累计
        total_lost_data = 0
        for td in self.topic_data_dict.values():
            total_lost_data += sum(count for _, count in td.drop_counts)
        
        return {
            "topic_count": topic_count,
            "data_points": total_data_points,
            "topics_with_data": topics_with_data,
            "topics_without_data": topics_without_data,
            "total_lost_data": total_lost_data
        }

# 创建全局SOA分析器实例
soa_analyzer = SOAAnalyzer()
