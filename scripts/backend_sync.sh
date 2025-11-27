#!/bin/bash
# 后端代码同步脚本 - 只同步Python后端代码到远程服务器
# 排除前端构建文件,专注于后端代码部署
set -e

# 进入项目根目录并加载 .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
# shellcheck source=./lib_sync.sh
. "$SCRIPT_DIR/lib_sync.sh"
load_remote_env
require_remote_dir
RBASE="/home/$RUSER/$REMOTE_DIR_NAME"
# 本地目录
LPATH=${LPATH:-/Users/bigzhu/Sync/Projects/mexc_bot}

# 同步前进行关键函数检查
if [ "${SKIP_BACKEND_CHECKS:-0}" != "1" ]; then
    echo "🔍 检查函数调用一致性..."
    if ! (cd "$PROJECT_ROOT" && uv run python scripts/check_specific_functions.py); then
        echo "❌ 函数调用检查失败,停止同步"
        exit 1
    fi
    echo "✅ 函数调用检查通过"
    echo ""
fi

# 执行后端代码同步
echo "🔄 开始同步后端代码到远程服务器..."
echo "📁 本地目录: $LPATH"
echo "🌐 远程目录: $RUSER@$RHOST:$RBASE (REMOTE_DIR_NAME=$REMOTE_DIR_NAME)"
echo ""

# 确保远程目录存在
ensure_remote_directory "$RBASE"

# 执行同步
echo "📦 同步后端代码和配置文件..."
rsync_with_options "$LPATH/" "$RUSER@$RHOST:$RBASE/" "${BACKEND_RSYNC_EXCLUDES[@]}"
echo "✅ 已同步: $RBASE"
echo ""

echo ""
echo "✅ 后端代码同步完成!"
echo ""
echo "📝 提示:"
echo "- 前端文件已排除,请使用 frontend_sync.sh 部署前端"
echo "- 如需重启后端服务,请登录服务器手动操作"
echo ""
echo "🔗 相关命令:"
echo "- 前端部署: ./scripts/frontend_sync.sh" 
echo "- 登录服务器: ssh $RUSER@$RHOST"
