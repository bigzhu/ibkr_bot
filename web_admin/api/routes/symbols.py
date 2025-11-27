"""
交易对管理相关的 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from database.crud import delete_trading_symbol
from database.db_config import get_db_manager

# 使用现有的数据库管理器
db_manager = get_db_manager()
from ..models.config import (
    AddTradingSymbolRequest,
    SymbolValidationResponse,
    TradingSymbolListResponse,
    TradingSymbolResponse,
    UpdateTradingSymbolRequest,
)
from ..models.symbol_factories import (
    create_operation_result_from_db_result,
)

# 移除不再使用的 binance_validator 依赖
from .auth import get_current_user

# 创建路由器
router = APIRouter(prefix="/symbols", tags=["交易对管理"])

# HTTP Bearer 认证
security = HTTPBearer()


@router.get(
    "/list",
    response_model=TradingSymbolListResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_all_symbols():
    """
    获取所有交易对

    返回所有配置的交易对列表
    """
    # 使用数据库辅助函数获取交易对数据
    from ..utils.database_helpers import get_all_trading_symbols

    symbols = get_all_trading_symbols()

    return {
        "success": True,
        "message": f"获取到 {len(symbols)} 个交易对",
        "symbols": symbols,
    }


from typing import Any


async def _fetch_binance_symbol_data(symbol: str) -> dict[str, Any]:
    """获取币安交易对详细信息

    如果交易对在币安不存在,抛出ValueError异常
    """
    # 导入币安API模块
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    from ibkr_api.common import get_configured_client
    from ibkr_api.get_exchange_info import get_complete_symbol_data

    # 获取币安客户端
    client = get_configured_client()

    if not client:
        raise ValueError("币安API未配置,无法验证交易对")

    logger.info(f"正在从币安API获取 {symbol} 的详细信息...")
    # 使用会抛出异常的版本,而不是安全版本
    binance_data = get_complete_symbol_data(client, symbol)
    logger.info(f"成功获取 {symbol} 的币安数据")
    return binance_data


async def _parse_symbol_assets(symbol: str) -> tuple[str, str]:
    """解析交易对的base_asset和quote_asset"""
    symbol_upper = symbol.upper()
    # 更智能的base_asset提取
    if symbol_upper.endswith("USDT"):
        base_asset = symbol_upper[:-4]
        quote_asset = "USDT"
    elif symbol_upper.endswith("USDC"):
        base_asset = symbol_upper[:-4]
        quote_asset = "USDC"
    elif symbol_upper.endswith("BTC"):
        base_asset = symbol_upper[:-3]
        quote_asset = "BTC"
    elif symbol_upper.endswith("ETH"):
        base_asset = symbol_upper[:-3]
        quote_asset = "ETH"
    else:
        # 默认假设为USDT交易对
        base_asset = symbol_upper[:-4] if len(symbol_upper) > 4 else symbol_upper
        quote_asset = "USDT"

    return base_asset, quote_asset


async def _prepare_symbol_insert_data(
    request: AddTradingSymbolRequest, binance_data: dict[str, Any] | None
) -> tuple[tuple[object, ...], str]:
    """准备交易对插入数据库的数据和SQL"""
    if binance_data:
        # 使用币安API获取的完整数据
        insert_data = (
            binance_data["symbol"],
            binance_data["base_asset"],
            binance_data["quote_asset"],
            binance_data["is_active"],
            request.description or binance_data["description"],
            request.max_fund or binance_data["max_fund"],
            binance_data["base_asset_precision"],
            binance_data["quote_asset_precision"],
            binance_data["current_price"],
            binance_data["volume_24h"],
            binance_data["volume_24h_quote"],
            binance_data["price_change_24h"],
            binance_data["high_24h"],
            binance_data["low_24h"],
            binance_data["min_qty"],
            binance_data["max_qty"],
            binance_data["step_size"],
            binance_data["min_notional"],
            binance_data["min_price"],
            binance_data["max_price"],
            binance_data["tick_size"],
            binance_data["last_updated_price"],
        )

        insert_sql = """INSERT INTO trading_symbols
               (symbol, base_asset, quote_asset, is_active, description, max_fund,
                base_asset_precision, quote_asset_precision, current_price, volume_24h,
                volume_24h_quote, price_change_24h, high_24h, low_24h, min_qty, max_qty,
                step_size, min_notional, min_price, max_price, tick_size, last_updated_price)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    else:
        # 使用基础信息创建(回退方案)
        symbol_upper = request.symbol.upper()
        base_asset, quote_asset = await _parse_symbol_assets(request.symbol)

        insert_data = (
            symbol_upper,
            base_asset,
            quote_asset,
            True,
            request.description or f"{base_asset}/{quote_asset} 交易对",
            request.max_fund or 0,
        )

        insert_sql = """INSERT INTO trading_symbols
               (symbol, base_asset, quote_asset, is_active, description, max_fund)
               VALUES (?, ?, ?, ?, ?, ?)"""

    return insert_data, insert_sql


