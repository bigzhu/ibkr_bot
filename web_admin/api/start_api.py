#!/usr/bin/env python3
"""
Web Admin API 启动脚本
使用 p start_api 来启动服务
"""

import importlib
import os
import sys
from contextlib import suppress
from pathlib import Path

import uvicorn

# 导入配置模块以自动加载项目根目录下的 .env
# 仅导入即可触发环境变量加载逻辑
with suppress(Exception):
    _ = importlib.import_module("shared.config")

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # 清理不必要的启动提示日志
    # 校验 REMOTE_DIR_NAME 必填
    remote_dir_raw = os.getenv("REMOTE_DIR_NAME")
    if not remote_dir_raw or not remote_dir_raw.strip():
        print(
            "ERROR: REMOTE_DIR_NAME is not set. Please set it to 'bot' or 'lead' in .env or environment.",
            file=sys.stderr,
        )
        sys.exit(1)
    remote_dir = remote_dir_raw.strip().lower()
    if remote_dir not in {"bot", "lead"}:
        print(
            f"ERROR: REMOTE_DIR_NAME must be 'bot' or 'lead'. Current: {remote_dir!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 端口优先级:
    # 1) WEB_ADMIN_PORT (若显式指定)
    # 2) REMOTE_DIR_NAME=lead -> LEAD_API_PORT(默认8001)
    #    REMOTE_DIR_NAME=bot  -> BOT_API_PORT(默认8000)
    env_port = os.getenv("WEB_ADMIN_PORT")
    default_port_str = (
        os.getenv("LEAD_API_PORT", "8001")
        if remote_dir == "lead"
        else os.getenv("BOT_API_PORT", "8000")
    )
    port_str = env_port or default_port_str
    try:
        port = int(port_str)
    except ValueError:
        port = 8000
    uvicorn.run(
        "web_admin.api.app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
