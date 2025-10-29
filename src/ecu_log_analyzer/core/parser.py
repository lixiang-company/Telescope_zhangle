# -*- coding: utf-8 -*-
"""
日志解析器模块（核心实现）
支持流式处理、配置接入与TRAP信息解析
"""

import os
import re
import logging
from typing import List, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager

from ..config.settings import Config
# 延迟导入以避免循环引用
# from ..analyzers.trap_analyzer import TrapAnalyzer, TrapInfo
from ..utils.file_utils import file_handler, memory_manager, cache_manager
from .performance import parallel_processor, smart_cache, performance_monitor


@dataclass
class ParsedData:
    project_name: Optional[str] = None
    baseline_version: Optional[str] = None
    core_loads: List[float] = field(default_factory=list)
    timestamp: Optional[str] = None
    file_path: str = ""
    trap_infos: List = field(default_factory=list)  # 暂时使用List而不TrapInfo


class FileParseError(Exception):
    """文件解析异常"""
    pass


class LogParser:
    def __init__(self, cfg=None, map_file_path: Optional[str] = None):
        self.cfg = cfg or Config()
        self.logger = logging.getLogger(__name__)
        # 延迟初始化TrapAnalyzer
        self._trap_analyzer = None
        self._map_file_path = map_file_path
    
    @property
    def trap_analyzer(self):
        """Lazy property for TrapAnalyzer"""
        if self._trap_analyzer is None:
            from ..analyzers.trap_analyzer import TrapAnalyzer
            self._trap_analyzer = TrapAnalyzer(self._map_file_path) if self._map_file_path else TrapAnalyzer()
        return self._trap_analyzer

    def parse_file(self, file_path: str) -> ParsedData:
        self.logger.info(f"开始解析文件: {file_path}")

        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return ParsedData(file_path=file_path)

        # 检查智能缓存
        cached_result = smart_cache.get(file_path)
        if cached_result:
            self.logger.info(f"使用智能缓存结果: {file_path}")
            return cached_result

        file_size = os.path.getsize(file_path)
        if file_size > self.cfg.system.max_file_size_mb * 1024 * 1024:
            self.logger.warning(f"文件过大，跳过: {file_path}")
            return ParsedData(file_path=file_path)

        parsed = ParsedData(file_path=file_path)

        with memory_manager.memory_monitor(f"解析文件 {os.path.basename(file_path)}"):
            if file_size <= 10 * 1024 * 1024:
                try:
                    with file_handler.safe_open(file_path, 'r') as f:
                        content = f.read()
                except Exception as e:
                    self.logger.error(f"读取文件失败 {file_path}: {e}")
                    return parsed

                parsed.project_name = self._extract_project_name(content, file_path)
                parsed.baseline_version = self._extract_baseline_version(content)
                parsed.core_loads = self._extract_core_loads(content)
                parsed.trap_infos = self._extract_trap_info(content)
                parsed.timestamp = self._extract_timestamp(file_path, content)
            else:
                # 大文件使用流式处理
                parsed = self._parse_large_file(file_path)

        # 智能缓存结果
        smart_cache.set(file_path, parsed)
        return parsed

    def _parse_large_file(self, file_path: str) -> ParsedData:
        """大文件流式处理"""
        project_names = set()
        baseline_versions = set()
        latest_core_loads: List[float] = []
        timestamps = set()
        
        try:
            for line in file_handler.read_file_lines(file_path):
                if not line:
                    continue
                pn = self._extract_project_name(line, file_path, line_mode=True)
                if pn:
                    project_names.add(pn)
                bv = self._extract_baseline_version(line)
                if bv:
                    baseline_versions.add(bv)
                loads = self._extract_core_loads(line)
                if loads:
                    latest_core_loads = loads
                ts = self._extract_timestamp_from_line(line)
                if ts:
                    timestamps.add(ts)
        except Exception as e:
            self.logger.error(f"流式解析失败 {file_path}: {e}")
            return ParsedData(file_path=file_path)
        
        return ParsedData(
            file_path=file_path,
            project_name=next(iter(project_names), None),
            baseline_version=next(iter(baseline_versions), None),
            core_loads=latest_core_loads,
            timestamp=next(iter(timestamps), None)
        )
    def parse_directory(self, directory: str, use_parallel: bool = True) -> List[ParsedData]:
        if not os.path.exists(directory) or not os.path.isdir(directory):
            self.logger.error(f"目录不存在: {directory}")
            return []
        
        # 收集所有日志文件
        log_files = []
        for root, _dirs, files in os.walk(directory):
            for name in files:
                # 兼容无后缀文件
                has_ext = os.path.splitext(name)[1] != ""
                if any(name.lower().endswith(ext) for ext in self.cfg.system.log_extensions) or not has_ext:
                    log_files.append(os.path.join(root, name))
        
        if not log_files:
            self.logger.warning(f"目录中未找到日志文件: {directory}")
            return []
        
        self.logger.info(f"找到 {len(log_files)} 个日志文件")
        
        if use_parallel and len(log_files) > 1:
            # 并行处理
            self.logger.info("使用并行处理模式")
            with performance_monitor.measure_performance("并行解析目录", len(log_files)):
                results = parallel_processor.process_files_parallel(
                    log_files, 
                    self.parse_file
                )
            # 过滤None结果
            return [r for r in results if r is not None]
        else:
            # 串行处理
            self.logger.info("使用串行处理模式")
            results = []
            with performance_monitor.measure_performance("串行解析目录", len(log_files)):
                for file_path in log_files:
                    result = self.parse_file(file_path)
                    if result:
                        results.append(result)
            return results

    @contextmanager
    def _safe_open(self, file_path: str):
        fh = None
        try:
            fh = open(file_path, 'r', encoding=self.cfg.system.file_encoding, errors='ignore')
            yield fh
        finally:
            try:
                if fh:
                    fh.close()
            except Exception:
                pass

    def _extract_project_name(self, content: str, file_path: str, line_mode: bool = False) -> Optional[str]:
        """提取项目名称"""
        # 优先级1: 从日志行中提取时间后面的项目名称 (如: "2025-08-25 16:53:41.276 BZCU I 02c5 {TRAP-RST}:Reset Info:")
        time_project_pattern = r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?\s+([A-Z]+[A-Z0-9_]*)\s+[A-Z]\s+[a-f0-9]+'
        m = re.search(time_project_pattern, content)
        if m:
            project_name = m.group(1).strip()
            self.logger.debug(f"从时间戳后提取到项目名称: {project_name}")
            return project_name
        
        # 优先级2: RMR模式
        m = re.search(r'RMR:([^;:,\s]+)', content)
        if m:
            project_name = m.group(1).strip()
            self.logger.debug(f"从RMR模式提取到项目名称: {project_name}")
            return project_name
        
        # 优先级3: 从文件名提取
        try:
            filename = os.path.basename(file_path)
            m2 = re.search(r'([A-Z]+[A-Z0-9_]*)-[0-9]+', filename)
            if m2:
                project_name = m2.group(1)
                self.logger.debug(f"从文件名提取到项目名称: {project_name}")
                return project_name
        except Exception:
            pass
        
        # 优先级4: 其他模式
        for pat in [r'Project:\s*([^\n\r]+)', r'项目:\s*([^\n\r]+)', r'ECU:\s*([^\n\r]+)']:
            m3 = re.search(pat, content, re.IGNORECASE)
            if m3:
                project_name = m3.group(1).strip()
                self.logger.debug(f"从其他模式提取到项目名称: {project_name}")
                return project_name
        
        self.logger.debug("未找到项目名称")
        return None

    def _extract_baseline_version(self, content: str) -> Optional[str]:
        for pat in [r'SWVerNum\s*:\s*([0-9a-fA-Fx]+)', r'version:\s*([0-9a-fA-Fx]+)']:
            m = re.search(pat, content, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _extract_core_loads(self, content: str) -> List[float]:
        loads_strs = re.findall(r'\[CPU_LOAD\]:core\s+load:\s*([\d.,\s]+?)(?=,\s*mcu_version|\n|$)', content, re.IGNORECASE)
        if not loads_strs:
            loads_strs = re.findall(r'core\s+load:\s*([\d.,\s]+?)(?=,\s*mcu_version|\n|$)', content, re.IGNORECASE)
        if loads_strs:
            latest = loads_strs[-1]
            try:
                values: List[float] = []
                for v in latest.split(','):
                    v = v.strip()
                    if v:
                        values.append(float(v))
                return values
            except Exception:
                return []
        return []

    def _extract_trap_info(self, content: str) -> List:
        try:
            return self.trap_analyzer.analyze_trap_logs(content) or []
        except Exception as e:
            self.logger.warning(f"TRAP解析失败: {e}")
            return []

    def _extract_timestamp(self, file_path: str, content: str) -> Optional[str]:
        filename = os.path.basename(file_path)
        for pat in [r'(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2})', r'(\d{8}_\d{6})']:
            m = re.search(pat, filename)
            if m:
                return m.group(1)
        for pat in [r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})']:
            m = re.search(pat, content)
            if m:
                return m.group(1)
        return None

    def _extract_timestamp_from_line(self, line: str) -> Optional[str]:
        for pat in [r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})']:
            m = re.search(pat, line)
            if m:
                return m.group(1)
        return None


