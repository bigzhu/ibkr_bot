"""
配置管理相关的 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from loguru import logger
from pydantic import BaseModel

from database.db_config import get_db_manager

# 使用现有的数据库管理器
db_manager = get_db_manager()
from ..models.config import (
    ApiValidationRequest,
    ApiValidationResponse,
    BinanceConfigRequest,
    BinanceConfigResponse,
    BinanceStatusData,
    BinanceStatusResponse,
    ConfigListResponse,
    ConfigUpdateRequest,
    ConfigUpdateResponse,
)

# 移除不再使用的 binance_validator 依赖
from .auth import get_current_user

# 创建路由器
router = APIRouter(prefix="/config", tags=["配置管理"])

# HTTP Bearer 认证
security = HTTPBearer()


@router.get(
    "/list",
    response_model=ConfigListResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_all_configs() -> ConfigListResponse:
    """
    获取所有配置项

    返回所有业务配置项的列表
    """
    from ..utils.database_helpers import get_all_system_configs

    configs = get_all_system_configs()

    return ConfigListResponse(success=True, message="获取配置列表成功", configs=configs)


@router.post(
    "/binance/validate",
    response_model=ApiValidationResponse,
    dependencies=[Depends(get_current_user)],
)
async def validate_ibkr_api(request: ApiValidationRequest) -> ApiValidationResponse:
    """
    验证Binance API连接 - 暂时禁用
    """
    # Access fields to avoid unused-parameter warning, without logging secrets
    api_key_len = len(request.api_key) if request.api_key else 0
    _ = api_key_len  # explicit use without exposing secrets
    return ApiValidationResponse(
        success=False,
        message="Binance API验证功能暂未实现",
        data=None,
        error_code="NOT_IMPLEMENTED",
        error_details="需要实现Binance API验证功能",
    )


@router.post(
    "/binance/save",
    response_model=BinanceConfigResponse,
    dependencies=[Depends(get_current_user)],
)
async def save_binance_config(request: BinanceConfigRequest) -> BinanceConfigResponse:
    """
    保存Binance API配置到数据库 - 异常直接向上传播
    """
    from ..utils.database_helpers import set_system_config

    # 保存API配置到系统配置表 - 异常直接向上传播
    set_system_config("MAIN_BINANCE_API_KEY", request.api_key)
    set_system_config("MAIN_BINANCE_SECRET_KEY", request.secret_key)

    return BinanceConfigResponse(
        success=True,
        message="Binance API配置保存成功",
        validation_result=None,
    )


@router.post(
    "/update",
    response_model=ConfigUpdateResponse,
    dependencies=[Depends(get_current_user)],
)
async def update_configs(request: ConfigUpdateRequest) -> ConfigUpdateResponse:
    """
    批量更新配置项

    更新多个配置项的值
    """
    updated_count = 0

    from ..utils.database_helpers import set_system_config

    for config_key, config_value in request.configs.items():
        set_system_config(config_key, config_value)
        updated_count += 1

    return ConfigUpdateResponse(
        success=True,
        message=f"成功更新 {updated_count} 个配置项",
        updated_count=updated_count,
        failed_configs=None,
    )


@router.get(
    "/binance/status",
    response_model=BinanceStatusResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_binance_status() -> BinanceStatusResponse:
    """
    获取当前Binance API配置状态

    返回API配置状态和当前值(用于表单回显)
    """
    # 获取主网配置,异常向上传播(fail-fast原则)
    from ..utils.database_helpers import get_system_config

    api_key = get_system_config("MAIN_BINANCE_API_KEY") or ""
    secret_key = get_system_config("MAIN_BINANCE_SECRET_KEY") or ""

    has_api_key = bool(api_key and api_key.strip())
    has_secret_key = bool(secret_key and secret_key.strip())
    is_configured = has_api_key and has_secret_key

    # 如果已配置,返回部分显示的值用于表单回显
    display_api_key = ""
    display_secret_key = ""

    if has_api_key:
        # 显示前4位和后4位,中间用*号代替
        if len(api_key) > 8:
            display_api_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
        else:
            display_api_key = "*" * len(api_key)

    if has_secret_key:
        # 密钥显示为固定长度的*号
        display_secret_key = "*" * 16

    status_data = BinanceStatusData(
        has_api_key=has_api_key,
        has_secret_key=has_secret_key,
        is_configured=is_configured,
        api_key=display_api_key,
        secret_key=display_secret_key,
        environment_name="主网",
    )

    return BinanceStatusResponse(success=True, data=status_data)


class LogLevelRequest(BaseModel):
    """日志级别设置请求模型"""

    log_level: str


class LogLevelResponse(BaseModel):
    """日志级别响应模型"""

    success: bool
    message: str
    log_level: str | None = None


@router.get(
    "/log-level",
    response_model=LogLevelResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_log_level() -> LogLevelResponse:
    """
    获取当前日志级别

    返回当前系统日志级别配置
    """
    # 异常向上传播(fail-fast原则)
    from ..utils.database_helpers import get_system_config

    log_level = get_system_config("LOG_LEVEL") or "INFO"

    return LogLevelResponse(
        success=True, message="获取日志级别成功", log_level=log_level
    )


@router.put(
    "/log-level",
    response_model=LogLevelResponse,
    dependencies=[Depends(get_current_user)],
)
async def update_log_level(request: LogLevelRequest) -> LogLevelResponse:
    """
    更新日志级别

    设置系统日志级别并立即生效
    """
    # 验证日志级别是否有效
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if request.log_level.upper() not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的日志级别: {request.log_level}.有效级别: {', '.join(valid_levels)}",
        )

    # 保存到数据库
    from ..utils.database_helpers import set_system_config

    set_system_config("LOG_LEVEL", request.log_level.upper())

    # 立即更新当前进程的日志级别
    import sys

    logger.remove()
    _ = logger.add(
        sys.stdout,
        level=request.log_level.upper(),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
    )

    logger.info(f"📋 日志级别已更新为: {request.log_level.upper()}")

    return LogLevelResponse(
        success=True,
        message=f"日志级别已成功更新为 {request.log_level.upper()}",
        log_level=request.log_level.upper(),
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("⚙️ 配置路由模块")
    logger.info("提供系统配置相关的 API 端点")
    logger.info("- GET /api/v1/config/binance - 获取Binance配置")
    logger.info("- PUT /api/v1/config/binance - 更新Binance配置")
    logger.info("- PUT /api/v1/config/log-level - 更新日志级别")
