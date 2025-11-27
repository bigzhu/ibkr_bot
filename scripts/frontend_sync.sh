#!/bin/bash

# 前端构建和部署脚本 - 构建Quasar前端并同步到服务器
# 专门用于前端的完整部署流程

set -e  # 出错时退出

# 自动切换到项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PROJECT_ROOT="$SCRIPT_DIR/.."
# shellcheck source=./lib_remote_env.sh
. "$SCRIPT_DIR/lib_remote_env.sh"
# shellcheck source=./lib_sync.sh
. "$SCRIPT_DIR/lib_sync.sh"
load_remote_env
require_remote_dir

show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --skip-install   跳过 yarn install"
    echo "  --force-install  无条件执行 yarn install"
    echo "  --help|-h|help   显示本帮助"
}

INSTALL_MODE="auto"
while [ "$#" -gt 0 ]; do
    case "$1" in
        --skip-install)
            INSTALL_MODE="skip"
            shift
            ;;
        --force-install)
            INSTALL_MODE="force"
            shift
            ;;
        --help|-h|help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ 错误: 未知选项 '$1'"
            show_usage
            exit 1
            ;;
    esac
done

FRONTEND_DIR="$PROJECT_ROOT/web_admin/frontend"
DIST_DIR="$FRONTEND_DIR/dist/spa"

echo "🚀 开始构建并同步前端到服务器..."

# 检查前端目录
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查是否有yarn
if ! command -v yarn >/dev/null 2>&1; then
    echo "❌ 错误: 未找到yarn,请先安装yarn"
    exit 1
fi

should_install_dependencies() {
    case "$INSTALL_MODE" in
        skip) return 1 ;;
        force) return 0 ;;
        auto)
            [ -d "$FRONTEND_DIR/node_modules" ] || return 0
            return 1
            ;;
    esac
}

echo "🔨 构建前端..."
if should_install_dependencies; then
    echo "📦 安装前端依赖..."
    (cd "$FRONTEND_DIR" && yarn install)
else
    echo "⏭️ 跳过依赖安装"
fi

echo "⚡ 开始构建前端..."
# 将 REMOTE_DIR_NAME 透传给构建,供 quasar.config.ts 使用
(cd "$FRONTEND_DIR" && REMOTE_DIR_NAME="$REMOTE_DIR_NAME" yarn quasar build)

echo "✅ 前端构建完成!"

# 2. 检查构建结果
if [ ! -f "$DIST_DIR/index.html" ]; then
    echo "❌ 错误: 前端构建失败,未找到index.html"
    exit 1
fi

# 2.1 添加版本时间戳到HTML文件,强制刷新缓存
echo "🕒 添加版本时间戳..."
TIMESTAMP=$(date +%s)
sed -i.bak "s/<html/<html data-version=\"$TIMESTAMP\"/g" "$DIST_DIR/index.html"
rm -f "$DIST_DIR/index.html.bak" 2>/dev/null || true

echo "📦 构建产物信息:"
echo "   - 主页面: $DIST_DIR/index.html (版本: $TIMESTAMP)"
echo "   - 资源目录: $DIST_DIR/assets/"
echo "   - 文件数量: $(find "$DIST_DIR" -type f | wc -l) 个文件"
echo "   - 总大小: $(du -sh "$DIST_DIR" | cut -f1)"

# 2.2 页面标题已在构建期由 quasar.config.ts 的 htmlVariables 注入,无需再二次替换

# 3. 同步前端到服务器
echo ""
echo "🌐 开始同步前端到服务器..."

RBASE="/home/$RUSER/$REMOTE_DIR_NAME"
RPATH="$RBASE/web_admin/frontend/dist/"

echo "📍 目标: $RUSER@$RHOST:$RPATH (REMOTE_DIR_NAME=$REMOTE_DIR_NAME)"

# 确保远程目录存在
echo "📁 确保远程目录存在: $RPATH/spa"
ensure_remote_directory "$RPATH/spa"

# 同步前端构建文件
echo "📦 同步前端构建文件到: $RPATH/spa"
rsync_with_options "$DIST_DIR/" "$RUSER@$RHOST:${RPATH}spa/" --delete
echo "✅ 已同步: $RPATH/spa"

echo ""
echo "✅ 构建和同步完成!"
echo ""
echo "📝 后续步骤:"
echo "1. 登录服务器: ssh bigzhu@bandwagonhost.bigzhu.net"
echo "2. 重载Nginx配置: sudo nginx -s reload"
echo "3. 检查服务状态: sudo systemctl status nginx"
echo ""
echo "🌐 访问地址:"
echo "   - 新前端界面: http://trading.bigzhu.net/"
echo "   - 老管理界面: http://trading.bigzhu.net/admin"
echo "   - API文档: http://trading.bigzhu.net/api/docs"
echo ""
echo "🔗 相关命令:"
echo "- 后端部署: ./scripts/backend_sync.sh"
