# -*- coding: utf-8 -*-
"""
HTML模板管理器
负责加载和渲染HTML模板
"""

import os
import json
from typing import Dict, Any, List
from dataclasses import dataclass
import logging

@dataclass
class TemplateData:
    """模板数据结构"""
    title: str = ""
    page_title: str = ""
    subtitle: str = ""
    nav_tabs: str = ""
    content: str = ""
    chart_scripts: str = ""

class TemplateManager:
    """HTML模板管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 使用绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_dir = os.path.join(current_dir, '..', '..', '..', 'resources', 'static', 'templates')
        self.template_dir = os.path.abspath(self.template_dir)
        self.logger.info(f"模板管理器初始化，模板目录: {self.template_dir}")
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """加载所有模板文件"""
        try:
            # 加载基础模板
            base_path = os.path.join(self.template_dir, 'base.html')
            self.logger.info(f"尝试加载基础模板: {base_path}")
            with open(base_path, 'r', encoding='utf-8') as f:
                self.templates['base'] = f.read()
            
            # 加载主页面模板
            main_path = os.path.join(self.template_dir, 'main_page.html')
            self.logger.info(f"尝试加载主页面模板: {main_path}")
            with open(main_path, 'r', encoding='utf-8') as f:
                self.templates['main_page'] = f.read()
            
            # 加载SOA页面模板
            soa_path = os.path.join(self.template_dir, 'soa_page.html')
            self.logger.info(f"尝试加载SOA页面模板: {soa_path}")
            with open(soa_path, 'r', encoding='utf-8') as f:
                self.templates['soa_page'] = f.read()
            
            self.logger.info(f"成功加载 {len(self.templates)} 个模板文件")
            
        except Exception as e:
            self.logger.error(f"加载模板文件失败: {e}")
            self.logger.error(f"模板目录: {self.template_dir}")
            # 如果模板加载失败，使用默认模板
            self._create_default_templates()
    
    def _create_default_templates(self):
        """创建默认模板（在模板文件不存在时使用）"""
        self.templates['base'] = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <!-- 引入ECharts -->
    <script src="static/echarts.min.js"></script>
    <link rel="stylesheet" href="static/main.css">
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar">
        <div class="nav-container">
            <div class="nav-brand">
                <span class="nav-logo">🔍</span>
                <span class="nav-title">ECU日志分析系统</span>
            </div>
            <div class="nav-menu">
                <a href="analysis_report_{timestamp}.html" class="nav-link" id="nav-ecu">
                    <span class="nav-icon">📊</span>
                    ECU分析报告
                </a>
                <a href="soa_analysis_{timestamp}.html" class="nav-link" id="nav-soa">
                    <span class="nav-icon">📡</span>
                    SOA分析报告
                </a>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="header">
            <h1>{page_title}</h1>
            <div class="subtitle">{subtitle}</div>
            <div class="nav-tabs">{nav_tabs}</div>
        </div>
        <div class="content">{content}</div>
    </div>
    <script>{chart_scripts}</script>
</body>
</html>
'''
        self.templates['main_page'] = '''<!-- 分析概览 -->
<div class="section">
    <div class="section-header">
        <div class="section-icon">📊</div>
        <h2>分析概览</h2>
    </div>
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{total_files}</div>
            <div class="stat-label">总文件数</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{valid_files}</div>
            <div class="stat-label">有效文件数</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{project_count}</div>
            <div class="stat-label">项目数量</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{core_count}</div>
            <div class="stat-label">CPU核心数</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{trap_count}</div>
            <div class="stat-label">TRAP重启数</div>
        </div>
    </div>
</div>

<!-- 项目信息 -->
<div class="section">
    <div class="section-header">
        <div class="section-icon">📋</div>
        <h2>项目信息</h2>
    </div>
    <div class="project-info-grid">
        <div class="info-card">
            <h4>检测到的项目</h4>
            <div class="project-list">{projects_list}</div>
        </div>
        <div class="info-card">
            <h4>基线版本</h4>
            <div class="version-list">{versions_list}</div>
        </div>
    </div>
</div>

<!-- 数据可视化分析 -->
<div class="section charts-section">
    <div class="section-header">
        <div class="section-icon">📈</div>
        <h2>CPU负载率分析</h2>
    </div>
    
    <!-- 核负载率统计图表 -->
    <div class="chart-wrapper">
        <h3>CPU核心负载率统计</h3>
        <div id="coreLoadsChart" class="chart-container"></div>
    </div>
    
    <!-- 项目对比图表 -->
    <div class="chart-wrapper">
        <h3>项目负载率对比</h3>
        <div id="comparisonChart" class="chart-container"></div>
    </div>
    
    <!-- 趋势分析图表 -->
    <div class="chart-wrapper">
        <h3>CPU负载率趋势分析</h3>
        <div id="trendChart" class="chart-container"></div>
    </div>
    
    <!-- TRAP重启图表 -->
    <div class="chart-wrapper">
        <h3>TRAP重启事件分析</h3>
        <div id="trapRestartChart" class="chart-container"></div>
    </div>
</div>

<!-- 核负载率统计表格 -->
<div class="section">
    <div class="section-header">
        <div class="section-icon">📊</div>
        <h2>CPU核心负载率统计</h2>
    </div>
    <div class="table-container">
        <table class="data-table">
            <thead>
                <tr>
                    <th>核心编号</th>
                    <th>平均负载率(%)</th>
                    <th>最大负载率(%)</th>
                    <th>最小负载率(%)</th>
                    <th>负载状态</th>
                </tr>
            </thead>
            <tbody id="loadStatsTableBody">
                {load_stats_rows}
            </tbody>
        </table>
    </div>
</div>

<!-- TRAP重启信息 -->
<div class="section">
    <div class="section-header">
        <div class="section-icon">⚠️</div>
        <h2>TRAP重启事件信息</h2>
    </div>
    <div class="trap-info-container">
        <div class="trap-summary">
            <p><strong>TRAP重启次数:</strong> <span id="trapCountDisplay">{trap_count}</span></p>
            <p><strong>重启类型:</strong> <span id="trapTypesDisplay">{trap_types_text}</span></p>
            <p><strong>涉及函数:</strong> <span id="trapFunctionsDisplay">{trap_functions_text}</span></p>
        </div>
        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>序号</th>
                        <th>重启类型</th>
                        <th>DEADD地址</th>
                        <th>函数地址</th>
                        <th>参数名</th>
                        <th>函数名</th>
                        <th>重启原因</th>
                    </tr>
                </thead>
                <tbody id="trapInfoTableBody">
                    {trap_info_rows}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- 文件详情表格 -->
<div class="section">
    <div class="section-header">
        <div class="section-icon">📁</div>
        <h2>文件详情</h2>
    </div>
    <div class="table-container">
        <table class="data-table">
            <thead>
                <tr>
                    <th>序号</th>
                    <th>文件名</th>
                    <th>项目名称</th>
                    <th>基线版本</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody id="fileDetailsTableBody">
                {file_details_rows}
            </tbody>
        </table>
    </div>
</div>
'''
        self.templates['soa_page'] = '''<!-- SOA分析概览 -->
<div class="section">
    <div class="section-header">
        <div class="section-icon">📡</div>
        <h2>SOA数据分析概览</h2>
    </div>
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number" id="topicCount">{soa_topic_count}</div>
            <div class="stat-label">Topic总数</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="dataPoints">{soa_data_points}</div>
            <div class="stat-label">数据点数</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="fileCount">{soa_file_count}</div>
            <div class="stat-label">包含SOA数据文件数</div>
        </div>
    </div>
</div>

<!-- SOA Topic图表分析 -->
<div class="section">
    <div class="section-header">
        <div class="section-icon">📈</div>
        <h2>SOA Topic数据分析</h2>
    </div>
    
    <!-- Topic选择器 -->
    <div class="topic-selector">
        <label for="topicSelect">选择Topic:</label>
        <select id="topicSelect" class="topic-select">
            <option value="">请选择Topic</option>
        </select>
    </div>
    
    <!-- Topic信息显示 -->
    <div id="topicInfo" class="topic-info">
        <p>请选择一个Topic查看详细信息</p>
    </div>
    
    <!-- Topic图表容器 -->
    <div class="chart-wrapper">
        <h3 id="selectedTopicTitle">SOA Topic数据分析</h3>
        <div id="soaTopicChart" class="chart-container">
            <div class="loading">请选择Topic查看图表</div>
        </div>
    </div>
</div>

<!-- SOA汇总统计图表 -->
<div class="section">
    <div class="section-header">
        <div class="section-icon">📊</div>
        <h2>SOA数据汇总分析</h2>
    </div>
    <div class="chart-wrapper">
        <h3>SOA汇总统计图表</h3>
        <div id="soaSummaryChart" class="chart-container"></div>
    </div>
</div>

<!-- SOA汇总统计表格 -->
<div class="section">
    <div class="section-header">
        <div class="section-icon">📋</div>
        <h2>SOA汇总统计信息</h2>
    </div>
    <div class="table-container">
        <table class="data-table" id="soaSummaryTable">
            <thead>
                <tr>
                    <th>统计项目</th>
                    <th>数值</th>
                    <th>说明</th>
                </tr>
            </thead>
            <tbody id="soaSummaryTableBody">
                <!-- 汇总统计信息将通过JavaScript动态填充 -->
            </tbody>
        </table>
    </div>
</div>

<!-- Topic详细统计信息 -->
<div class="section">
    <div class="section-header">
        <div class="section-icon">📝</div>
        <h2>Topic详细统计信息</h2>
    </div>
    <div class="table-container">
        <table class="data-table" id="soaTopicDetailTable">
            <thead>
                <tr>
                    <th>序号</th>
                    <th>Topic名称</th>
                    <th>发送总包数</th>
                    <th>接收总包数</th>
                    <th>丢失总包数</th>
                    <th>数据状态</th>
                    <th>详细信息</th>
                </tr>
            </thead>
            <tbody id="soaTopicDetailTableBody">
                <!-- Topic详细统计信息将通过JavaScript动态填充 -->
            </tbody>
        </table>
    </div>
</div>

<!-- SOA详细日志信息 -->
<div class="section">
    <div class="section-header">
        <div class="section-icon">📄</div>
        <h2>SOA详细日志信息</h2>
    </div>
    <div class="table-container">
        <table class="data-table" id="soaLogDetailTable">
            <thead>
                <tr>
                    <th>序号</th>
                    <th>文件名</th>
                    <th>行号</th>
                    <th>原始日志</th>
                    <th>数据类型</th>
                </tr>
            </thead>
            <tbody id="soaLogDetailTableBody">
                <!-- SOA详细日志信息将通过JavaScript动态填充 -->
            </tbody>
        </table>
    </div>
</div>

<!-- 错误显示区域 -->
<div id="soaError" class="error-container" style="display: none;">
    <!-- 错误信息将在这里显示 -->
</div>
'''
    
    def generate_nav_tabs(self, current_page: str = "main", timestamp: str = "") -> str:
        """生成导航标签（已废弃，返回空字符串）"""
        return ""
    
    def render_main_page(self, data: Dict[str, Any], timestamp: str = "") -> str:
        """渲染主页面"""
        try:
            # 准备模板数据
            template_data = TemplateData(
                title="ECU日志分析报告",
                page_title="ECU日志分析报告",
                subtitle=data.get('subtitle', ''),
                nav_tabs=self.generate_nav_tabs("main", timestamp)
            )
            
            # 渲染主页面内容，处理所有占位符
            # 确保所有必需的占位符都有默认值
            default_data = {
                'total_files': 0,
                'valid_files': 0,
                'project_count': 0,
                'core_count': 0,
                'trap_count': 0,
                'projects_list': '未知',
                'versions_list': '未知',
                'load_stats_rows': '<tr><td colspan="5">暂无数据</td></tr>',
                'trap_types_text': '未知',
                'trap_functions_text': '未知',
                'trap_info_rows': '<tr><td colspan="7">暂无TRAP信息</td></tr>',
                'file_details_rows': '<tr><td colspan="5">暂无文件信息</td></tr>',
                'chart_scripts': ''
            }
            # 合并默认数据和传入数据
            merged_data = {**default_data, **data}
            main_content = self.templates['main_page'].format(**merged_data)
            template_data.content = main_content
            
            # 使用报告生成器传递的图表脚本，如果没有则使用默认的
            if data.get('chart_scripts'):
                template_data.chart_scripts = data['chart_scripts']
            else:
                # 生成简化的JSON数据加载脚本作为备用
                chart_scripts = """
                // ECU数据加载和图表初始化脚本
                document.addEventListener('DOMContentLoaded', function() {
                    console.log('页面加载完成，开始加载ECU数据...');
                    
                    const ecuDataPath = 'ecu_data_""" + timestamp + """.json';
                    console.log('尝试加载ECU数据文件:', ecuDataPath);
                    
                    // 使用fetch加载JSON文件
                    fetch(ecuDataPath)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('HTTP ' + response.status + ': ' + response.statusText);
                            }
                            console.log('ECU数据文件加载成功，开始解析...');
                            return response.json();
                        })
                        .then(data => {
                            console.log('ECU数据解析成功:', data);
                            initializeCharts(data);
                        })
                        .catch(error => {
                            console.error('加载ECU数据失败:', error);
                            showError('加载ECU数据失败: ' + error.message);
                        });
                    
                    // 显示错误信息
                    function showError(message) {
                        console.error(message);
                        document.querySelectorAll('.chart-container').forEach(container => {
                            container.innerHTML = '<div class="error-message">' + message + '</div>';
                        });
                    }
                    
                    // 初始化图表
                    function initializeCharts(data) {
                        try {
                            // 初始化核负载率图表
                            if (data.charts && data.charts.coreLoads && Object.keys(data.charts.coreLoads).length > 0) {
                                const chart1 = echarts.init(document.getElementById('coreLoadsChart'));
                                chart1.setOption(data.charts.coreLoads);
                                window.addEventListener('resize', () => chart1.resize());
                                console.log('核负载率图表初始化成功');
                            } else {
                                document.getElementById('coreLoadsChart').innerHTML = '<div class="loading">暂无核负载率数据</div>';
                                console.log('核负载率图表: 无数据');
                            }
                            
                            // 初始化对比图表
                            if (data.charts && data.charts.comparison && Object.keys(data.charts.comparison).length > 0) {
                                const chart2 = echarts.init(document.getElementById('comparisonChart'));
                                chart2.setOption(data.charts.coreLoads);
                                window.addEventListener('resize', () => chart2.resize());
                                console.log('对比图表初始化成功');
                            } else {
                                document.getElementById('comparisonChart').innerHTML = '<div class="loading">暂无对比数据</div>';
                                console.log('对比图表: 无数据');
                            }
                            
                            // 初始化趋势图表
                            if (data.charts && data.charts.trend && Object.keys(data.charts.trend).length > 0) {
                                const chart3 = echarts.init(document.getElementById('trendChart'));
                                chart3.setOption(data.charts.trend);
                                window.addEventListener('resize', () => chart3.resize());
                                console.log('趋势图表初始化成功');
                            } else {
                                document.getElementById('trendChart').innerHTML = '<div class="loading">暂无趋势数据</div>';
                                console.log('趋势图表: 无数据');
                            }
                            
                            // 初始化TRAP重启图表
                            if (data.charts && data.charts.trapRestart && Object.keys(data.charts.trapRestart).length > 0) {
                                const chart4 = echarts.init(document.getElementById('trapRestartChart'));
                                chart4.setOption(data.charts.trapRestart);
                                window.addEventListener('resize', () => chart4.resize());
                                console.log('TRAP重启图表初始化成功');
                            } else {
                                document.getElementById('trapRestartChart').innerHTML = '<div class="loading">暂无TRAP重启数据</div>';
                                console.log('TRAP重启图表: 无数据');
                            }
                            
                            console.log('所有图表初始化完成');
                            
                        } catch (error) {
                            console.error('图表初始化失败:', error);
                            showError('图表初始化失败: ' + error.message);
                        }
                    }
                };
                """
                template_data.chart_scripts = chart_scripts
            
            # 渲染最终HTML
            return self.templates['base'].format(
                title=template_data.title,
                page_title=template_data.page_title,
                subtitle=template_data.subtitle,
                nav_tabs=template_data.nav_tabs,
                content=template_data.content,
                chart_scripts=template_data.chart_scripts,
                timestamp=timestamp,
                project_name=data.get('project_name', '未知项目'),
                baseline_version=data.get('baseline_version', '未知版本')
            )
            
        except Exception as e:
            self.logger.error(f"渲染主页面失败: {e}")
            return f"<h1>页面渲染失败</h1><p>错误信息: {e}</p>"
    
    def render_soa_page(self, data: Dict[str, Any], timestamp: str = "") -> str:
        """渲染SOA页面"""
        try:
            # 准备模板数据
            template_data = TemplateData(
                title="SOA数据分析报告",
                page_title="SOA数据分析报告",
                subtitle="Service-Oriented Architecture 数据分析",
                nav_tabs=self.generate_nav_tabs("soa", timestamp)
            )
            
            # 渲染SOA页面内容，处理所有占位符
            # 确保所有必需的占位符都有默认值
            default_data = {
                'soa_topic_count': 0,
                'soa_data_points': 0,
                'soa_file_count': 0,
                'soa_charts_section': '',
                'chart_scripts': ''
            }
            # 合并默认数据和传入数据
            merged_data = {**default_data, **data}
            soa_content = self.templates['soa_page'].format(**merged_data)
            template_data.content = soa_content
            
            # 生成SOA数据加载和图表初始化脚本
            chart_scripts = """
            // SOA数据直接嵌入，无需fetch加载
            // 将SOA数据直接嵌入到页面中
            window.soaData = """ + json.dumps(data.get('soa_data', {}), ensure_ascii=False) + """;
            
            // 全局函数定义
            function showError(message) {
                console.error(message);
                const errorContainer = document.getElementById('soaError');
                if (errorContainer) {
                    errorContainer.innerHTML = '<div class="error-message">' + message + '</div>';
                    errorContainer.style.display = 'block';
                }
            }
            
            // 显示指定Topic的图表
            function showTopicChart(topicName) {
                try {
                    const chartContainer = document.getElementById('soaTopicChart');
                    const titleEl = document.getElementById('selectedTopicTitle');
                    const topicInfo = document.getElementById('topicInfo');
                    
                    if (chartContainer && titleEl && topicInfo) {
                        // 更新标题
                        titleEl.textContent = 'SOA Topic数据分析: ' + topicName;
                        
                        // 更新Topic信息
                        if (window.soaData && window.soaData.statistics) {
                            const stats = window.soaData.statistics;
                            topicInfo.innerHTML = '<div class="topic-stats">' +
                                '<p><strong>Topic名称:</strong> ' + topicName + '</p>' +
                                '<p><strong>总Topic数:</strong> ' + (stats.topic_count || 0) + '</p>' +
                                '<p><strong>数据点数量:</strong> ' + (stats.data_points || 0) + '</p>' +
                                '<p><strong>包含SOA数据文件:</strong> ' + (stats.file_count || 0) + '</p>' +
                                '</div>';
                        }
                        
                        // 初始化图表
                        if (window.currentChart) {
                            window.currentChart.dispose();
                        }
                        
                        const chartData = window.topicCharts[topicName];
                        if (chartData) {
                            window.currentChart = echarts.init(chartContainer);
                            window.currentChart.setOption(chartData);
                            
                            // 添加窗口大小变化监听
                            window.addEventListener('resize', function() {
                                if (window.currentChart) {
                                    window.currentChart.resize();
                                }
                            });
                            
                            console.log('Topic图表 ' + topicName + ' 显示成功');
                        } else {
                            chartContainer.innerHTML = '<div class="error-message">未找到Topic数据: ' + topicName + '</div>';
                        }
                    }
                } catch (error) {
                    console.error('显示Topic图表失败:', error);
                    const chartContainer = document.getElementById('soaTopicChart');
                    if (chartContainer) {
                        chartContainer.innerHTML = '<div class="error-message">显示Topic图表失败: ' + error.message + '</div>';
                    }
                }
            }
            
            // 生成汇总统计表格
            function generateSummaryTable(data) {
                try {
                    const tableBody = document.getElementById('soaSummaryTableBody');
                    if (!tableBody) return;
                    
                    if (data.statistics) {
                        const stats = data.statistics;
                        tableBody.innerHTML = 
                            '<tr><td><strong>Topic总数</strong></td><td>' + (stats.topic_count || 0) + '</td><td>系统中发现的SOA Topic数量</td></tr>' +
                            '<tr><td><strong>数据点总数</strong></td><td>' + (stats.data_points || 0) + '</td><td>所有Topic的数据点总数</td></tr>' +
                            '<tr><td><strong>有数据Topic数</strong></td><td>' + (stats.topics_with_data || 0) + '</td><td>包含实际数据的Topic数量</td></tr>' +
                            '<tr><td><strong>无数据Topic数</strong></td><td>' + (stats.topics_without_data || 0) + '</td><td>不包含实际数据的Topic数量</td></tr>' +
                            '<tr><td><strong>总丢失数据</strong></td><td>' + (stats.total_lost_data || 0) + '</td><td>所有Topic的丢失数据包总数</td></tr>';
                    } else {
                        tableBody.innerHTML = '<tr><td colspan="3">暂无汇总统计数据</td></tr>';
                    }
                } catch (error) {
                    console.error('生成汇总统计表格失败:', error);
                }
            }
            
            // 生成Topic详细统计表格
            function generateTopicDetailTable(data) {
                try {
                    const tableBody = document.getElementById('soaTopicDetailTableBody');
                    if (!tableBody) return;
                    
                    if (data.charts && data.charts.topic_charts) {
                        const topicCharts = data.charts.topic_charts;
                        let html = '';
                        let index = 1;
                        
                        Object.keys(topicCharts).forEach(topicName => {
                            const chartData = topicCharts[topicName];
                            if (chartData && chartData.series && chartData.series.length > 0) {
                                // 计算发送、接收和丢失数据总数
                                let totalSent = 0, totalReceived = 0, totalLost = 0;
                                chartData.series.forEach(series => {
                                    if (series.name === '发送数据' && series.data) {
                                        totalSent = series.data.reduce((sum, val) => sum + (val || 0), 0);
                                    } else if (series.name === '接收数据' && series.data) {
                                        totalReceived = series.data.reduce((sum, val) => sum + (val || 0), 0);
                                    } else if (series.name === '丢失数据' && series.data) {
                                        totalLost = series.data.reduce((sum, val) => sum + (val || 0), 0);
                                    }
                                });
                                
                                const status = (totalSent > 0 || totalReceived > 0 || totalLost > 0) ? '有数据' : '无数据';
                                const details = '发送: ' + totalSent + ', 接收: ' + totalReceived + ', 丢失: ' + totalLost;
                                
                                html += '<tr>' +
                                    '<td>' + index + '</td>' +
                                    '<td>' + topicName + '</td>' +
                                    '<td>' + totalSent + '</td>' +
                                    '<td>' + totalReceived + '</td>' +
                                    '<td>' + totalLost + '</td>' +
                                    '<td>' + status + '</td>' +
                                    '<td>' + details + '</td>' +
                                    '</tr>';
                                index++;
                            }
                        });
                        
                        if (html) {
                            tableBody.innerHTML = html;
                        } else {
                            tableBody.innerHTML = '<tr><td colspan="7">暂无Topic详细统计数据</td></tr>';
                        }
                    } else {
                        tableBody.innerHTML = '<tr><td colspan="7">暂无Topic详细统计数据</td></tr>';
                    }
                } catch (error) {
                    console.error('生成Topic详细统计表格失败:', error);
                }
            }
            
            // 生成SOA日志详细表格
            function generateLogDetailTable(data) {
                try {
                    const tableBody = document.getElementById('soaLogDetailTableBody');
                    if (!tableBody) return;
                    
                    if (data.log_details && data.log_details.length > 0) {
                        let html = '';
                        data.log_details.forEach((log, index) => {
                            html += '<tr>' +
                                '<td>' + (index + 1) + '</td>' +
                                '<td>' + (log.file_name || 'N/A') + '</td>' +
                                '<td>' + (log.line_number || 'N/A') + '</td>' +
                                '<td>' + (log.raw_line || 'N/A') + '</td>' +
                                '<td>' + (log.data_type || 'N/A') + '</td>' +
                                '</tr>';
                        });
                        tableBody.innerHTML = html;
                    } else {
                        tableBody.innerHTML = '<tr><td colspan="5">暂无SOA日志详细信息</td></tr>';
                    }
                } catch (error) {
                    console.error('生成SOA日志详细表格失败:', error);
                }
            }
            
            // 初始化表格展开/收起功能
            function initTableExpandCollapse() {
                // Topic详细统计表格展开/收起功能
                const expandTopicBtn = document.getElementById('expandTopicBtn');
                const collapseTopicBtn = document.getElementById('collapseTopicBtn');
                const topicTableBody = document.getElementById('soaTopicDetailTableBody');
                const topicTableInfo = document.getElementById('topicTableInfo');
                
                if (expandTopicBtn && collapseTopicBtn && topicTableBody) {
                    const topicRows = topicTableBody.querySelectorAll('tr');
                    const totalTopicRows = topicRows.length;
                    
                    // 默认显示前10行
                    let currentDisplayCount = Math.min(10, totalTopicRows);
                    updateTopicTableDisplay(currentDisplayCount, totalTopicRows);
                    
                    expandTopicBtn.addEventListener('click', function() {
                        currentDisplayCount = totalTopicRows;
                        updateTopicTableDisplay(currentDisplayCount, totalTopicRows);
                    });
                    
                    collapseTopicBtn.addEventListener('click', function() {
                        currentDisplayCount = Math.min(10, totalTopicRows);
                        updateTopicTableDisplay(currentDisplayCount, totalTopicRows);
                    });
                }
                
                // SOA详细日志表格展开/收起功能
                const expandLogBtn = document.getElementById('expandLogBtn');
                const collapseLogBtn = document.getElementById('collapseLogBtn');
                const logTableBody = document.getElementById('soaLogDetailTableBody');
                const logTableInfo = document.getElementById('logTableInfo');
                
                if (expandLogBtn && collapseLogBtn && logTableBody) {
                    const logRows = logTableBody.querySelectorAll('tr');
                    const totalLogRows = logRows.length;
                    
                    // 默认显示前10行
                    let currentDisplayCount = Math.min(10, totalLogRows);
                    updateLogTableDisplay(currentDisplayCount, totalLogRows);
                    
                    expandLogBtn.addEventListener('click', function() {
                        currentDisplayCount = totalLogRows;
                        updateLogTableDisplay(currentDisplayCount, totalLogRows);
                    });
                    
                    collapseLogBtn.addEventListener('click', function() {
                        currentDisplayCount = Math.min(10, totalLogRows);
                        updateLogTableDisplay(currentDisplayCount, totalLogRows);
                    });
                }
            }
            
            function updateTopicTableDisplay(displayCount, totalCount) {
                const topicTableBody = document.getElementById('soaTopicDetailTableBody');
                const topicTableInfo = document.getElementById('topicTableInfo');
                const topicRows = topicTableBody.querySelectorAll('tr');
                
                topicRows.forEach((row, index) => {
                    if (index < displayCount) {
                        row.classList.remove('table-row-hidden');
                    } else {
                        row.classList.add('table-row-hidden');
                    }
                });
                
                if (topicTableInfo) {
                    if (displayCount >= totalCount) {
                        topicTableInfo.textContent = '显示全部 ' + totalCount + ' 行';
                    } else {
                        topicTableInfo.textContent = '显示前 ' + displayCount + ' 行，共 ' + totalCount + ' 行，点击"展开全部"查看更多';
                    }
                }
            }
            
            function updateLogTableDisplay(displayCount, totalCount) {
                const logTableBody = document.getElementById('soaLogDetailTableBody');
                const logTableInfo = document.getElementById('logTableInfo');
                const logRows = logTableBody.querySelectorAll('tr');
                
                logRows.forEach((row, index) => {
                    if (index < displayCount) {
                        row.classList.remove('table-row-hidden');
                    } else {
                        row.classList.add('table-row-hidden');
                    }
                });
                
                if (logTableInfo) {
                    if (displayCount >= totalCount) {
                        logTableInfo.textContent = '显示全部 ' + totalCount + ' 行';
                    } else {
                        logTableInfo.textContent = '显示前 ' + displayCount + ' 行，共 ' + totalCount + ' 行，点击"展开全部"查看更多';
                    }
                }
            }
            
            // 初始化SOA图表
            function initializeSOACharts(data) {
                try {
                    // 更新统计信息
                    if (data.statistics) {
                        const topicCountEl = document.getElementById('topicCount');
                        const dataPointsEl = document.getElementById('dataPoints');
                        const fileCountEl = document.getElementById('fileCount');
                        
                        if (topicCountEl) topicCountEl.textContent = data.statistics.topic_count || 0;
                        if (dataPointsEl) dataPointsEl.textContent = data.statistics.data_points || 0;
                        if (fileCountEl) fileCountEl.textContent = data.statistics.file_count || 0;
                    }
                    
                    // 初始化下拉菜单
                    if (data.charts && data.charts.topic_charts && Object.keys(data.charts.topic_charts).length > 0) {
                        window.topicCharts = data.charts.topic_charts;
                        const topicNames = Object.keys(data.charts.topic_charts);
                        
                        const topicSelect = document.getElementById('topicSelect');
                        if (topicSelect) {
                            topicSelect.innerHTML = '<option value="">请选择Topic</option>';
                            topicNames.forEach(topicName => {
                                const option = document.createElement('option');
                                option.value = topicName;
                                option.textContent = topicName;
                                topicSelect.appendChild(option);
                            });
                            
                            // 添加change事件监听
                            topicSelect.addEventListener('change', function() {
                                const selectedTopic = this.value;
                                if (selectedTopic) {
                                    showTopicChart(selectedTopic);
                                }
                            });
                            
                            console.log('SOA Topic下拉菜单初始化成功，共 ' + topicNames.length + ' 个Topic');
                        }
                    } else {
                        console.log('SOA Topic图表: 无数据');
                        const topicInfo = document.getElementById('topicInfo');
                        if (topicInfo) {
                            topicInfo.innerHTML = '<p class="error-message">暂无SOA Topic数据</p>';
                        }
                    }
                    
                    // 初始化SOA汇总图表
                    if (data.charts && data.charts.summary_chart && Object.keys(data.charts.summary_chart).length > 0) {
                        const summaryChartEl = document.getElementById('soaSummaryChart');
                        if (summaryChartEl) {
                            try {
                                const summaryChart = echarts.init(summaryChartEl);
                                summaryChart.setOption(data.charts.summary_chart);
                                window.addEventListener('resize', function() {
                                    summaryChart.resize();
                                });
                                console.log('SOA汇总图表初始化成功');
                            } catch (chartError) {
                                console.error('SOA汇总图表初始化失败:', chartError);
                                summaryChartEl.innerHTML = '<div class="error-message">汇总图表初始化失败: ' + chartError.message + '</div>';
                            }
                        }
                    } else {
                        const summaryChartEl = document.getElementById('soaSummaryChart');
                        if (summaryChartEl) {
                            summaryChartEl.innerHTML = '<div class="loading">暂无SOA汇总数据</div>';
                            console.log('SOA汇总图表: 无数据');
                        }
                    }
                    
                    // 生成汇总统计表格
                    generateSummaryTable(data);
                    
                    // 生成Topic详细统计表格
                    generateTopicDetailTable(data);
                    
                    // 生成SOA日志详细表格
                    generateLogDetailTable(data);
                    
                    // 初始化表格展开/收起功能
                    initTableExpandCollapse();
                    
                    console.log('所有SOA图表和表格初始化完成');
                    
                } catch (error) {
                    console.error('SOA图表初始化失败:', error);
                    showError('SOA图表初始化失败: ' + error.message);
                }
            }
            
            document.addEventListener('DOMContentLoaded', function() {
                console.log('SOA页面加载完成，开始初始化SOA数据...');
                
                // 直接使用嵌入的SOA数据
                const soaData = window.soaData || {};
                console.log('SOA数据已就绪:', soaData);
                
                if (soaData && Object.keys(soaData).length > 0) {
                    initializeSOACharts(soaData);
                } else {
                    console.error('SOA数据为空，无法初始化图表');
                    showError('SOA数据为空，请检查数据生成');
                }
            });
            """
            
            template_data.chart_scripts = chart_scripts
            
            # 渲染最终HTML
            return self.templates['base'].format(
                title=template_data.title,
                page_title=template_data.page_title,
                subtitle=template_data.subtitle,
                nav_tabs=template_data.nav_tabs,
                content=template_data.content,
                chart_scripts=template_data.chart_scripts,
                timestamp=timestamp,
                project_name=data.get('project_name', '未知项目'),
                baseline_version=data.get('baseline_version', '未知版本')
            )
            
        except Exception as e:
            self.logger.error(f"渲染SOA页面失败: {e}")
            return f"<h1>页面渲染失败</h1><p>错误信息: {e}</p>"
    
    def render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """渲染指定模板"""
        if template_name not in self.templates:
            raise ValueError(f"模板 {template_name} 不存在")
        
        try:
            return self.templates[template_name].format(**data)
        except Exception as e:
            self.logger.error(f"渲染模板 {template_name} 失败: {e}")
            return f"<h1>模板渲染失败</h1><p>错误信息: {e}</p>"

# 创建全局实例
template_manager = TemplateManager()
