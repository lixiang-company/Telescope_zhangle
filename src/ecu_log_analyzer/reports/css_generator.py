# -*- coding: utf-8 -*-
"""
CSS文件生成器
负责生成独立的CSS样式文件
"""

import os
from typing import Dict, Any

class CSSGenerator:
    """CSS文件生成器类"""
    
    def __init__(self):
        pass
    
    def generate_base_css(self) -> str:
        """生成基础CSS样式"""
        return """
/* 基础样式重置 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* 主体样式 */
body {
    font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    line-height: 1.6;
    color: #333;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 0;
}

/* 导航栏样式 */
.navbar {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    position: sticky;
    top: 0;
    z-index: 1000;
    box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

.nav-container {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 30px;
    height: 60px;
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.nav-logo {
    font-size: 24px;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.nav-title {
    font-size: 18px;
    font-weight: 600;
    color: #2c3e50;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.nav-project-info {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    margin-left: 15px;
    padding-left: 15px;
    border-left: 2px solid rgba(102, 126, 234, 0.3);
}

.project-name {
    font-size: 14px;
    font-weight: 500;
    color: #2c3e50;
    margin-bottom: 2px;
}

.baseline-version {
    font-size: 12px;
    color: #7f8c8d;
    font-weight: 400;
}

.nav-menu {
    display: flex;
    gap: 20px;
}

.nav-link {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-decoration: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.nav-link:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
}

.nav-link.active {
    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    box-shadow: 0 4px 16px rgba(90, 103, 216, 0.4);
}

.nav-icon {
    font-size: 16px;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

/* 容器样式 */
.container {
    max-width: 1400px;
    margin: 15px auto;
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    overflow: hidden;
}

/* 头部样式 */
.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 25px 30px;
    text-align: center;
    position: relative;
}

.header h1 {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 8px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.header .subtitle {
    font-size: 12px;
    opacity: 0.9;
}

/* 导航标签样式 */
.nav-tabs {
    position: absolute;
    top: 20px;
    right: 30px;
    display: flex;
    gap: 10px;
}

.nav-tab {
    padding: 8px 16px;
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    color: white;
    text-decoration: none;
    font-size: 12px;
    transition: all 0.3s ease;
}

.nav-tab:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
}

.nav-tab.active {
    background: rgba(255, 255, 255, 0.4);
    border-color: rgba(255, 255, 255, 0.6);
}

/* 内容区域样式 */
.content {
    padding: 25px 30px;
}

.section {
    margin-bottom: 35px;
    padding: 20px;
    background-color: #fafbfc;
    border-radius: 8px;
    border: 1px solid #e1e8ed;
}

.section-header {
    display: flex;
    align-items: center;
    margin-bottom: 18px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e1e8ed;
}

.section-icon {
    width: 20px;
    height: 20px;
    margin-right: 10px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 3px;
}

/* 标题样式 */
h2 {
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
    margin: 0;
}

h3 {
    font-size: 14px;
    font-weight: 600;
    color: #34495e;
    margin-bottom: 12px;
}

/* 统计卡片样式 */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.stat-card {
    background: white;
    border: 1px solid #e1e8ed;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.stat-number {
    font-size: 20px;
    font-weight: 700;
    color: #667eea;
    margin-bottom: 4px;
}

.stat-label {
    font-size: 11px;
    color: #7f8c8d;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* 数据表格样式 */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
    background: white;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.data-table th {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 10px 8px;
    text-align: left;
    font-weight: 600;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.data-table td {
    padding: 8px;
    border-bottom: 1px solid #f1f3f4;
    vertical-align: middle;
}

.data-table tr:nth-child(even) {
    background-color: #f8f9fa;
}

.data-table tr:hover {
    background-color: #e8f4fd;
}

/* 图表容器样式 */
.chart-wrapper {
    background: white;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 25px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border: 1px solid #e1e8ed;
}

.chart-container {
    width: 100%;
    height: 400px;
    margin: 20px 0;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
}

.v-chart-container {
    width: 100%;
    height: 400px;
}

/* 警告框样式 */
.alert {
    padding: 12px 16px;
    margin-bottom: 20px;
    border-radius: 6px;
    border-left: 4px solid;
    font-size: 12px;
}

.alert strong {
    font-weight: 600;
}

.alert-info {
    background-color: #e8f4fd;
    border-left-color: #1890ff;
    color: #0c5460;
}

.alert-warning {
    background-color: #fff7e6;
    border-left-color: #fa8c16;
    color: #d46b08;
}

.alert-danger {
    background-color: #fff2f0;
    border-left-color: #f5222d;
    color: #cf1322;
}

/* 负载指示器样式 */
.load-indicator {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
}

.load-low { 
    background-color: #d4edda; 
    color: #155724; 
}

.load-medium { 
    background-color: #fff3cd; 
    color: #856404; 
}

.load-high { 
    background-color: #f8d7da; 
    color: #721c24; 
}

/* 文件路径样式 */
.file-path {
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 10px;
    color: #6c757d;
    background: #f8f9fa;
    padding: 2px 4px;
    border-radius: 3px;
}

/* 加载提示样式 */
.loading {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 400px;
    color: #666;
    font-size: 1.2em;
    background: #f8f9fa;
    border-radius: 8px;
}

/* 信息卡片样式 */
.info-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.info-card {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    border: 1px solid #e9ecef;
}

.info-value {
    font-size: 2em;
    font-weight: bold;
    color: #667eea;
    margin-bottom: 10px;
}

.info-label {
    color: #666;
    font-size: 0.9em;
}

.charts-section {
    margin-top: 30px;
}

/* SOA信息样式 */
.soa-info {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
    border: 1px solid #e9ecef;
}

.soa-info p {
    margin: 10px 0;
    font-size: 1.1em;
}

.soa-info span {
    font-weight: bold;
    color: #667eea;
}

/* 展开/收起功能样式 */
.section-actions {
    display: flex;
    gap: 10px;
    margin-left: auto;
}

.btn {
    padding: 6px 12px;
    border: none;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    display: inline-block;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
}

.btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
    background: #f8f9fa;
    color: #6c757d;
    border: 1px solid #dee2e6;
}

.btn-secondary:hover {
    background: #e9ecef;
    color: #495057;
}

.table-footer {
    padding: 10px;
    background: #f8f9fa;
    border-top: 1px solid #dee2e6;
    text-align: center;
    font-size: 11px;
    color: #6c757d;
}

.table-footer span {
    font-style: italic;
}

/* 隐藏行样式 */
.table-row-hidden {
    display: none;
}

/* 状态指示器样式 */
.status-high {
    background-color: #f8d7da;
    color: #721c24;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
}

.status-medium {
    background-color: #fff3cd;
    color: #856404;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
}

.status-low {
    background-color: #d4edda;
    color: #155724;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
}

.status-valid {
    background-color: #d4edda;
    color: #155724;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
}

.status-invalid {
    background-color: #f8d7da;
    color: #721c24;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
}
"""
    
    def save_css_file(self, css_content: str, filepath: str) -> None:
        """保存CSS文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(css_content)
    
    def generate_all_css_files(self, static_dir: str) -> Dict[str, str]:
        """生成所有CSS文件并返回文件路径映射"""
        css_files = {}
        
        # 生成主样式文件
        main_css_path = os.path.join(static_dir, 'main.css')
        main_css_content = self.generate_base_css()
        self.save_css_file(main_css_content, main_css_path)
        css_files['main'] = 'static/main.css'
        
        return css_files

# 创建全局CSS生成器实例
css_generator = CSSGenerator()