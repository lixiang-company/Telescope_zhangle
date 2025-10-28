# ECU日志分析系统 🚗

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/ecuanalyzer/telescope_bak)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)](#)

> 专业的汽车电子控制单元(ECU)日志分析工具，提供全面的性能监控、异常检测和数据可视化功能。

## 📋 项目概述

ECU日志分析系统是一个专为汽车电子工程师和系统调试人员设计的综合性分析工具。它能够解析ECU日志文件，提取关键性能指标，并生成直观的可视化报告。

### 🎯 核心功能

- **🔍 日志解析**: 支持多种ECU日志格式的智能解析
- **📊 性能监控**: 实时CPU核心负载率监控和分析
- **⚠️ 异常检测**: TRAP重启事件的智能识别和分析
- **🌐 SOA分析**: 服务导向架构通信数据深度分析
- **📈 数据可视化**: 基于ECharts的专业图表展示
- **📄 报告生成**: 生成详细的HTML格式分析报告

### 🏗️ 技术架构

- **架构模式**: 模块化设计，纯新版架构
- **编程语言**: Python 3.7+
- **可视化引擎**: ECharts
- **模板引擎**: Jinja2
- **数据格式**: JSON, HTML

## 🚀 快速开始

### 环境要求

- Python 3.7 或更高版本
- 操作系统: Windows/Linux/macOS

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/ecuanalyzer/telescope_bak.git
cd telescope_bak
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行分析**
```bash
# 分析单个文件
python pure_new_ecu_analyzer.py -f path/to/logfile.log

# 分析整个目录
python pure_new_ecu_analyzer.py -d path/to/logs/

# 详细模式
python pure_new_ecu_analyzer.py -d path/to/logs/ -v
```

### 使用示例

```bash
# 基本用法
python pure_new_ecu_analyzer.py -f data/sample_logs/ecu_log_001.log

# 批量分析
python pure_new_ecu_analyzer.py -d data/sample_logs/ -v

# 查看帮助
python pure_new_ecu_analyzer.py -h
```

## 📁 项目结构

```
telescope_bak/
├── 📄 README.md                    # 项目说明文档
├── 📄 requirements.txt             # 项目依赖
├── 📄 setup.py                     # 安装配置
├── 🐍 pure_new_ecu_analyzer.py     # 主程序入口
├── 📁 src/                         # 源代码目录
│   └── 📁 ecu_log_analyzer/        # 核心分析模块
│       ├── 📄 __init__.py          # 模块初始化
│       ├── 📁 analyzers/           # 分析器模块
│       ├── 📁 config/              # 配置管理
│       ├── 📁 core/                # 核心功能
│       ├── 📁 reports/             # 报告生成
│       └── 📁 utils/               # 工具函数
├── 📁 resources/                   # 资源文件
│   └── 📁 static/                  # 静态资源
│       ├── 📄 echarts.min.js       # ECharts库
│       └── 📁 templates/           # HTML模板
├── 📁 data/                        # 测试数据
│   └── 📁 sample_logs/             # 示例日志文件
└── 📁 output/                      # 输出目录
    └── (生成的分析报告)
```

## 🔧 核心模块

### 1. 日志解析器 (Log Parser)
- 支持多种ECU日志格式
- 智能数据提取和清洗
- 高性能并行处理

### 2. 性能分析器 (Performance Analyzer)
- CPU核心负载率统计
- 内存使用情况监控
- 系统性能指标分析

### 3. 异常检测器 (Exception Detector)
- TRAP重启事件识别
- 异常模式分析
- 故障根因分析

### 4. SOA分析器 (SOA Analyzer)
- 服务通信分析
- Topic数据统计
- 通信性能评估

### 5. 报告生成器 (Report Generator)
- HTML可视化报告
- JSON数据导出
- 图表交互功能

## 📊 分析报告

生成的分析报告包含以下内容：

### 📈 主要图表
- **CPU核心负载率统计图**: 多核心负载实时监控
- **项目负载率对比图**: 不同项目性能对比
- **负载趋势分析图**: 时间序列趋势分析
- **TRAP重启分析图**: 异常事件可视化

### 📋 统计信息
- 文件处理统计
- 性能指标汇总
- 异常事件统计
- SOA通信分析

### 🎨 可视化特性
- 响应式设计
- 交互式图表
- 专业样式
- 导出功能

## ⚙️ 配置选项

### 分析配置
```python
# CPU负载阈值设置
LOAD_THRESHOLDS = {
    'normal': 70,    # 正常负载阈值
    'medium': 90,    # 中等负载阈值
    'high': 100      # 高负载阈值
}

# 输出配置
OUTPUT_CONFIG = {
    'format': 'html',           # 输出格式
    'include_charts': True,     # 包含图表
    'include_raw_data': False   # 包含原始数据
}
```

## 🔍 性能优化

- **内存优化**: 大文件流式处理
- **并行处理**: 多文件并行分析
- **缓存机制**: 智能结果缓存
- **懒加载**: 按需加载模块

## 🧪 测试

项目包含完整的测试数据：

```bash
# 运行示例分析
python pure_new_ecu_analyzer.py -d data/sample_logs/ -v
```

测试数据包含：
- 多种ECU日志格式
- 不同负载情况
- 异常事件样本
- SOA通信数据

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发规范
- 遵循 PEP 8 编码规范
- 添加适当的注释和文档
- 编写单元测试
- 确保向后兼容性

## 📝 更新日志

### v2.0.0 (最新)
- ✨ 全新架构重构
- 🎨 改进的用户界面
- 🚀 性能优化提升
- 📊 增强的可视化功能
- 🔧 模块化设计

### v1.x.x
- 基础功能实现
- 日志解析功能
- 简单报告生成

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 📞 联系我们

- **项目主页**: [GitHub Repository](https://github.com/ecuanalyzer/telescope_bak)
- **问题反馈**: [Issues](https://github.com/ecuanalyzer/telescope_bak/issues)
- **邮箱**: team@ecuanalyzer.com

## 🙏 致谢

感谢所有为项目做出贡献的开发者和用户！

---

**💡 提示**: 如果您在使用过程中遇到任何问题，请查看 [Issues](https://github.com/ecuanalyzer/telescope_bak/issues) 或创建新的问题报告。

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**