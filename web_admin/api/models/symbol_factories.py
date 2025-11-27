"""
Web API symbols相关工厂函数
提供类型安全的数据库记录转换为API模型的工厂方法
"""

from typing import Any, cast

from loguru import logger

from .config import ApiValidationResponse, TradingSymbol


def strict_int(value: Any, field_name: str, allow_none: bool = False) -> int | None:
    """严格的int转换,金融数据不允许模糊处理"""
    if value is None:
        if allow_none:
            return None
        raise ValueError(f"金融数据字段 {field_name} 不能为空")
    return int(value)


def strict_float(
    value: Any, field_name: str, allow_none: bool = False, positive_only: bool = False
) -> float | None:
    """严格的float转换,确保数据有效性"""
    if value is None:
        if allow_none:
            return None
        raise ValueError(f"数据字段 {field_name} 不能为空")
    if isinstance(value, str) and (not value or value.strip() == ""):
        if allow_none:
            return None
        raise ValueError(f"数据字段 {field_name} 不能为空字符串")

    float_val = float(value)
    if positive_only and float_val <= 0:
        raise ValueError(f"数据字段 {field_name} 必须大于0")
    elif not positive_only and float_val < 0:
        raise ValueError(f"数据字段 {field_name} 不能为负数")
    return float_val


def strict_string(value: Any, field_name: str, allow_none: bool = False) -> str | None:
    """严格的字符串验证"""
    if value is None:
        if allow_none:
            return None
        raise ValueError(f"关键字段 {field_name} 不能为空")
    return str(value)


def strict_bool(value: Any, field_name: str) -> bool:
    """严格的bool验证"""
    if value is None:
        raise ValueError(f"关键字段 {field_name} 不能为空")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    if isinstance(value, int):
        return bool(value)
    raise ValueError(f"字段 {field_name} 无法转换为布尔值: {value}")


def _validate_required_fields(symbol_data: dict[str, Any]) -> None:
    """验证必需字段的存在性和非空性"""
    required_fields = [
        "id",
        "symbol",
        "base_asset",
        "quote_asset",
        "is_active",
        "description",
        "created_at",
        "updated_at",
    ]
    missing_fields = [field for field in required_fields if field not in symbol_data]

    if missing_fields:
        error_msg = f"[严重错误]交易对数据缺少关键字段: {missing_fields}"
        logger.critical(f"{error_msg}, 完整数据: {symbol_data}")
        raise ValueError(f"{error_msg} - 金融系统不能处理不完整数据")

    none_fields = [field for field in required_fields if symbol_data[field] is None]
    if none_fields:
        error_msg = f"[严重错误]交易对关键字段为空: {none_fields}"
        logger.critical(f"{error_msg}, 完整数据: {symbol_data}")
        raise ValueError(f"{error_msg} - 金融系统不允许关键字段为空")


def _safe_float_field(
    symbol_data: dict[str, Any], field: str, positive_only: bool = False
) -> float | None:
    """安全地获取可选的float字段值"""
    value = symbol_data.get(field)
    return (
        strict_float(value, field, allow_none=True, positive_only=positive_only)
        if value is not None
        else None
    )


def _safe_int_field(symbol_data: dict[str, Any], field: str) -> int | None:
    """安全地获取可选的int字段值"""
    value = symbol_data.get(field)
    return strict_int(value, field, allow_none=True) if value is not None else None


