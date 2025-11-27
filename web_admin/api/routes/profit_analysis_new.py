"""盈利分析路由 - 重新设计版本"""

from typing import Any

from fastapi import APIRouter, Depends, Query

from ..utils.database_helpers import (
    compute_pagination,
    query_all_dict,
    query_one_dict,
)
from ..utils.precision_math import calculate_net_profit
from .auth import get_current_user

router = APIRouter()

FILLED_ALL_SUBQUERY = (
    "(SELECT * FROM filled_orders UNION ALL SELECT * FROM filled_his_orders)"
)


@router.get(
    "/profit-analysis/order-matches/{sell_order_no}",
    dependencies=[Depends(get_current_user)],
)
async def get_order_matches(sell_order_no: str):
    """获取指定SELL单的撮合详情"""
    # 查询撮合详情
    rows = query_all_dict(
        """
        SELECT
            id,
            sell_order_no,
            buy_order_no,
            sell_price,
            buy_price,
            matched_qty,
            profit,
            pair,
            timeframe,
            matched_at,
            created_at
        FROM order_matches
        WHERE sell_order_no = ?
        ORDER BY matched_at ASC
        """,
        (sell_order_no,),
    )

    matches: list[dict[str, Any]] = []
    total_profit: float = 0.0

    for row in rows:
        match_data = {
            "id": row["id"],
            "sell_order_no": row["sell_order_no"],
            "buy_order_no": row["buy_order_no"],
            "sell_price": float(row["sell_price"]),
            "buy_price": float(row["buy_price"]),
            "matched_qty": float(row["matched_qty"]),
            "profit": float(row["profit"]),
            "pair": row["pair"],
            "timeframe": row["timeframe"],
            "matched_at": row["matched_at"],
            "created_at": row["created_at"],
        }
        matches.append(match_data)
        total_profit += match_data["profit"]

    return {
        "sell_order_no": sell_order_no,
        "matches": matches,
        "summary": {
            "total_matches": len(matches),
            "total_profit": round(total_profit, 8),
        },
    }


@router.get(
    "/profit-analysis/order-matches/buy/{buy_order_no}",
    dependencies=[Depends(get_current_user)],
)
async def get_order_matches_by_buy(buy_order_no: str):
    """获取指定BUY单的撮合详情"""
    # 查询撮合详情
    rows = query_all_dict(
        """
        SELECT
            id,
            sell_order_no,
            buy_order_no,
            sell_price,
            buy_price,
            matched_qty,
            profit,
            pair,
            timeframe,
            matched_at,
            created_at
        FROM order_matches
        WHERE buy_order_no = ?
        ORDER BY matched_at ASC
        """,
        (buy_order_no,),
    )

    matches: list[dict[str, Any]] = []
    total_matched_qty: float = 0.0

    for row in rows:
        match_data = {
            "id": row["id"],
            "sell_order_no": row["sell_order_no"],
            "buy_order_no": row["buy_order_no"],
            "sell_price": float(row["sell_price"]),
            "buy_price": float(row["buy_price"]),
            "matched_qty": float(row["matched_qty"]),
            "profit": float(row["profit"]),
            "pair": row["pair"],
            "timeframe": row["timeframe"],
            "matched_at": row["matched_at"],
            "created_at": row["created_at"],
        }
        matches.append(match_data)
        total_matched_qty += match_data["matched_qty"]

    return {
        "buy_order_no": buy_order_no,
        "matches": matches,
        "summary": {
            "total_matches": len(matches),
            "total_matched_qty": round(total_matched_qty, 8),
        },
    }


