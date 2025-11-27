#!/bin/bash

# 统一同步脚本 - 调用前端和后端同步脚本
# 提供完整的项目部署解决方案

set -e  # 出错时退出

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=./lib_remote_env.sh
. "$SCRIPT_DIR/lib_remote_env.sh"
# shellcheck source=./lib_sync.sh
. "$SCRIPT_DIR/lib_sync.sh"
load_remote_env
require_remote_dir

# 检查必要的脚本文件是否存在
FRONTEND_SYNC="$PROJECT_ROOT/scripts/frontend_sync.sh"
BACKEND_SYNC="$PROJECT_ROOT/scripts/backend_sync.sh"
ensure_scripts_executable "$FRONTEND_SYNC" "$BACKEND_SYNC"

echo "🚀 开始项目同步..."
echo "📍 项目根目录: $PROJECT_ROOT"
echo ""

# 显示使用说明
show_usage() {
    echo "用法: $0 [frontend|backend|all] [选项]"
    echo ""
    echo "选项:"
    echo "  --targets bot,lead   依次同步多个 REMOTE_DIR_NAME, 逗号分隔 (默认使用当前环境)"
    echo "  --skip-frontend      在 all 模式下跳过前端同步"
    echo "  --skip-backend       在 all 模式下跳过后端同步"
    echo "  --help|-h|help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                    # 同步当前 REMOTE_DIR_NAME 的前端和后端"
    echo "  $0 frontend          # 只同步前端"
    echo "  $0 --targets bot,lead # 依次同步 bot 与 lead"
}

# 解析命令行参数
ACTION="all"
TARGETS_ARG=""
SKIP_FRONTEND=0
SKIP_BACKEND=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        frontend|backend|all)
            ACTION="$1"
            shift
            ;;
        --targets)
            TARGETS_ARG="${2:-}"
            shift 2
            ;;
        --targets=*)
            TARGETS_ARG="${1#*=}"
            shift
            ;;
        --skip-frontend)
            SKIP_FRONTEND=1
            shift
            ;;
        --skip-backend)
            SKIP_BACKEND=1
            shift
            ;;
        --help|-h|help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ 错误: 未知选项 '$1'"
            echo ""
            show_usage
            exit 1
            ;;
    esac
done

if [ -z "$TARGETS_ARG" ]; then
    require_remote_dir
    TARGETS_ARG="$REMOTE_DIR_NAME"
fi

IFS=',' read -r -a SYNC_TARGETS <<< "$TARGETS_ARG"
if [ "${#SYNC_TARGETS[@]}" -eq 0 ]; then
    echo "❌ 错误: --targets 不能为空"
    exit 1
fi

run_backend_sync() {
    if [ "$SKIP_BACKEND" -eq 1 ]; then
        echo "⏭️ 已跳过后端同步"
        return
    fi
    echo "⚙️ 开始后端同步..."
    echo "=================================="
    "$BACKEND_SYNC"
    echo ""
    echo "✅ 后端同步完成!"
    echo ""
}

run_frontend_sync() {
    if [ "$SKIP_FRONTEND" -eq 1 ]; then
        echo "⏭️ 已跳过前端同步"
        return
    fi
    echo "🎨 开始前端同步..."
    echo "=================================="
    "$FRONTEND_SYNC"
    echo ""
    echo "✅ 前端同步完成!"
    echo ""
}

perform_sync() {
    case "$ACTION" in
        frontend)
            run_frontend_sync
            ;;
        backend)
            run_backend_sync
            ;;
        all)
            run_backend_sync
            run_frontend_sync
            echo "🎉 完整项目同步成功!"
            ;;
        *)
            echo "❌ 错误: 未知模式 '$ACTION'"
            exit 1
            ;;
    esac
}

TARGETS_PROCESSED=0
for target in "${SYNC_TARGETS[@]}"; do
    target="$(echo "$target" | tr -d '[:space:]')"
    if [ -z "$target" ]; then
        continue
    fi
    REMOTE_DIR_NAME="$target"
    export REMOTE_DIR_NAME
    require_remote_dir
    echo "🌐 目标远端目录: $(remote_base_path) (REMOTE_DIR_NAME=$REMOTE_DIR_NAME)"
    echo ""
    perform_sync
    TARGETS_PROCESSED=$((TARGETS_PROCESSED + 1))
done

if [ "$TARGETS_PROCESSED" -eq 0 ]; then
    echo "❌ 错误: 未指定有效 REMOTE_DIR_NAME"
    exit 1
fi

echo ""
echo "📝 同步完成提示:"
echo "1. 登录服务器检查服务状态: ssh bigzhu@bandwagonhost.bigzhu.net"
echo "2. 重启后端服务 (如需要): sudo systemctl restart your-service"
echo "3. 重载Nginx配置: sudo nginx -s reload"
echo "4. 检查服务状态: sudo systemctl status nginx"
echo ""
echo "🌐 访问地址:"
echo "   - 前端界面: http://trading.bigzhu.net/"
echo "   - 管理界面: http://trading.bigzhu.net/admin"
echo "   - API文档: http://trading.bigzhu.net/api/docs"
echo ""
echo "🔧 相关脚本:"
echo "   - 只同步前端: $0 frontend"
echo "   - 只同步后端: $0 backend"
echo "   - 多环境同步: $0 --targets bot,lead"
