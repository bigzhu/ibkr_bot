"""
MEXC DeMark 14 Trading Bot - 重构版本 v2.0

一个基于模块化设计的MEXC交易机器人,采用 DeMark 14 技术指标.

## 模块架构

- **database/**: 数据库操作模块
- **demark/**: DeMark 14 指标计算模块
- **ibkr_api/**: Binance API 接口模块
- **order_filler/**: 币安订单撮合处理模块
- **webadmin/**: Web 管理端 API 模块
- **monitor/**: 监控和调度模块
- **logging/**: 日志管理模块
- **config/**: 配置管理模块
- **utils/**: 通用工具模块
- **scripts/**: 可执行脚本模块

## 设计原则

- 单一职责原则:每个模块只负责一个特定功能
- 完全独立:不依赖外部目录的任何资源
- 金融数据零容忍:任何数据异常都立即失败
- 易于测试:每个模块都可独立测试
"""

__version__ = "2.0.0"
__author__ = "bigzhu"
__description__ = "MEXC DeMark 14 Trading Bot - Modular Refactored Version"

# 交易方向常量
BUY = "BUY"
SELL = "SELL"