def create_trading_symbol_from_db_data(symbol_data: dict[str, Any]) -> TradingSymbol:
    """
    从数据库数据创建交易对模型,严格数据验证(金融系统fail-fast原则)

    Args:
        symbol_data: 数据库查询返回的字典数据

    Returns:
        TradingSymbol: 严格验证的交易对模型

    Raises:
        ValueError: 当数据验证失败或字段缺失时(金融系统必须立即中断)
        ValidationError: 当Pydantic验证失败时
    """
    _validate_required_fields(symbol_data)

    symbol_id = strict_int(symbol_data["id"], "id")
    if symbol_id is None:
        raise ValueError("TradingSymbol id cannot be None")

    return TradingSymbol(
        id=symbol_id,
        symbol=strict_string(symbol_data.get("symbol"), "symbol") or "",
        base_asset=strict_string(symbol_data.get("base_asset"), "base_asset") or "",
        quote_asset=strict_string(symbol_data.get("quote_asset"), "quote_asset") or "",
        base_asset_precision=strict_int(
            symbol_data.get("base_asset_precision", 8), "base_asset_precision"
        ),
        quote_asset_precision=strict_int(
            symbol_data.get("quote_asset_precision", 8), "quote_asset_precision"
        ),
        is_active=strict_bool(symbol_data["is_active"], "is_active"),
        description=strict_string(
            symbol_data["description"], "description", allow_none=True
        ),
        current_price=_safe_float_field(symbol_data, "current_price"),
        volume_24h=_safe_float_field(symbol_data, "volume_24h"),
        volume_24h_quote=_safe_float_field(symbol_data, "volume_24h_quote"),
        price_change_24h=_safe_float_field(symbol_data, "price_change_24h"),
        high_24h=_safe_float_field(symbol_data, "high_24h", positive_only=True),
        low_24h=_safe_float_field(symbol_data, "low_24h", positive_only=True),
        min_qty=_safe_float_field(symbol_data, "min_qty"),
        max_qty=_safe_float_field(symbol_data, "max_qty"),
        step_size=_safe_float_field(symbol_data, "step_size"),
        min_notional=_safe_float_field(symbol_data, "min_notional"),
        min_price=_safe_float_field(symbol_data, "min_price"),
        max_price=_safe_float_field(symbol_data, "max_price"),
        tick_size=_safe_float_field(symbol_data, "tick_size"),
        last_updated_price=strict_string(
            symbol_data.get("last_updated_price"), "last_updated_price", allow_none=True
        ),
        max_fund=_safe_int_field(symbol_data, "max_fund"),
        created_at=strict_string(symbol_data.get("created_at"), "created_at") or "",
        updated_at=strict_string(symbol_data.get("updated_at"), "updated_at") or "",
    )


def create_trading_symbols_from_db_data(
    symbols_data: list[dict[str, Any]],
) -> list[TradingSymbol]:
    """
    批量从数据库数据创建交易对模型列表(金融系统严格模式)

    Args:
        symbols_data: 数据库查询返回的字典数据列表

    Returns:
        List[TradingSymbol]: 严格验证的交易对模型列表

    Raises:
        ValueError: 任何一个交易对数据异常都会导致整个批次失败(金融系统不能容忍异常数据)
    """
    if not symbols_data:
        logger.warning("交易对数据列表为空")
        return []

    symbols: list[TradingSymbol] = []
    for symbol_data in symbols_data:
        symbol = create_trading_symbol_from_db_data(symbol_data)
        symbols.append(symbol)

    logger.info(f"✅ 严格验证成功:{len(symbols)} 个交易对数据")
    return symbols


