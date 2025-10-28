# -*- coding: utf-8 -*-
"""
ECU日志分析系统 - 配置模块
提供与历史版本兼容的全局 config 实例。
"""

import os
from .settings import Config

# 创建全局配置实例，优先从项目根目录的 config.yaml 加载
def _create_global_config() -> Config:
    # 尝试多种位置查找配置文件
    possible_paths = [
        os.path.join(os.getcwd(), 'config.yaml'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml'),
    ]
    for path in possible_paths:
        try:
            if os.path.exists(path):
                return Config.from_file(path)
        except Exception:
            continue
    return Config()

config = _create_global_config()

__all__ = ['Config', 'config']
