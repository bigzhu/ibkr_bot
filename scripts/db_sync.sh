#!/bin/bash
# SQLite数据库单向同步脚本
# 从远程服务器下载数据库文件(支持WAL模式)到本地
# 远程目录从项目根目录下的 .env 读取: REMOTE_DIR_NAME=bot|lead
set -e

# 进入项目根目录并加载 .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
# shellcheck source=./lib_remote_env.sh
. "$SCRIPT_DIR/lib_remote_env.sh"
load_remote_env
require_remote_dir

show_usage() {
  echo "用法: $0 [--help|-h]"
  echo "说明: 从远端指定目录(bot 或 lead)的 data 下载 SQLite 数据库到本地 data/"
  echo "配置: 在项目 .env 设置 REMOTE_DIR_NAME=bot 或 lead; 可覆盖环境变量 RUSER, RHOST, LPATH"
  echo "示例: REMOTE_DIR_NAME=lead ./scripts/db_sync.sh"
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  show_usage
  exit 0
fi

RPATH="/home/$RUSER/$REMOTE_DIR_NAME/data"
LPATH=${LPATH:-/Users/bigzhu/Sync/Projects/mexc_bot/data}

# 数据库文件列表
DB_FILES=("bot.db" "bot.db-shm" "bot.db-wal")

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "\033[0;34mℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# 确认提示
confirm() {
  warning "$1"
  echo -n "继续? (y/N): "
  read -r response
  case "$response" in [yY]) return 0 ;; *) exit 0 ;; esac
}

# 备份本地文件
backup_local() {
  local backup_dir
  backup_dir="$LPATH/backups/$(date +%Y%m%d_%H%M%S)"
  local has_files=false

  for file in "${DB_FILES[@]}"; do
    if [ -f "$LPATH/$file" ]; then
      has_files=true
      break
    fi
  done

  if [ "$has_files" = true ]; then
    info "备份本地数据库文件..."
    mkdir -p "$backup_dir"
    for file in "${DB_FILES[@]}"; do
      if [ -f "$LPATH/$file" ]; then
        cp "$LPATH/$file" "$backup_dir/"
        success "已备份: $file"
      fi
    done
    success "备份完成: $backup_dir"
  fi
}

# 主函数
main() {
  info "开始SQLite数据库同步..."
  info "远程: $RUSER@$RHOST:$RPATH (REMOTE_DIR_NAME=$REMOTE_DIR_NAME)"
  info "本地: $LPATH"
  echo

  # 检查连接
  if ! ssh "$RUSER@$RHOST" "echo 连接测试" >/dev/null 2>&1; then
    error "无法连接远程服务器"
    exit 1
  fi
  success "远程连接正常"

  # 检查远程主数据库文件
  # shellcheck disable=SC2029
  if ! ssh "$RUSER@$RHOST" "[ -f '$RPATH/bot.db' ]"; then
    error "远程没有bot.db文件"
    exit 1
  fi
  success "远程数据库文件存在"

  # 直接开始同步,不需要确认
  info "即将从远程下载数据库文件覆盖本地"

  # 备份本地文件
  backup_local

  # 创建本地目录
  mkdir -p "$LPATH"

  # 删除本地旧文件
  for file in "${DB_FILES[@]}"; do
    if [ -f "$LPATH/$file" ]; then
      rm -f "$LPATH/$file"
      info "删除本地旧文件: $file"
    fi
  done

  # 同步文件 - 确保原子性操作
  info "开始下载数据库文件..."

  # 方法1: 先将远程数据库检查点化,确保WAL内容写入主文件
  info "请求远程数据库检查点..."
  # shellcheck disable=SC2029
  ssh "$RUSER@$RHOST" "cd '$RPATH' && sqlite3 bot.db 'PRAGMA wal_checkpoint(FULL);' 2>/dev/null || true"

  # 方法2: 同步所有相关文件到临时目录,然后原子性移动
  temp_dir=$(mktemp -d)
  info "使用临时目录: $temp_dir"

  rsync -avz --include="bot.db*" --exclude="*" "$RUSER@$RHOST:$RPATH/" "$temp_dir/"

  # 原子性移动到目标位置
  for file in "${DB_FILES[@]}"; do
    if [ -f "$temp_dir/$file" ]; then
      mv "$temp_dir/$file" "$LPATH/"
      success "同步完成: $file"
    fi
  done

  # 清理临时目录
  rm -rf "$temp_dir"

  # 验证结果
  if [ -f "$LPATH/bot.db" ]; then
    success "数据库同步完成"
    info "文件列表:"
    for file in "${DB_FILES[@]}"; do
      if [ -f "$LPATH/$file" ]; then
        size=$(stat -f%z "$LPATH/$file" 2>/dev/null || echo "0")
        success "  $file (${size} bytes)"
      else
        info "  $file (不存在)"
      fi
    done
  else
    error "同步失败: 本地没有bot.db文件"
    exit 1
  fi
}

main "$@"