def create_parser_with_map() -> LogParser:
    """创建带有map文件的解析器"""
    possible_map_paths = [
        # 相对路径
        "./BZCU_VecorARCode.map",
        "../BZCU_VecorARCode.map",
        "../../BZCU_VecorARCode.map",
        
        # data目录中的map文件
        "./data/sample_logs/BZCU_VecorARCode.map",
        "../data/sample_logs/BZCU_VecorARCode.map",
        "../../data/sample_logs/BZCU_VecorARCode.map",
        
        # 绝对路径（Windows）
        "d:/telescope/ecu_info_check/BZCU_VecorARCode.map",
        "c:/telescope/ecu_info_check/BZCU_VecorARCode.map",
        
        # 其他可能的路径
        "../ecu_info_check/BZCU_VecorARCode.map",
        "./ecu_info_check/BZCU_VecorARCode.map",
    ]
    
    map_file_path: Optional[str] = None
    for path in possible_map_paths:
        try:
            if os.path.exists(path):
                map_file_path = path
                print(f"✅ 找到map文件: {path}")
                break
        except Exception:
            continue
    
    if not map_file_path:
        print("⚠️  未找到map文件，TRAP分析将使用默认符号名")
    
    return LogParser(map_file_path=map_file_path)


parser = create_parser_with_map()