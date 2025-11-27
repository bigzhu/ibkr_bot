#!/usr/bin/env bash

# 同步脚本公共库: 统一的依赖检查,远程目录管理与 rsync 包装

if [ -n "${_SYNC_LIB_SOURCED:-}" ]; then
    return 0
fi
_SYNC_LIB_SOURCED=1

SCRIPT_SYNC_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib_remote_env.sh
. "$SCRIPT_SYNC_LIB_DIR/lib_remote_env.sh"

ensure_scripts_executable() {
    if [ "$#" -eq 0 ]; then
        return
    fi
    local script_path
    for script_path in "$@"; do
        if [ ! -f "$script_path" ]; then
            echo "❌ 错误: 未找到脚本 $script_path"
            exit 1
        fi
        chmod +x "$script_path"
    done
}

ensure_remote_directory() {
    local remote_path="$1"
    if [ -z "$remote_path" ]; then
        echo "❌ 错误: ensure_remote_directory 需要远程路径" >&2
        exit 1
    fi
    ssh "$RUSER@$RHOST" "mkdir -p '$remote_path'"
}

rsync_with_options() {
    local source_path="$1"
    local destination="$2"
    shift 2
    local rsync_args=(-e "ssh" -avz)
    if [ "$#" -gt 0 ]; then
        rsync_args+=("$@")
    fi
    rsync "${rsync_args[@]}" "$source_path" "$destination"
}

# 后端同步需要排除的文件与目录
BACKEND_RSYNC_EXCLUDES=(
    "--exclude=pg_data"           # 数据库数据目录
    "--exclude=*.dump"            # 数据库转储文件
    "--exclude=*.db"              # SQLite数据库文件
    "--exclude=*.db-shm"          # SQLite共享内存文件
    "--exclude=*.db-wal"          # SQLite预写日志文件
    "--exclude=var/data/"         # 服务器数据目录
    "--exclude=*.key"             # 密钥文件
    "--exclude=*.pem"             # SSL证书文件
    "--exclude=*.crt"             # 证书文件
    "--exclude=*.p12"             # PKCS12文件
    "--exclude=.env"              # 环境变量文件
    "--exclude=.env.*"            # 环境变量文件
    "--exclude=*.swp"             # Vim临时文件
    "--exclude=*.tmp"             # 临时文件
    "--exclude=*.temp"            # 临时文件
    "--exclude=.DS_Store"         # macOS系统文件
    "--exclude=Thumbs.db"         # Windows缩略图文件
    "--exclude=*.log"             # 日志文件
    "--exclude=logs/"             # 日志目录
    "--exclude=.venv"             # 虚拟环境目录
    "--exclude=venv/"             # 虚拟环境目录
    "--exclude=*.pyc"             # Python编译缓存
    "--exclude=__pycache__"       # Python缓存目录
    "--exclude=*.egg-info"        # Python包信息
    "--exclude=build/"            # build目录
    "--exclude=dist/"             # dist目录
    "--exclude=src/cli/build/"    # CLI build目录
    "--exclude=.pytest_cache"     # pytest缓存
    "--exclude=.mypy_cache"       # mypy缓存
    "--exclude=.ruff_cache"       # Ruff缓存
    "--exclude=htmlcov"           # 覆盖率报告
    "--exclude=.coverage"         # 覆盖率文件
    "--exclude=.tox"              # tox环境
    "--exclude=web_admin/frontend/" # 前端代码
    "--exclude=.git"              # Git目录
    "--exclude=.gitignore"        # Git忽略文件
    "--exclude=.claude"           # Claude配置
    "--exclude=.vscode"           # VSCode配置
    "--exclude=.idea"             # IDEA配置
    "--exclude=*.pid"             # 进程ID文件
    "--exclude=*.sock"            # Socket文件
    "--exclude=gunicorn.pid"      # Gunicorn进程文件
)
