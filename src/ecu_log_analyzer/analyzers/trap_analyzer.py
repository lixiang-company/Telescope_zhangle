# -*- coding: utf-8 -*-
"""
TRAP重启日志分析器模块
负责解析ECU日志文件中的TRAP-RST重启信息，提取Rest Type、DEADD、FuncX等信息
并通过map文件解析出对应的参数名和函数名
"""

import re
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import time
import concurrent.futures
from threading import Lock

from ..config.settings import Config

# 创建全局配置实例
config = Config()

@dataclass
class TrapInfo:
    """TRAP重启信息数据结构"""
    rest_type: Optional[str] = None
    deadd_address: Optional[str] = None
    func_addresses: Dict[int, str] = None  # {func_num: address}
    max_func_address: Optional[str] = None
    max_func_num: Optional[int] = None
    
    # 行号信息
    start_line_number: Optional[int] = None
    end_line_number: Optional[int] = None
    
    # 解析结果
    parameter_name: Optional[str] = None
    function_name: Optional[str] = None
    restart_reason: Optional[str] = None
    
    def __post_init__(self):
        if self.func_addresses is None:
            self.func_addresses = {}

@dataclass 
class MapSymbol:
    """Map文件符号信息"""
    address: str
    name: str
    section: str = ""
    file: str = ""