async def _create_default_timeframe_configs(symbol: str) -> int:
    """为新添加的交易对创建默认时间周期配置"""
    logger.info(f"开始为交易对 {symbol} 创建时间周期配置...")

    # 定义默认创建的时间周期
    from shared.timeframes import DEFAULT_CONFIG_TIMEFRAMES as timeframes

    default_config = {
        "demark_buy": 1,
        "demark_sell": 1,
        "daily_max_percentage": 24,
        "demark_percentage_coefficient": 1.4,
        "minimum_profit_percentage": 0.44,
        "monitor_delay": 1,
        "oper_mode": "all",
        "is_active": False,
    }

    logger.info(f"准备创建 {len(timeframes)} 个时间周期配置: {timeframes}")

    # 为每个时间周期创建配置
    success_count = 0
    for timeframe in timeframes:
        logger.debug(f"正在创建 {symbol} - {timeframe} 配置...")
        # 创建时间周期配置 - 使用直接的SQL插入
        with db_manager.transaction() as conn:
            cursor = conn.execute(
                """INSERT INTO symbol_timeframe_configs
                   (trading_symbol, kline_timeframe, demark_buy, demark_sell,
                    daily_max_percentage, demark_percentage_coefficient, minimum_profit_percentage,
                    monitor_delay, oper_mode, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    symbol,
                    timeframe,
                    int(default_config["demark_buy"]),
                    int(default_config["demark_sell"]),
                    int(default_config["daily_max_percentage"]),
                    float(default_config["demark_percentage_coefficient"]),
                    float(default_config["minimum_profit_percentage"]),
                    float(default_config["monitor_delay"]),
                    str(default_config["oper_mode"]),
                    bool(default_config["is_active"]),
                ),
            )
            config_id = cursor.lastrowid
            raw_config_result = {
                "success": True,
                "message": f"成功创建配置 {timeframe}",
                "data": {"id": config_id, "timeframe": timeframe},
            }

        # 使用类型安全的结果处理
        config_result = create_operation_result_from_db_result(
            raw_config_result, f"创建{timeframe}配置"
        )
        logger.debug(f"创建 {timeframe} 配置结果: {config_result}")
        if config_result["success"]:
            success_count += 1

    logger.info(
        f"成功为交易对 {symbol} 创建了 {success_count}/{len(timeframes)} 个时间周期配置"
    )
    return success_count


@router.post(
    "/add",
    response_model=TradingSymbolResponse,
    dependencies=[Depends(get_current_user)],
)
async def add_symbol(request: AddTradingSymbolRequest):
    """添加新的交易对

    先从币安API验证交易对是否存在,然后添加到数据库
    """
    # 验证币安交易对存在性
    try:
        binance_data = await _fetch_binance_symbol_data(request.symbol)
    except ValueError as e:
        logger.error(f"添加交易对失败: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"交易对 {request.symbol} 在币安不存在,请检查交易对名称",
        ) from e

    # 准备插入数据
    insert_data, insert_sql = await _prepare_symbol_insert_data(request, binance_data)

    # 添加到数据库
    with db_manager.transaction() as conn:
        cursor = conn.execute(insert_sql, insert_data)
        symbol_id = cursor.lastrowid
        raw_result = {
            "success": True,
            "message": f"成功添加交易对 {request.symbol}"
            + (" (含币安详细信息)" if binance_data else " (基础信息)"),
            "data": {
                "id": symbol_id,
                "symbol": request.symbol,
                "has_binance_data": bool(binance_data),
            },
        }

    # 使用类型安全的操作结果处理
    result = create_operation_result_from_db_result(raw_result, "添加交易对")

    # 如果交易对添加成功,自动创建时间周期的默认配置
    if result["success"]:
        _ = await _create_default_timeframe_configs(request.symbol)
    else:
        logger.warning(f"交易对 {request.symbol} 添加失败,跳过创建时间周期配置")

    return TradingSymbolResponse(
        success=result["success"], message=result["message"], data=result.get("data")
    )


@router.put(
    "/{symbol_id}",
    response_model=TradingSymbolResponse,
    dependencies=[Depends(get_current_user)],
)
async def update_symbol(symbol_id: int, request: UpdateTradingSymbolRequest):
    """
    更新交易对信息

    可以更新激活状态和描述信息
    """
    # 更新交易对 - 使用直接的SQL更新
    with db_manager.transaction() as conn:
        cursor = conn.execute(
            """UPDATE trading_symbols
               SET is_active = ?, description = ?, max_fund = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (
                request.is_active if request.is_active is not None else True,
                request.description or "",
                request.max_fund or 0,
                symbol_id,
            ),
        )

        if cursor.rowcount > 0:
            # 获取更新后的记录
            result_cursor = conn.execute(
                "SELECT id, symbol, is_active, description, max_fund FROM trading_symbols WHERE id = ?",
                (symbol_id,),
            )
            updated_record = result_cursor.fetchone()

            raw_result = {
                "success": True,
                "message": f"成功更新交易对 (ID: {symbol_id})",
                "data": dict(updated_record) if updated_record else None,
            }
        else:
            raw_result = {
                "success": False,
                "message": f"未找到ID为 {symbol_id} 的交易对",
                "data": None,
            }

    # 使用类型安全的操作结果处理
    result = create_operation_result_from_db_result(raw_result, "更新交易对")

    return TradingSymbolResponse(
        success=result["success"], message=result["message"], data=result["data"]
    )


