"""
FastAPI 纯API应用 - 不启动定时任务调度器
仅提供Web API服务,不运行后台定时任务
支持 WebSocket 实时推送
"""

from typing import Any

from fastapi import FastAPI, WebSocket
from loguru import logger

# 统一双重用途模块导入处理(仅处理 ImportError)
try:
    from shared.path_utils import add_project_root_to_path
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from shared.path_utils import add_project_root_to_path

add_project_root_to_path()

from shared.logger_utils import setup_web_admin_logger

from .routes.auth import router as auth_router
from .routes.binance_filled_orders import router as binance_order_filler_router
from .routes.config import router as config_router
from .routes.filled_orders import router as order_filler_router
from .routes.internal_events import router as internal_events_router
from .routes.profit_analysis_new import router as profit_analysis_new_router
from .routes.symbols import router as symbols_router
from .routes.timeframe_configs import router as timeframe_configs_router
from .routes.trading_logs import router as trading_logs_router
from .websocket import websocket_logs_endpoint

# 应用启动时配置日志
setup_web_admin_logger()

# 创建 FastAPI 应用
app = FastAPI(
    title="DeMark 交易机器人 Web API",
    description="提供配置管理的API接口(不包含定时任务)",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc
)


# 注册路由
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(config_router, prefix="/api/v1")
app.include_router(symbols_router, prefix="/api/v1")
app.include_router(timeframe_configs_router, prefix="/api/v1")
app.include_router(trading_logs_router, prefix="/api/v1")
app.include_router(order_filler_router, prefix="/api/v1", tags=["成交订单管理"])
app.include_router(
    binance_order_filler_router, prefix="/api/v1", tags=["币安成交订单管理"]
)
app.include_router(
    internal_events_router, prefix="/api/v1/internal/events", tags=["内部事件通知"]
)
app.include_router(profit_analysis_new_router, prefix="/api", tags=["盈利分析-新版"])


# WebSocket 路由
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket) -> None:
    """交易日志 WebSocket 实时推送端点"""
    await websocket_logs_endpoint(websocket)


@app.get("/")
async def root() -> dict[str, Any]:
    """API根路径 - 返回服务信息"""
    return {
        "message": "DeMark 交易机器人 Web API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health",
        "websocket": "/ws/logs",
    }


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "DeMark Web API (API Only)",
        "version": "1.0.0",
        "scheduler_enabled": False,
    }


@app.get("/api/v1/scheduler/status")
async def get_scheduler_status_api() -> dict[str, Any]:
    """获取任务调度器状态 - API Only模式下返回未启用状态"""
    return {
        "success": True,
        "data": {
            "enabled": False,
            "running": False,
            "message": "调度器未启用 - 当前为纯API模式",
            "jobs": [],
        },
    }


if __name__ == "__main__":
    import os
    import sys
    from pathlib import Path

    import uvicorn

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    # 端口从环境读取,与 start_api.py 一致
    env_port = os.getenv("WEB_ADMIN_PORT")
    remote = os.getenv("REMOTE_DIR_NAME", "").strip().lower()
    default_port = (
        os.getenv("LEAD_API_PORT", "8001")
        if remote == "lead"
        else os.getenv("BOT_API_PORT", "8000")
    )
    try:
        port = int(env_port or default_port)
    except ValueError:
        port = 8000

    logger.info("🚀 启动 Web Admin API 服务")
    logger.info(f"📁 项目根目录: {project_root}")
    logger.info(f"📖 API 文档: http://localhost:{port}/api/docs")

    uvicorn.run(
        "web_admin.api.app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