def create_api_validation_response_from_result(
    validation_result: dict[str, Any],
) -> ApiValidationResponse:
    """
    从验证结果字典创建API验证响应模型

    Args:
        validation_result: 币安API验证结果字典

    Returns:
        ApiValidationResponse: 类型安全的API验证响应模型
    """

    def safe_bool(value: Any, default: bool = False) -> bool:
        """安全转换为bool"""
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return default

    def safe_string(value: Any, default: str = "") -> str:
        """安全转换为字符串"""
        if value is None:
            return default
        return str(value)

    def safe_dict(
        value: Any, default: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """安全转换为字典"""
        if value is None:
            return default
        if isinstance(value, dict):
            return cast(dict[str, Any], value)
        return default

    return ApiValidationResponse(
        success=safe_bool(validation_result.get("success")),
        message=safe_string(validation_result.get("message")),
        data=safe_dict(validation_result.get("data")),
        error_code=safe_string(validation_result.get("error_code"))
        if validation_result.get("error_code")
        else None,
        error_details=safe_string(validation_result.get("error_details"))
        if validation_result.get("error_details")
        else None,
    )


def create_operation_result_from_db_result(
    db_result: dict[str, Any], operation_name: str = "操作"
) -> dict[str, Any]:
    """
    从数据库操作结果创建标准化的API响应格式

    Args:
        db_result: 数据库操作返回的结果字典
        operation_name: 操作名称,用于错误日志

    Returns:
        Dict[str, Any]: 标准化的API响应格式
    """

    def safe_bool(value: Any, default: bool = False) -> bool:
        """安全转换为bool"""
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return default

    def safe_string(value: Any, default: str = f"{operation_name}结果未知") -> str:
        """安全转换为字符串"""
        if value is None:
            return default
        return str(value)

    def safe_dict(
        value: Any, default: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """安全转换为字典"""
        if value is None:
            return default
        if isinstance(value, dict):
            return cast(dict[str, Any], value)
        # 如果不是字典类型,记录警告并返回默认值
        logger.debug(f"期待字典但获得 {type(value)}: {value}")
        return default

    return {
        "success": safe_bool(db_result.get("success")),
        "message": safe_string(db_result.get("message")),
        "data": safe_dict(db_result.get("data")),
    }


if __name__ == "__main__":
    """演示symbols工厂函数功能"""
    logger.info("🏭 Web API Symbols工厂函数演示")
    logger.info("=" * 40)

    # 测试交易对模型创建
    logger.info("1. 交易对模型创建:")
    mock_symbol_data = {
        "id": 1,
        "symbol": "ADAUSDC",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "base_asset_precision": 8,
        "quote_asset_precision": 8,
        "is_active": True,
        "description": "比特币对USDT",
        "current_price": "45000.50",
        "volume_24h": "1000.123",
        "volume_24h_quote": "45000000.0",
        "price_change_24h": "2.5",
        "high_24h": "46000.0",
        "low_24h": "44000.0",
        "min_qty": "0.00001",
        "max_qty": "10000.0",
        "step_size": "0.00001",
        "min_notional": "10.0",
        "min_price": "0.01",
        "max_price": "100000.0",
        "tick_size": "0.01",
        "last_updated_price": "2024-01-01T10:00:00Z",
        "max_fund": 1000,
        "created_at": "2024-01-01T08:00:00Z",
        "updated_at": "2024-01-01T09:00:00Z",
    }

    trading_symbol = create_trading_symbol_from_db_data(mock_symbol_data)
    logger.info(f"   - 交易对: {trading_symbol.symbol}")
    logger.info(f"   - 是否激活: {trading_symbol.is_active}")
    logger.info(f"   - 当前价格: {trading_symbol.current_price}")
    logger.info(f"   - 基础资产精度: {trading_symbol.base_asset_precision}")
    logger.info(f"   - 最大资金: {trading_symbol.max_fund}")

    # 测试API验证响应创建
    logger.info("\n2. API验证响应创建:")
    mock_validation_result = {
        "success": True,
        "message": "验证成功",
        "data": {
            "symbol": "ADAUSDC",
            "status": "TRADING",
            "baseAsset": "BTC",
            "quoteAsset": "USDT",
        },
        "error_code": None,
        "error_details": None,
    }

    api_response = create_api_validation_response_from_result(mock_validation_result)
    logger.info(f"   - 验证成功: {api_response.success}")
    logger.info(f"   - 消息: {api_response.message}")
    logger.info(f"   - 数据: {api_response.data}")
    logger.info(f"   - 错误代码: {api_response.error_code}")

    # 测试操作结果创建
    logger.info("\n3. 操作结果创建:")
    mock_db_result = {"success": True, "message": "交易对添加成功", "data": {"id": 123}}

    operation_result = create_operation_result_from_db_result(
        mock_db_result, "添加交易对"
    )
    logger.info(f"   - 操作成功: {operation_result['success']}")
    logger.info(f"   - 消息: {operation_result['message']}")
    logger.info(f"   - 数据: {operation_result['data']}")

    # 测试批量创建
    logger.info("\n4. 批量交易对创建:")
    mock_symbols_data = [
        mock_symbol_data,
        {**mock_symbol_data, "id": 2, "symbol": "ETHUSDT", "base_asset": "ETH"},
    ]

    symbols = create_trading_symbols_from_db_data(mock_symbols_data)
    logger.info(f"   - 成功创建 {len(symbols)} 个交易对")
    for symbol in symbols:
        logger.info(f"     * {symbol.symbol}: {symbol.base_asset}/{symbol.quote_asset}")

    logger.info("\n✅ Web API Symbols工厂函数演示完成!")