class MapFileParser:
    """Map文件解析器"""
    
    def __init__(self, map_file_path: str):
        self.map_file_path = map_file_path
        self.symbols = {}  # {address: MapSymbol}
        self.functions = {}  # {address: function_name}
        self.variables = {}  # {address: variable_name}
        self.logger = logging.getLogger(__name__)
        
        # 智能缓存系统
        self._lookup_cache = {}  # {address: symbol_name}
        self._range_cache = {}   # {address: closest_symbol}
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'range_hits': 0,
            'range_misses': 0
        }
        self._cache_max_size = 10000  # 最大缓存条目数
        
        if os.path.exists(map_file_path):
            self._parse_map_file()
    
    def _cleanup_cache(self):
        """清理缓存，保持内存使用合理"""
        if len(self._lookup_cache) > self._cache_max_size:
            # 简单的LRU策略：删除最旧的20%条目
            items_to_remove = int(self._cache_max_size * 0.2)
            keys_to_remove = list(self._lookup_cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self._lookup_cache[key]
            self.logger.debug(f"清理了 {items_to_remove} 个缓存条目")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = (self._cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self._lookup_cache),
            'range_cache_size': len(self._range_cache),
            'hits': self._cache_stats['hits'],
            'misses': self._cache_stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'range_hits': self._cache_stats['range_hits'],
            'range_misses': self._cache_stats['range_misses']
        }
    
    def _parse_map_file(self):
        """解析map文件，提取符号表"""
        self.logger.info(f"开始解析map文件: {self.map_file_path}")
        
        try:
            with open(self.map_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 检查文件大小，决定是否使用并行处理
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > 1.0:  # 大于1MB的文件使用并行处理
                self.logger.info(f"文件大小: {file_size_mb:.1f}MB，使用并行解析")
                self._parse_tasking_map_parallel(content)
            else:
                self.logger.info(f"文件大小: {file_size_mb:.1f}MB，使用串行解析")
                self._parse_tasking_map(content)
            
        except Exception as e:
            self.logger.error(f"解析map文件失败: {e}")
    
    def _parse_tasking_map_parallel(self, content: str):
        """并行解析TASKING格式的map文件"""
        self.logger.info(f"开始并行解析TASKING格式map文件")
        
        lines = content.split('\n')
        total_lines = len(lines)
        
        # 根据CPU核心数确定线程数
        import multiprocessing
        max_workers = min(multiprocessing.cpu_count(), 4)  # 最多4个线程
        
        # 将数据分块
        chunk_size = total_lines // max_workers
        chunks = []
        for i in range(max_workers):
            start = i * chunk_size
            end = start + chunk_size if i < max_workers - 1 else total_lines
            chunks.append(lines[start:end])
        
        # 线程安全的字典
        symbols_lock = Lock()
        functions_lock = Lock()
        variables_lock = Lock()
        
        def parse_chunk(chunk_lines):
            """解析数据块"""
            local_symbols = {}
            local_functions = {}
            local_variables = {}
            parsed_count = 0
            
            for line in chunk_lines:
                line = line.strip()
                if not line or not line.startswith('|'):
                    continue
                
                # 分割表格列
                parts = [part.strip() for part in line.split('|')]
                if len(parts) < 3:
                    continue
                
                # 查找地址和符号名
                addr = None
                symbol_name = None
                
                # 检查所有可能的格式
                for i, part in enumerate(parts):
                    part = part.strip()
                    if not part:
                        continue
                    
                    # 检查是否为地址格式
                    if re.match(r'0x[0-9a-fA-F]{8}$', part):
                        addr = part.lower()
                        
                        # 查找符号名（检查前后列）
                        for j in range(i):
                            candidate = parts[j].strip()
                            if (candidate and candidate != '' and not candidate.startswith('0x') 
                                and not candidate.startswith('mpe:') and len(candidate) > 2):
                                if re.match(r'[a-zA-Z_][a-zA-Z0-9_]*', candidate):
                                    symbol_name = candidate
                                    break
                        
                        if not symbol_name:
                            for j in range(i + 1, len(parts)):
                                candidate = parts[j].strip()
                                if (candidate and candidate != '' and not candidate.startswith('0x') 
                                    and not candidate.startswith('mpe:') and len(candidate) > 2):
                                    if re.match(r'[a-zA-Z_][a-zA-Z0-9_]*', candidate):
                                        symbol_name = candidate
                                        break
                        break
                    
                    # 检查是否为符号名格式（反向映射）
                    elif re.match(r'[a-zA-Z_][a-zA-Z0-9_]*$', part) and not part.startswith('mpe:'):
                        symbol_name = part
                        for j in range(i + 1, len(parts)):
                            candidate = parts[j].strip()
                            if re.match(r'0x[0-9a-fA-F]{8}$', candidate):
                                addr = candidate.lower()
                                break
                        break
                
                # 如果找到了地址和符号名，添加到本地映射表
                if addr and symbol_name:
                    local_symbols[addr] = MapSymbol(address=addr, name=symbol_name)
                    
                    if self._is_function_symbol(symbol_name):
                        local_functions[addr] = symbol_name
                    else:
                        local_variables[addr] = symbol_name
                    
                    parsed_count += 1
            
            return local_symbols, local_functions, local_variables, parsed_count
        
        # 使用线程池并行处理
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(parse_chunk, chunk) for chunk in chunks]
            
            total_parsed = 0
            for future in concurrent.futures.as_completed(futures):
                try:
                    local_symbols, local_functions, local_variables, parsed_count = future.result()
                    
                    # 合并结果
                    with symbols_lock:
                        self.symbols.update(local_symbols)
                    with functions_lock:
                        self.functions.update(local_functions)
                    with variables_lock:
                        self.variables.update(local_variables)
                    
                    total_parsed += parsed_count
                    
                except Exception as e:
                    self.logger.error(f"并行解析块失败: {e}")
        
        parse_time = time.time() - start_time
        self.logger.info(f"并行解析完成: 函数 {len(self.functions)} 个, 变量 {len(self.variables)} 个, 符号 {len(self.symbols)} 个 (处理了 {total_parsed} 行，耗时: {parse_time:.2f}秒)")
    
    def _parse_tasking_map(self, content: str):
        """解析TASKING格式的map文件"""
        self.logger.info(f"开始解析TASKING格式map文件")
        
        # 优化：一次遍历解析所有格式
        lines = content.split('\n')
        parsed_count = 0
        
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('|'):
                continue
            
            # 分割表格列
            parts = [part.strip() for part in line.split('|')]
            if len(parts) < 3:
                continue
            
            # 查找地址和符号名
            addr = None
            symbol_name = None
            
            # 检查所有可能的格式
            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                
                # 检查是否为地址格式
                if re.match(r'0x[0-9a-fA-F]{8}$', part):
                    addr = part.lower()
                    
                    # 查找符号名（检查前后列）
                    # 1. 检查前面的列
                    for j in range(i):
                        candidate = parts[j].strip()
                        if (candidate and candidate != '' and not candidate.startswith('0x') 
                            and not candidate.startswith('mpe:') and len(candidate) > 2):
                            if re.match(r'[a-zA-Z_][a-zA-Z0-9_]*', candidate):
                                symbol_name = candidate
                                break
                    
                    # 2. 如果前面没找到，检查后面的列
                    if not symbol_name:
                        for j in range(i + 1, len(parts)):
                            candidate = parts[j].strip()
                            if (candidate and candidate != '' and not candidate.startswith('0x') 
                                and not candidate.startswith('mpe:') and len(candidate) > 2):
                                if re.match(r'[a-zA-Z_][a-zA-Z0-9_]*', candidate):
                                    symbol_name = candidate
                                    break
                    break
                
                # 检查是否为符号名格式（反向映射）
                elif re.match(r'[a-zA-Z_][a-zA-Z0-9_]*$', part) and not part.startswith('mpe:'):
                    symbol_name = part
                    # 查找地址（在符号名后面的列）
                    for j in range(i + 1, len(parts)):
                        candidate = parts[j].strip()
                        if re.match(r'0x[0-9a-fA-F]{8}$', candidate):
                            addr = candidate.lower()
                            break
                    break
            
            # 如果找到了地址和符号名，添加到映射表
            if addr and symbol_name:
                self.symbols[addr] = MapSymbol(address=addr, name=symbol_name)
                
                # 根据命名约定分类函数和变量
                if self._is_function_symbol(symbol_name):
                    self.functions[addr] = symbol_name
                else:
                    self.variables[addr] = symbol_name
                
                parsed_count += 1
        
        self.logger.info(f"解析完成: 函数 {len(self.functions)} 个, 变量 {len(self.variables)} 个, 符号 {len(self.symbols)} 个 (处理了 {parsed_count} 行)")
    
    def _is_function_symbol(self, symbol: str) -> bool:
        """判断是否为函数符号"""
        # 通常函数名不包含点号，变量名可能包含点号
        # 这里用简单的启发式判断
        function_keywords = ['func', 'handler', 'init', 'main', 'process', 'task', 'isr', 'os_']
        symbol_lower = symbol.lower()
        
        # 如果包含函数关键字，可能是函数
        for keyword in function_keywords:
            if keyword in symbol_lower:
                return True
        
        # 如果不包含点号且以大小写字母开头，可能是函数
        if '.' not in symbol and symbol[0].isupper():
            return True
        
        return False
    
    def find_symbol_by_address(self, address: str) -> Optional[str]:
        """根据地址查找符号名"""
        # 标准化地址格式
        if not address.lower().startswith('0x'):
            address = '0x' + address
        addr_key = address.lower()
        
        # 检查缓存
        if addr_key in self._lookup_cache:
            self._cache_stats['hits'] += 1
            return self._lookup_cache[addr_key]
        
        # 1. 精确匹配
        if addr_key in self.symbols:
            result = self.symbols[addr_key].name
            self._lookup_cache[addr_key] = result
            self._cache_stats['hits'] += 1
            return result
        
        # 2. 检查范围匹配缓存
        if addr_key in self._range_cache:
            self._cache_stats['range_hits'] += 1
            return self._range_cache[addr_key]
        
        # 3. 尝试地址范围匹配（查找最接近的符号）
        try:
            target_addr = int(address, 16)
            closest_symbol = None
            min_distance = float('inf')
            
            for addr_str, symbol in self.symbols.items():
                try:
                    symbol_addr = int(symbol.address, 16)
                    distance = abs(target_addr - symbol_addr)
                    
                    # 如果距离在合理范围内（4KB），且比之前找到的更近
                    if distance < min_distance and distance < 0x1000:
                        min_distance = distance
                        closest_symbol = symbol.name
                except (ValueError, AttributeError):
                    continue
            
            if closest_symbol:
                self.logger.debug(f"地址 {address} 未找到精确匹配，使用最接近的符号: {closest_symbol} (距离: {min_distance})")
                self._range_cache[addr_key] = closest_symbol
                self._cache_stats['range_hits'] += 1
                return closest_symbol
                
        except (ValueError, TypeError) as e:
            self.logger.warning(f"地址格式错误 {address}: {e}")
        
        # 缓存未找到的结果
        self._lookup_cache[addr_key] = None
        self._cache_stats['misses'] += 1
        return None
    
    def find_function_by_pattern(self, address: str) -> Optional[str]:
        """根据地址模式查找函数名"""
        # 简化实现：根据地址特征推测可能的函数名
        try:
            addr_int = int(address, 16)
            # 根据地址范围推测可能的模块
            if 0x80000000 <= addr_int <= 0x8FFFFFFF:
                return f"func_at_{address}"
            elif 0x90000000 <= addr_int <= 0x9FFFFFFF:
                return f"interrupt_handler_{address}"
            else:
                return f"unknown_func_{address}"
        except:
            return f"invalid_addr_{address}"
    
    def find_variable_by_pattern(self, address: str) -> Optional[str]:
        """根据地址模式查找变量名"""
        # 简化实现：根据地址特征推测可能的变量名
        try:
            addr_int = int(address, 16)
            # 根据地址范围推测可能的变量类型
            if 0xD0000000 <= addr_int <= 0xDFFFFFFF:
                return f"ram_var_{address}"
            elif 0x80000000 <= addr_int <= 0x8FFFFFFF:
                return f"rom_const_{address}"
            else:
                return f"unknown_var_{address}"
        except:
            return f"invalid_addr_{address}"

