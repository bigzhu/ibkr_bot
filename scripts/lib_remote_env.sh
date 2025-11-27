#!/usr/bin/env bash

# 共享的远程环境加载工具,供同步与部署脚本引用

if [ -n "${_REMOTE_ENV_LIB_SOURCED:-}" ]; then
    return 0
fi
_REMOTE_ENV_LIB_SOURCED=1

SCRIPT_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${PROJECT_ROOT:="$(cd "$SCRIPT_LIB_DIR/.." && pwd)"}"

load_remote_env() {
    # 允许调用方预先设置 REMOTE_DIR_NAME 覆盖 .env
    local preserved_remote=""
    local has_preserved_remote=0
    if [ -n "${REMOTE_DIR_NAME+x}" ]; then
        preserved_remote="$REMOTE_DIR_NAME"
        has_preserved_remote=1
    fi

    if [ -f "$PROJECT_ROOT/.env" ]; then
        # shellcheck disable=SC1090
        set -a; . "$PROJECT_ROOT/.env"; set +a
    fi

    if [ "$has_preserved_remote" -eq 1 ]; then
        REMOTE_DIR_NAME="$preserved_remote"
    fi

    export RUSER=${RUSER:-bigzhu}
    export RHOST=${RHOST:-bandwagonhost.bigzhu.net}
}

require_remote_dir() {
    if [ -z "${REMOTE_DIR_NAME:-}" ]; then
        echo "ERROR: REMOTE_DIR_NAME is not set. Please set it to 'bot' or 'lead'."
        exit 1
    fi

    case "$REMOTE_DIR_NAME" in
        bot|lead) ;;
        *)
            echo "ERROR: REMOTE_DIR_NAME must be 'bot' or 'lead'. Current: ${REMOTE_DIR_NAME}"
            exit 1
            ;;
    esac
}

remote_base_path() {
    require_remote_dir
    printf "/home/%s/%s" "$RUSER" "$REMOTE_DIR_NAME"
}
