#!/bin/bash
# API服务启动脚本 - 启动Web Admin API服务
# 使用uvicorn启动FastAPI应用

set -e  # 出错时退出

# 自动切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "🚀 启动Web Admin API服务..."

# 检查是否在正确的目录
if [ ! -f "web_admin/api/start_api.py" ]; then
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
echo "📦 启动API服务..."

# shellcheck source=./lib_remote_env.sh
. "scripts/lib_remote_env.sh"
load_remote_env
require_remote_dir

# 根据 REMOTE_DIR_NAME 选择端口
BOT_API_PORT=${BOT_API_PORT:-8000}
LEAD_API_PORT=${LEAD_API_PORT:-8001}
if [ "$REMOTE_DIR_NAME" = "lead" ]; then
    WEB_ADMIN_PORT=${WEB_ADMIN_PORT:-$LEAD_API_PORT}
else
    WEB_ADMIN_PORT=${WEB_ADMIN_PORT:-$BOT_API_PORT}
fi
export WEB_ADMIN_PORT

echo "🔌 使用端口: $WEB_ADMIN_PORT (REMOTE_DIR_NAME=$REMOTE_DIR_NAME)"
echo "📑 文档: http://localhost:$WEB_ADMIN_PORT/api/docs"
echo "💓 健康: http://localhost:$WEB_ADMIN_PORT/health"

# 使用uv运行API服务
uv run python web_admin/api/start_api.py

echo ""
echo "📝 提示:"
echo "- API文档: http://localhost:$WEB_ADMIN_PORT/api/docs"
echo "- 健康检查: http://localhost:$WEB_ADMIN_PORT/health"
echo "- 停止服务: Ctrl+C"
