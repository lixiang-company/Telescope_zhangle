# -*- coding: utf-8 -*-
"""
ECU日志分析系统安装配置
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

# 读取requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="ecu-log-analyzer",
    version="2.0.0",
    author="ECU Log Analyzer Team",
    author_email="team@ecuanalyzer.com",
    description="专业的汽车ECU日志分析工具",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="xxx",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
        "performance": [
            "psutil>=5.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ecu-analyzer=ecu_log_analyzer.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ecu_log_analyzer": [
            "resources/static/templates/*.html",
            "resources/static/css/*.css",
            "resources/static/js/*.js",
            "resources/configs/*.yaml",
        ],
    },
)