def _build_sell_orders_conditions(
    start_date: str | None,
    end_date: str | None,
    symbol: str | None,
    order_no: str | None,
    quote_asset: str | None,
) -> tuple[list[str], list[str]]:
    """构建SELL订单查询条件"""
    conditions: list[str] = ["side = 'SELL'"]  # 只查询SELL订单
    params: list[str] = []

    if start_date:
        conditions.append("date(time) >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("date(time) <= ?")
        params.append(end_date)

    if symbol:
        conditions.append("pair LIKE ?")
        params.append(f"%{symbol}%")

    if order_no:
        conditions.append("order_no LIKE ?")
        params.append(f"%{order_no}%")

    if quote_asset:
        conditions.append("UPPER(pair) LIKE ?")
        params.append(f"%{quote_asset.upper()}")

    return conditions, params


# 旧版分页与统计函数已由 query_one_dict/query_all_dict 替代


@router.get("/profit-analysis/daily-profits")
async def get_daily_profits(
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    symbol: str | None = Query(None, description="交易对符号"),
    quote_asset: str | None = Query(None, description="计价资产符号, 例如 USDC"),
):
    """获取每日盈亏汇总数据"""
    # 构建查询条件 - 包含所有订单
    conditions: list[str] = []
    params: list[str] = []

    if start_date:
        conditions.append("date(time) >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("date(time) <= ?")
        params.append(end_date)

    if symbol:
        conditions.append("pair LIKE ?")
        params.append(f"%{symbol}%")

    if quote_asset:
        conditions.append("UPPER(pair) LIKE ?")
        params.append(f"%{quote_asset.upper()}")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # 使用SQL直接汇总每日盈亏数据
    query = f"""
        SELECT
            date(time) as date,
            COUNT(*) as order_count,
            SUM(COALESCE(CAST(profit AS REAL), 0)) as total_profit,
            SUM(COALESCE(CAST(commission AS REAL), 0)) as total_commission
        FROM {FILLED_ALL_SUBQUERY} AS filled_all
        WHERE {where_clause}
        GROUP BY date(time)
        ORDER BY date(time) DESC
    """

    rows = query_all_dict(query, tuple(params))

    # 将已有数据放入字典,便于后续补零
    existing_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        total_profit = float(row["total_profit"]) if row["total_profit"] else 0.0
        total_commission = (
            float(row["total_commission"]) if row["total_commission"] else 0.0
        )
        net_profit = calculate_net_profit(total_profit, total_commission)
        existing_map[row["date"]] = {
            "date": row["date"],
            "order_count": row["order_count"],
            "total_profit": total_profit,
            "total_commission": total_commission,
            "net_profit": net_profit,
        }

    # 计算需要覆盖的日期范围
    # 优先使用传入的 start_date / end_date; 否则用数据库中该条件下的最小/最大日期
    from datetime import datetime, timedelta

    def _parse(d: str) -> datetime:
        return datetime.strptime(d, "%Y-%m-%d")

    range_start: str | None = start_date
    range_end: str | None = end_date

    if range_start is None or range_end is None:
        # 查询该筛选条件下的最小/最大日期
        range_query = f"SELECT MIN(date(time)) AS min_d, MAX(date(time)) AS max_d FROM {FILLED_ALL_SUBQUERY} AS filled_all WHERE {where_clause}"
        r = query_one_dict(range_query, tuple(params))
        min_d = r["min_d"] if r and r["min_d"] else None
        max_d = r["max_d"] if r and r["max_d"] else None
        if range_start is None:
            range_start = min_d
        if range_end is None:
            range_end = max_d

    daily_profits: list[dict[str, Any]] = []

    if range_start and range_end:
        # 生成完整日期序列,对缺失日期补零
        start_dt = _parse(range_start)
        end_dt = _parse(range_end)
        if start_dt > end_dt:
            start_dt, end_dt = end_dt, start_dt

        current = start_dt
        while current <= end_dt:
            d = current.strftime("%Y-%m-%d")
            if d in existing_map:
                daily_profits.append(existing_map[d])
            else:
                # 缺失日期补零
                daily_profits.append(
                    {
                        "date": d,
                        "order_count": 0,
                        "total_profit": 0.0,
                        "total_commission": 0.0,
                        "net_profit": calculate_net_profit(0.0, 0.0),
                    }
                )
            current += timedelta(days=1)

        # 默认按日期倒序(与原API行为一致)
        daily_profits.sort(key=lambda x: x["date"], reverse=True)
    else:
        # 没有可确定的日期范围时,返回已有数据(保持向后兼容)
        daily_profits = sorted(
            existing_map.values(), key=lambda x: x["date"], reverse=True
        )

    return {
        "success": True,
        "message": "获取每日盈亏数据成功",
        "data": daily_profits,
        "total": len(daily_profits),
    }


@router.get("/profit-analysis/monthly-profits")
async def get_monthly_profits(
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    symbol: str | None = Query(None, description="交易对符号"),
    quote_asset: str | None = Query(None, description="计价资产符号, 例如 USDC"),
):
    """获取每月盈亏汇总数据"""
    conditions: list[str] = []
    params: list[str] = []

    if start_date:
        conditions.append("date(time) >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("date(time) <= ?")
        params.append(end_date)

    if symbol:
        conditions.append("pair LIKE ?")
        params.append(f"%{symbol}%")

    if quote_asset:
        conditions.append("UPPER(pair) LIKE ?")
        params.append(f"%{quote_asset.upper()}")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT
            strftime('%Y-%m', time) as month,
            COUNT(*) as order_count,
            SUM(COALESCE(CAST(profit AS REAL), 0)) as total_profit,
            SUM(COALESCE(CAST(commission AS REAL), 0)) as total_commission
        FROM {FILLED_ALL_SUBQUERY} AS filled_all
        WHERE {where_clause}
        GROUP BY strftime('%Y-%m', time)
        ORDER BY month DESC
    """

    rows = query_all_dict(query, tuple(params))

    existing_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        total_profit = float(row["total_profit"]) if row["total_profit"] else 0.0
        total_commission = (
            float(row["total_commission"]) if row["total_commission"] else 0.0
        )
        net_profit = calculate_net_profit(total_profit, total_commission)

        existing_map[row["month"]] = {
            "month": row["month"],
            "order_count": row["order_count"],
            "total_profit": total_profit,
            "total_commission": total_commission,
            "net_profit": net_profit,
        }

    from datetime import datetime

    def _parse_date(value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%d")

    def _month_start(dt: datetime) -> datetime:
        return dt.replace(day=1)

    def _month_key(dt: datetime) -> str:
        return dt.strftime("%Y-%m")

    def _next_month(dt: datetime) -> datetime:
        year = dt.year + (1 if dt.month == 12 else 0)
        month = 1 if dt.month == 12 else dt.month + 1
        return dt.replace(year=year, month=month, day=1)

    range_start: str | None = start_date
    range_end: str | None = end_date

    if range_start is None or range_end is None:
        range_query = f"SELECT MIN(date(time)) AS min_d, MAX(date(time)) AS max_d FROM {FILLED_ALL_SUBQUERY} AS filled_all WHERE {where_clause}"
        r = query_one_dict(range_query, tuple(params))
        min_d = r["min_d"] if r and r["min_d"] else None
        max_d = r["max_d"] if r and r["max_d"] else None
        if range_start is None:
            range_start = min_d
        if range_end is None:
            range_end = max_d

    monthly_profits: list[dict[str, Any]] = []

    if range_start and range_end:
        start_dt = _month_start(_parse_date(range_start))
        end_dt = _month_start(_parse_date(range_end))
        if start_dt > end_dt:
            start_dt, end_dt = end_dt, start_dt

        current = start_dt
        while current <= end_dt:
            key = _month_key(current)
            if key in existing_map:
                monthly_profits.append(existing_map[key])
            else:
                monthly_profits.append(
                    {
                        "month": key,
                        "order_count": 0,
                        "total_profit": 0.0,
                        "total_commission": 0.0,
                        "net_profit": calculate_net_profit(0.0, 0.0),
                    }
                )
            current = _next_month(current)

        monthly_profits.sort(key=lambda x: x["month"], reverse=True)
    else:
        monthly_profits = sorted(
            existing_map.values(), key=lambda x: x["month"], reverse=True
        )

    return {
        "success": True,
        "message": "获取每月盈亏数据成功",
        "data": monthly_profits,
        "total": len(monthly_profits),
    }


@router.get("/profit-analysis/symbol-profits")
async def get_symbol_profits(
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    quote_asset: str | None = Query(None, description="计价资产符号, 例如 USDC"),
):
    """获取交易对盈亏汇总数据"""
    # 构建查询条件 - 包含所有订单
    conditions: list[str] = []
    params: list[str] = []

    if start_date:
        conditions.append("date(time) >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("date(time) <= ?")
        params.append(end_date)

    if quote_asset:
        conditions.append("UPPER(pair) LIKE ?")
        params.append(f"%{quote_asset.upper()}")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # 使用SQL直接汇总交易对盈亏数据
    query = f"""
        SELECT
            pair as symbol,
            COUNT(*) as order_count,
            SUM(COALESCE(CAST(profit AS REAL), 0)) as total_profit,
            SUM(COALESCE(CAST(commission AS REAL), 0)) as total_commission
        FROM {FILLED_ALL_SUBQUERY} AS filled_all
        WHERE {where_clause}
        GROUP BY pair
        ORDER BY pair
    """

    rows = query_all_dict(query, tuple(params))
    symbol_profits: list[dict[str, Any]] = []
    for row in rows:
        total_profit = float(row["total_profit"]) if row["total_profit"] else 0.0
        total_commission = (
            float(row["total_commission"]) if row["total_commission"] else 0.0
        )
        net_profit = calculate_net_profit(total_profit, total_commission)

        symbol_profits.append(
            {
                "symbol": row["symbol"],
                "order_count": row["order_count"],
                "total_profit": total_profit,
                "total_commission": total_commission,
                "net_profit": net_profit,
            }
        )

    # 按净利润降序排列
    symbol_profits.sort(key=lambda x: x["net_profit"], reverse=True)

    return {
        "success": True,
        "message": "获取交易对盈亏数据成功",
        "data": symbol_profits,
        "total": len(symbol_profits),
    }


@router.get(
    "/profit-analysis/symbol-daily-profits",
    dependencies=[Depends(get_current_user)],
)
async def get_symbol_daily_profits(
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    symbol: str | None = Query(None, description="交易对符号"),
    quote_asset: str | None = Query(None, description="计价资产符号, 例如 USDC"),
):
    """获取交易对每日盈亏详情数据"""
    # 构建查询条件 - 包含所有订单
    conditions: list[str] = []
    params: list[str] = []

    if start_date:
        conditions.append("date(time) >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("date(time) <= ?")
        params.append(end_date)

    if symbol:
        conditions.append("pair LIKE ?")
        params.append(f"%{symbol}%")

    if quote_asset:
        conditions.append("UPPER(pair) LIKE ?")
        params.append(f"%{quote_asset.upper()}")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # 使用SQL直接汇总交易对每日盈亏数据
    query = f"""
        SELECT
            pair as symbol,
            date(time) as date,
            COUNT(*) as order_count,
            SUM(COALESCE(CAST(profit AS REAL), 0)) as total_profit,
            SUM(COALESCE(CAST(commission AS REAL), 0)) as total_commission
        FROM {FILLED_ALL_SUBQUERY} AS filled_all
        WHERE {where_clause}
        GROUP BY pair, date(time)
        ORDER BY pair ASC, date(time) DESC
    """

    rows = query_all_dict(query, tuple(params))
    symbol_daily_profits: list[dict[str, Any]] = []
    for row in rows:
        total_profit = float(row["total_profit"]) if row["total_profit"] else 0.0
        total_commission = (
            float(row["total_commission"]) if row["total_commission"] else 0.0
        )
        net_profit = calculate_net_profit(total_profit, total_commission)

        symbol_daily_profits.append(
            {
                "symbol": row["symbol"],
                "date": row["date"],
                "order_count": row["order_count"],
                "total_profit": total_profit,
                "total_commission": total_commission,
                "net_profit": net_profit,
            }
        )

    return {
        "success": True,
        "message": "获取交易对每日盈亏数据成功",
        "data": symbol_daily_profits,
        "total": len(symbol_daily_profits),
    }


@router.get(
    "/profit-analysis/sell-orders",
    dependencies=[Depends(get_current_user)],
)
async def get_sell_orders(
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    symbol: str | None = Query(None, description="交易对符号"),
    order_no: str | None = Query(None, description="订单号"),
    quote_asset: str | None = Query(None, description="计价资产符号, 例如 USDC"),
    page: int = Query(1, description="页码"),
    limit: int = Query(20, description="每页数量"),
):
    """获取SELL订单明细 (只包含SELL订单,因为只有SELL单才产生利润)"""
    conditions, params = _build_sell_orders_conditions(
        start_date, end_date, symbol, order_no, quote_asset
    )
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    count_row = query_one_dict(
        f"SELECT COUNT(*) as total FROM {FILLED_ALL_SUBQUERY} AS filled_all WHERE {where_clause}",
        tuple(params),
    )
    total = int(count_row["total"]) if count_row else 0

    total_pages, offset = compute_pagination(total, page, limit)
    data_rows = query_all_dict(
        f"""
        SELECT id, pair, side, order_amount, average_price, trading_total,
               COALESCE(profit, '0') as profit, COALESCE(commission, '0') as commission,
               time, order_no, client_order_id
        FROM {FILLED_ALL_SUBQUERY} AS filled_all
        WHERE {where_clause}
        ORDER BY time DESC
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    )

    orders: list[dict[str, Any]] = []
    for row in data_rows:
        order_dict: dict[str, Any] = dict(row)
        order_dict["net_profit"] = calculate_net_profit(
            order_dict.get("profit", 0), order_dict.get("commission", 0)
        )
        orders.append(order_dict)

    return {
        "success": True,
        "message": "获取订单数据成功",
        "data": orders,
        "total": total,
        "page": page,
        "page_size": limit,
        "total_pages": total_pages,
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    # 删除无必要的模块说明日志