@router.delete(
    "/{symbol_id}",
    response_model=TradingSymbolResponse,
    dependencies=[Depends(get_current_user)],
)
async def delete_symbol(symbol_id: int):
    """
    删除交易对

    从数据库中删除指定的交易对
    """
    raw_result = delete_trading_symbol(db_manager, symbol_id)

    # 使用类型安全的操作结果处理
    result = create_operation_result_from_db_result(raw_result, "删除交易对")

    return TradingSymbolResponse(
        success=result["success"], message=result["message"], data=result["data"]
    )


@router.post(
    "/validate/{symbol}",
    response_model=SymbolValidationResponse,
    dependencies=[Depends(get_current_user)],
)
async def validate_symbol(symbol: str):
    """
    验证单个交易对 (已禁用)

    此功能已禁用,因为不再使用 Binance API
    """
    # Echo symbol to avoid unused-parameter warning and provide context
    return SymbolValidationResponse(
        success=False,
        message=f"交易对验证功能已禁用: {symbol}",
        data=None,
        error_code="FEATURE_DISABLED",
        error_details="不再使用 Binance API 验证",
    )


@router.post("/refresh/{symbol_id}")
async def refresh_symbol_data(
    symbol_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """刷新单个交易对的数据 (已禁用)"""
    from .auth import verify_token

    _ = verify_token(credentials)
    # Include symbol_id for context to avoid unused-parameter warning
    return TradingSymbolResponse(
        success=False, message=f"数据刷新功能已禁用: {symbol_id}", data=None
    )


@router.get(
    "/{symbol}/signal-strength",
    dependencies=[Depends(get_current_user)],
)
async def get_symbol_signal_strength(symbol: str):
    """
    获取交易对的1m信号强度

    返回指定交易对在1m时间周期的最新信号强度值
    """
    # 获取该交易对1m时间周期的最新交易日志
    from ..utils.database_helpers import get_trading_logs

    latest_logs = get_trading_logs(symbol=symbol, timeframe="1m", limit=1, offset=0)

    logger.info(
        f"交易对 {symbol} 查询到 {len(latest_logs) if latest_logs else 0} 条1m日志记录"
    )

    if latest_logs and len(latest_logs) > 0:
        latest_log = latest_logs[0]
        logger.info(f"交易对 {symbol} 最新1m日志: {latest_log}")

        # 如果日志有信号强度数据,返回
        if "signal_value" in latest_log and latest_log["signal_value"] is not None:
            signal_value = latest_log["signal_value"]
            logger.info(f"交易对 {symbol} 返回信号强度: {signal_value}")
            return {
                "success": True,
                "message": f"获取 {symbol} 信号强度成功",
                "data": {
                    "symbol": symbol,
                    "signal_value": signal_value,
                    "timeframe": "1m",
                    "timestamp": latest_log.get("run_time"),
                },
            }
        else:
            logger.info(f"交易对 {symbol} 1m日志中没有有效的信号强度数据")
            return {
                "success": True,
                "message": f"交易对 {symbol} 暂无信号强度数据",
                "data": {
                    "symbol": symbol,
                    "signal_value": None,
                    "timeframe": "1m",
                    "timestamp": None,
                },
            }
    else:
        logger.info(f"交易对 {symbol} 没有找到1m交易日志")
        return {
            "success": True,
            "message": f"交易对 {symbol} 暂无1m交易日志",
            "data": {
                "symbol": symbol,
                "signal_value": None,
                "timeframe": "1m",
                "timestamp": None,
            },
        }


@router.post("/refresh-all")
async def refresh_all_symbols(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """批量刷新所有交易对的数据 (已禁用)"""
    from .auth import verify_token

    _ = verify_token(credentials)
    return TradingSymbolResponse(
        success=False, message="批量数据刷新功能已禁用", data=None
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("📈 交易对路由模块")
    logger.info("提供交易对管理相关的 API 端点")
    logger.info("- GET /api/v1/symbols - 获取交易对列表")
    logger.info("- POST /api/v1/symbols - 添加新交易对")
    logger.info("- PUT /api/v1/symbols/{symbol} - 更新交易对配置")
    logger.info("- DELETE /api/v1/symbols/{symbol} - 删除交易对")
    logger.info("- POST /api/v1/symbols/refresh - 刷新交易对数据(已禁用)")
    logger.info("- POST /api/v1/symbols/refresh-all - 批量刷新(已禁用)")