class TrapAnalyzer:
    """TRAP重启日志分析器"""
    
    def __init__(self, map_file_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.map_parser = None
        
        # 性能统计
        self.performance_stats = {
            'map_parse_time': 0.0,
            'symbol_lookup_time': 0.0,
            'trap_analysis_time': 0.0,
            'total_traps_found': 0,
            'symbol_resolution_success': 0,
            'symbol_resolution_failed': 0
        }
        
        self.logger.info(f"TrapAnalyzer初始化，map_file_path: {map_file_path}")
        
        if map_file_path and os.path.exists(map_file_path):
            try:
                self.logger.info(f"找到map文件，开始解析: {map_file_path}")
                start_time = time.time()
                self.map_parser = MapFileParser(map_file_path)
                parse_time = time.time() - start_time
                self.performance_stats['map_parse_time'] = parse_time
                self.logger.info(f"Map文件解析完成，耗时: {parse_time:.2f}秒")
            except Exception as e:
                self.logger.error(f"Map文件解析失败: {e}")
                self.map_parser = None
        else:
            self.logger.warning(f"未找到map文件或文件不存在: {map_file_path}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        stats = self.performance_stats.copy()
        
        # 添加缓存统计
        if self.map_parser:
            cache_stats = self.map_parser.get_cache_stats()
            stats['cache_stats'] = cache_stats
        
        return stats
    
    def analyze_trap_logs(self, content: str) -> List[TrapInfo]:
        """分析TRAP重启日志"""
        trap_infos = []
        
        # 将内容按行分割，方便计算行号
        lines = content.split('\n')
        
        # 查找所有TRAP-RST块，每个"Reset Info:"表示一次重启
        reset_info_pattern = config.log_patterns.trap_rst_pattern
        diear_pattern = r'\{TRAP-RST\}:DIEAR:'
        
        reset_info_matches = []
        diear_matches = []
        
        # 找到所有"Reset Info:"和"DIEAR:"的位置和行号
        for match in re.finditer(reset_info_pattern, content):
            # 计算匹配位置对应的行号
            line_number = content[:match.start()].count('\n') + 1
            reset_info_matches.append((match.start(), line_number))
        
        for match in re.finditer(diear_pattern, content):
            # 计算匹配位置对应的行号
            line_number = content[:match.start()].count('\n') + 1
            diear_matches.append((match.start(), line_number))
        
        self.logger.info(f"找到 {len(reset_info_matches)} 次TRAP重启事件")
        
        # 对每个重启事件进行分析
        for i, (start_pos, start_line) in enumerate(reset_info_matches):
            # 找到对应的DIEAR结束位置和行号
            end_pos = None
            end_line = None
            
            for diear_pos, diear_line in diear_matches:
                if diear_pos > start_pos:
                    # 找到当前Reset Info后的第一个DIEAR
                    end_pos = diear_pos + 200  # 包含DIEAR行及其后的少量内容
                    end_line = diear_line
                    break
            
            # 如果没有找到对应的DIEAR，使用下一个Reset Info或文件结尾
            if end_pos is None:
                if i + 1 < len(reset_info_matches):
                    end_pos = reset_info_matches[i + 1][0]
                    end_line = reset_info_matches[i + 1][1] - 1
                else:
                    # 最后一个块，向后找5000个字符或到文件结尾
                    end_pos = min(start_pos + 5000, len(content))
                    end_line = len(lines)
            
            # 提取当前TRAP块的内容
            trap_block = content[start_pos:end_pos]
            
            # 解析当前TRAP块
            trap_info = self._parse_trap_block(trap_block)
            if trap_info:
                # 设置行号信息
                trap_info.start_line_number = start_line
                trap_info.end_line_number = end_line
                
                # 解析符号信息
                self._resolve_symbols(trap_info)
                # 生成重启原因结论
                self._generate_restart_reason(trap_info)
                trap_infos.append(trap_info)
        
        return trap_infos
    
    def _parse_trap_block(self, trap_block: str) -> Optional[TrapInfo]:
        """解析单个TRAP块信息"""
        trap_info = TrapInfo()
        
        # 提取Reset Type
        reset_type_match = re.search(config.log_patterns.trap_reset_type_pattern, trap_block)
        if reset_type_match:
            trap_info.rest_type = reset_type_match.group(1)
        
        # 提取DEADD地址（需要加上0x前缀）
        deadd_match = re.search(config.log_patterns.trap_deadd_pattern, trap_block)
        if deadd_match:
            deadd_addr = deadd_match.group(1)
            # 确保地址以0x开头
            if not deadd_addr.lower().startswith('0x'):
                deadd_addr = '0x' + deadd_addr
            trap_info.deadd_address = deadd_addr
        
        # 提取所有FuncX地址
        func_matches = re.findall(config.log_patterns.trap_func_pattern, trap_block)
        for func_num_str, func_addr in func_matches:
            func_num = int(func_num_str)
            # 确保地址以0x开头
            if not func_addr.lower().startswith('0x'):
                func_addr = '0x' + func_addr
            trap_info.func_addresses[func_num] = func_addr
        
        # 找到数值最大的FuncX
        if trap_info.func_addresses:
            max_func_num = max(trap_info.func_addresses.keys())
            trap_info.max_func_num = max_func_num
            trap_info.max_func_address = trap_info.func_addresses[max_func_num]
        
        # 验证是否解析到关键信息
        if not trap_info.rest_type and not trap_info.deadd_address and not trap_info.func_addresses:
            return None
        
        return trap_info
    
    def _parse_trap_info(self, trap_log: str) -> Optional[TrapInfo]:
        """解析单条TRAP日志信息"""
        trap_info = TrapInfo()
        
        # 提取Rest Type
        rest_type_match = re.search(config.log_patterns.trap_reset_type_pattern, trap_log)
        if rest_type_match:
            trap_info.rest_type = rest_type_match.group(1)
        
        # 提取DEADD地址
        deadd_match = re.search(config.log_patterns.trap_deadd_pattern, trap_log)
        if deadd_match:
            deadd_addr = deadd_match.group(1)
            # 确保地址以0x开头
            if not deadd_addr.lower().startswith('0x'):
                deadd_addr = '0x' + deadd_addr
            trap_info.deadd_address = deadd_addr
        
        # 提取所有FuncX地址
        func_matches = re.findall(config.log_patterns.trap_func_pattern, trap_log)
        for func_num_str, func_addr in func_matches:
            func_num = int(func_num_str)
            # 确保地址以0x开头
            if not func_addr.lower().startswith('0x'):
                func_addr = '0x' + func_addr
            trap_info.func_addresses[func_num] = func_addr
        
        # 找到数值最大的FuncX
        if trap_info.func_addresses:
            max_func_num = max(trap_info.func_addresses.keys())
            trap_info.max_func_num = max_func_num
            trap_info.max_func_address = trap_info.func_addresses[max_func_num]
        
        # 验证是否解析到关键信息
        if not trap_info.rest_type and not trap_info.deadd_address and not trap_info.func_addresses:
            return None
        
        return trap_info
    
    def _resolve_symbols(self, trap_info: TrapInfo):
        """解析符号信息"""
        if not self.map_parser:
            # 如果没有map文件，使用地址模式匹配
            if trap_info.deadd_address:
                trap_info.parameter_name = f"param_at_{trap_info.deadd_address}"
                self.logger.warning(f"未提供map文件，使用默认参数名: {trap_info.parameter_name}")
            if trap_info.max_func_address:
                trap_info.function_name = f"func_at_{trap_info.max_func_address}"
                self.logger.warning(f"未提供map文件，使用默认函数名: {trap_info.function_name}")
            return
        
        # 根据DEADD地址查找参数名
        if trap_info.deadd_address:
            param_name = self.map_parser.find_symbol_by_address(trap_info.deadd_address)
            if param_name:
                trap_info.parameter_name = param_name
                self.logger.info(f"找到参数名: {param_name} (地址: {trap_info.deadd_address})")
            else:
                trap_info.parameter_name = self.map_parser.find_variable_by_pattern(trap_info.deadd_address)
                self.logger.warning(f"未找到参数名，使用模式匹配: {trap_info.parameter_name} (地址: {trap_info.deadd_address})")
        
        # 根据最大FuncX地址查找函数名
        if trap_info.max_func_address:
            func_name = self.map_parser.find_symbol_by_address(trap_info.max_func_address)
            if func_name:
                trap_info.function_name = func_name
                self.logger.info(f"找到函数名: {func_name} (地址: {trap_info.max_func_address})")
            else:
                trap_info.function_name = self.map_parser.find_function_by_pattern(trap_info.max_func_address)
                self.logger.warning(f"未找到函数名，使用模式匹配: {trap_info.function_name} (地址: {trap_info.max_func_address})")
    
    def _generate_restart_reason(self, trap_info: TrapInfo):
        """生成重启原因结论"""
        # 使用新的格式：重启原因：【函数名】访问【参数名】异常进入Trap
        function_name = trap_info.function_name or "未知函数"
        parameter_name = trap_info.parameter_name or "未知参数"
        
        # 生成格式化的重启原因
        if trap_info.function_name and trap_info.parameter_name:
            trap_info.restart_reason = f"重启原因：【{function_name}】访问【{parameter_name}】异常进入Trap"
        elif trap_info.function_name:
            trap_info.restart_reason = f"重启原因：【{function_name}】访问内存异常进入Trap"
        elif trap_info.parameter_name:
            trap_info.restart_reason = f"重启原因：未知函数访问【{parameter_name}】异常进入Trap"
        else:
            # fallback到原有格式
            reason_parts = []
            if trap_info.rest_type:
                reason_parts.append(f"重启类型: {trap_info.rest_type}")
            if trap_info.deadd_address or trap_info.max_func_address:
                reason_parts.append("异常进入TRAP")
            trap_info.restart_reason = " ".join(reason_parts) if reason_parts else "未知重启原因"

# 全局TRAP分析器实例
trap_analyzer = TrapAnalyzer()