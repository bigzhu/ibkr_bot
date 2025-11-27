#!/bin/bash
# 调度器启动脚本 - 启动整点调度器服务
# 每分钟整点执行demark计算

set -e  # 出错时退出

# 自动切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "🚀 启动整点调度器服务..."

# 检查是否在正确的目录
if [ ! -d "scheduler" ] || [ ! -f "scheduler/__main__.py" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查uv命令
if ! command -v uv >/dev/null 2>&1; then
    echo "❌ 错误: 未找到uv,请先安装uv包管理器"
    exit 1
fi

echo "📁 当前目录: $(pwd)"
echo "🐍 Python版本: $(uv run python --version)"
echo "⏰ 启动调度器服务..."
echo "📝 调度器将在每分钟整点(0秒)执行demark计算"

# 默认精简日志样式与子进程降噪
# 可通过在运行前覆盖以下环境变量进行调整:
#   SCHEDULER_LOG_STYLE=normal|concise
#   SCHEDULER_WORKER_LOG_LEVEL=ERROR|WARNING|INFO
export SCHEDULER_LOG_STYLE=${SCHEDULER_LOG_STYLE:-concise}
export SCHEDULER_WORKER_LOG_LEVEL=${SCHEDULER_WORKER_LOG_LEVEL:-ERROR}

# 使用uv运行调度器模块
uv run python -m scheduler

echo ""
echo "📝 提示:"
echo "- 调度器每分钟整点执行一次"
echo "- 测试执行: uv run python -m scheduler test"
echo "- 停止服务: Ctrl+C"
