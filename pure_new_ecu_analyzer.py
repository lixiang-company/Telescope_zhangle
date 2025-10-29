#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECU日志分析系统 - 纯新版架构入口程序
使用 src/ecu_log_analyzer 纯新版模块

版本: 2.0.0
作者: ECU Log Analyzer Team
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import time

# 确保能够找到src模块
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    # 使用延迟导入方式避免循环引用
    import ecu_log_analyzer
    
    # 获取类
    Config = ecu_log_analyzer.get_config()
    LogParser = ecu_log_analyzer.get_log_parser()
    ParsedData = ecu_log_analyzer.get_parsed_data()
    ReportGenerator = ecu_log_analyzer.get_report_generator()
    
except ImportError as e:
    print(f"错误: 无法导入必要的模块 - {e}")
    print("请确保所有依赖文件都在正确的位置")
    import traceback
    traceback.print_exc()
    sys.exit(1)

class PureNewECUAnalyzer:
    """ECU日志分析器主类 - 纯新版架构"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.version = "2.0.0 (Pure New)"
        self.config = Config()
        
        # 延迟初始化parser，map文件路径将在分析时确定
        self.parser = None
        self.report_generator = ReportGenerator(self.config)
    
    def _setup_logging(self):
        """设置日志记录"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def _find_map_file_for_log(self, log_file_path: str) -> Optional[str]:
        """根据log文件路径查找同目录下的map文件"""
        start_time = time.time()
        
        # 获取log文件所在目录
        log_dir = os.path.dirname(os.path.abspath(log_file_path))
        self.logger.info(f"在log文件目录中查找map文件: {log_dir}")
        
        # 搜索策略：优先在同目录下查找
        search_strategies = [
            # 策略1: log文件同目录
            lambda: self._search_in_directory(log_dir),
            # 策略2: log文件同目录的子目录
            lambda: self._search_in_subdirectories(log_dir),
            # 策略3: 当前工作目录
            lambda: self._search_in_directory("."),
            # 策略4: 常见项目目录
            self._search_common_directories,
            # 策略5: 递归搜索（最后使用）
            lambda: self._search_recursive_from_dir(log_dir)
        ]
        
        checked_paths = []
        for strategy in search_strategies:
            try:
                result = strategy()
                if result:
                    find_time = time.time() - start_time
                    self.logger.info(f"✅ 找到map文件: {result} (检查了 {len(checked_paths)} 个路径，耗时: {find_time:.3f}秒)")
                    return result
                if isinstance(result, list):
                    checked_paths.extend(result)
            except Exception as e:
                self.logger.debug(f"搜索策略失败: {e}")
                continue
        
        find_time = time.time() - start_time
        self.logger.warning(f"⚠️ 未找到map文件 (检查了 {len(checked_paths)} 个路径，耗时: {find_time:.3f}秒)")
        return None
    
    def _search_in_directory(self, directory: str) -> Optional[str]:
        """在指定目录中查找map文件"""
        map_file_path = os.path.join(directory, "BZCU_VecorARCode.map")
        if os.path.exists(map_file_path):
            return map_file_path
        return None
    
    def _search_in_subdirectories(self, parent_dir: str) -> Optional[str]:
        """在指定目录的子目录中查找map文件"""
        if not os.path.exists(parent_dir):
            return None
            
        # 常见的子目录名称
        subdirs = ["map", "maps", "symbols", "debug", "build", "output", "bin"]
        
        for subdir in subdirs:
            subdir_path = os.path.join(parent_dir, subdir)
            if os.path.exists(subdir_path) and os.path.isdir(subdir_path):
                map_file_path = os.path.join(subdir_path, "BZCU_VecorARCode.map")
                if os.path.exists(map_file_path):
                    return map_file_path
        return None
    
    def _search_common_directories(self) -> List[str]:
        """搜索常见项目目录"""
        common_paths = [
            "./data/sample_logs/BZCU_VecorARCode.map",
            "./ecu_info_check/BZCU_VecorARCode.map",
            "../BZCU_VecorARCode.map",
            "../../BZCU_VecorARCode.map",
            "../data/sample_logs/BZCU_VecorARCode.map",
            "../../data/sample_logs/BZCU_VecorARCode.map",
            "../ecu_info_check/BZCU_VecorARCode.map"
        ]
        
        checked = []
        for path in common_paths:
            checked.append(path)
            if os.path.exists(path):
                return path
        return checked
    
    def _search_recursive_from_dir(self, start_dir: str) -> Optional[str]:
        """从指定目录开始递归搜索（仅在必要时使用）"""
        # 限制搜索深度和范围，避免性能问题
        max_depth = 2
        max_files_to_check = 1000
        files_checked = 0
        
        for root, dirs, files in os.walk(start_dir):
            # 限制搜索深度
            depth = root.count(os.sep) - start_dir.count(os.sep)
            if depth > max_depth:
                continue
            
            for file in files:
                files_checked += 1
                if files_checked > max_files_to_check:
                    self.logger.debug(f"达到最大文件检查数量限制: {max_files_to_check}")
                    return None
                    
                if file == "BZCU_VecorARCode.map":
                    full_path = os.path.join(root, file)
                    self.logger.info(f"递归搜索找到map文件: {full_path}")
                    return full_path
        return None
    
    def _get_parser_with_map(self, log_file_path: str) -> LogParser:
        """获取带有map文件的LogParser实例"""
        if self.parser is None:
            # 根据log文件路径查找map文件
            map_file_path = self._find_map_file_for_log(log_file_path)
            if map_file_path:
                self.logger.info(f"使用map文件: {map_file_path}")
            else:
                self.logger.warning("未找到map文件，TRAP分析将使用默认符号名")
            
            self.parser = LogParser(self.config, map_file_path)
        
        return self.parser
    
    def print_banner(self):
        """打印程序横幅"""
        banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ECU日志分析系统 - 纯新版架构                           ║
║                         版本: {self.version}                                    ║
║                                                                              ║
║  架构特点:                                                                    ║
║    • 使用全新的src/ecu_log_analyzer代码库                                     ║
║    • 模块化设计，延迟导入避免循环依赖                                         ║
║    • 集成ECharts静态文件自动复制功能                                         ║
║    • 支持完整的折线图显示                                                    ║
║    • 优化的配置管理和性能监控                                                ║
║                                                                              ║
║  功能特性:                                                                    ║
║    • ECU日志文件解析 (新版解析器)                                             ║
║    • CPU核负载率数据提取                                                     ║
║    • TRAP重启信息分析                                                        ║
║    • SOA数据分析                                                             ║
║    • HTML报告生成 (新版模板引擎)                                             ║
║    • 数据可视化图表                                                          ║
║                                                                              ║
║  支持格式: .log 文件                                                         ║
║  输出格式: HTML报告、JSON数据                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def analyze_file(self, file_path: str, verbose: bool = False) -> bool:
        """
        分析单个日志文件
        
        Args:
            file_path: 日志文件路径
            verbose: 是否显示详细信息
            
        Returns:
            bool: 分析是否成功
        """
        if verbose:
            self.print_banner()
        
        self.logger.info(f"开始分析文件: {file_path}")
        
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return False
        
        try:
            # 获取带有map文件的parser实例
            parser_with_map = self._get_parser_with_map(file_path)
            
            # 解析文件
            parsed_data = parser_with_map.parse_file(file_path)
            if not parsed_data:
                self.logger.error("文件解析失败")
                return False
            
            # 分析数据
            analysis_result = self.report_generator.analyze_data([parsed_data])
            
            # 生成报告
            self._generate_reports([parsed_data], analysis_result)
            
            # 显示结果
            self._display_file_analysis_result(analysis_result, verbose)
            
            return True
            
        except Exception as e:
            self.logger.error(f"分析文件失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def analyze_directory(self, directory: str, verbose: bool = False) -> bool:
        """
        分析目录中的日志文件
        
        Args:
            directory: 目录路径
            verbose: 是否显示详细信息
            
        Returns:
            bool: 分析是否成功
        """
        if verbose:
            self.print_banner()
        
        self.logger.info(f"开始分析目录: {directory}")
        
        if not os.path.exists(directory) or not os.path.isdir(directory):
            self.logger.error(f"目录不存在或不是有效目录: {directory}")
            return False
        
        try:
            # 查找目录中的日志文件
            log_files = []
            for file in os.listdir(directory):
                ext = os.path.splitext(file)[1].lower()
                if file.endswith(('.log', '.txt', '.out')) or ext == '':
                    log_files.append(os.path.join(directory, file))
            
            if not log_files:
                self.logger.error("目录中未找到可解析的日志文件")
                return False
            
            self.logger.info(f"找到 {len(log_files)} 个日志文件")
            
            # 解析每个日志文件，为每个文件查找对应的map文件
            parsed_data_list = []
            for log_file_path in log_files:
                try:
                    # 为每个log文件获取对应的parser（包含map文件）
                    parser_with_map = self._get_parser_with_map(log_file_path)
                    parsed_data = parser_with_map.parse_file(log_file_path)
                    if parsed_data:
                        parsed_data_list.append(parsed_data)
                        self.logger.info(f"成功解析文件: {os.path.basename(log_file_path)}")
                    else:
                        self.logger.warning(f"文件解析失败: {os.path.basename(log_file_path)}")
                except Exception as e:
                    self.logger.error(f"解析文件失败 {log_file_path}: {e}")
                    continue
            
            if not parsed_data_list:
                self.logger.error("目录中未找到可解析的日志文件")
                return False
            
            # 分析数据
            analysis_result = self.report_generator.analyze_data(parsed_data_list)
            
            # 生成报告
            self._generate_reports(parsed_data_list, analysis_result)
            
            # 显示结果
            self._display_directory_analysis_result(analysis_result, verbose)
            
            return True
            
        except Exception as e:
            self.logger.error(f"分析目录失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_reports(self, parsed_data_list, analysis_result) -> None:
        """生成分析报告"""
        try:
            # 生成HTML报告
            main_report_path = self.report_generator.generate_html_report(parsed_data_list, analysis_result)
            
            if main_report_path:
                self.logger.info("HTML报告生成完成")
                print(f"\n✅ 报告生成成功!")
                print(f"📊 主报告: {main_report_path}")
                
                # 检查ECharts文件是否已复制
                timestamp_dir = os.path.dirname(main_report_path)
                echarts_path = os.path.join(timestamp_dir, 'static', 'echarts.min.js')
                if os.path.exists(echarts_path):
                    file_size = os.path.getsize(echarts_path) / 1024 / 1024  # MB
                    print(f"✅ ECharts库已复制: {file_size:.1f}MB")
                else:
                    print(f"⚠️  警告: ECharts库未找到，图表可能无法显示")
            else:
                self.logger.error("HTML报告生成失败")
            
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_file_analysis_result(self, result, verbose: bool) -> None:
        """显示单个文件分析结果"""
        if verbose:
            print(f"\n✓ 文件分析完成")
            print(f"  项目: {result.projects[0] if result.projects else '未知'}")
            print(f"  版本: {result.baseline_versions[0] if result.baseline_versions else '未知'}")
            print(f"  CPU核心数: {result.core_count}")
            if result.avg_loads:
                print(f"  平均核负载率:")
                for i, load in enumerate(result.avg_loads):
                    status = "✅ 正常" if load < 70 else "⚡ 中等" if load < 90 else "⚠️ 高负载"
                    print(f"    Core{i}:  {load:.2f}% {status}")
            print(f"  TRAP重启: {result.trap_count} 次")
            if hasattr(result, 'soa_topic_count'):
                print(f"  SOA Topics: {result.soa_topic_count} 个")
            if hasattr(result, 'soa_data_points'):
                print(f"  SOA数据点: {result.soa_data_points} 个")
    
    def _display_directory_analysis_result(self, result, verbose: bool) -> None:
        """显示目录分析结果"""
        if verbose:
            print(f"\n✓ 目录分析完成")
            print(f"  总文件数: {result.total_files}")
            print(f"  有效文件数: {result.valid_files}")
            print(f"  发现项目: {', '.join(result.projects) if result.projects else '未知'}")
            print(f"  基线版本: {', '.join(result.baseline_versions)}")
            print(f"  CPU核心数: {result.core_count}")
            if result.avg_loads:
                print(f"  CPU核平均负载:")
                for i, load in enumerate(result.avg_loads):
                    status = "✅ 正常" if load < 70 else "⚡ 中等" if load < 90 else "⚠️ 高负载"
                    print(f"    Core{i}: {load:.2f}% {status}")
            print(f"  TRAP重启事件: {result.trap_count} 次")
            if hasattr(result, 'soa_topic_count'):
                print(f"  SOA数据分析: {result.soa_topic_count} 个Topic")
            if hasattr(result, 'soa_data_points'):
                print(f"  SOA数据点: {result.soa_data_points} 个")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ECU日志分析系统 - 纯新版架构",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python pure_new_ecu_analyzer.py -f log_file.log              # 分析单个文件
  python pure_new_ecu_analyzer.py -d /path/to/logs/           # 分析目录
  python pure_new_ecu_analyzer.py -d /path/to/logs/ -v        # 详细模式
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', 
                      help='分析单个日志文件')
    group.add_argument('-d', '--directory', 
                      help='分析目录中的所有日志文件')
    
    parser.add_argument('-v', '--verbose', 
                       action='store_true',
                       help='显示详细信息')
    
    args = parser.parse_args()
    
    # 创建分析器实例
    analyzer = PureNewECUAnalyzer()
    
    # 执行分析
    success = False
    try:
        if args.file:
            success = analyzer.analyze_file(args.file, args.verbose)
        elif args.directory:
            success = analyzer.analyze_directory(args.directory, args.verbose)
        
        if success:
            print(f"\n✅ 分析完成！")
            print(f"💡 在浏览器中打开生成的HTML报告查看详细结果")
            print(f"📈 使用纯新版架构，所有图表功能完整支持")
        else:
            print(f"\n❌ 分析失败！")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()