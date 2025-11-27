"""Mock Binance Client for Backtesting."""

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m backtester.mock_client` 运行该模块, 无需手动修改 sys.path"
    )

import random
from collections import defaultdict, deque
from datetime import datetime
from typing import Any

import pandas as pd
from binance.exceptions import BinanceAPIException
from loguru import logger

from database.crud import get_symbol_info
from database.db_config import get_db_manager


class MockBinanceClient:
    """
    A mock client that simulates the python-binance client.
    """

    def __init__(self, broker: Any, data: Any):
        """
        Initializes the Mock Client as a virtual exchange.

        Args:
            broker: The backtesting broker instance.
            data: The historical market data (pandas DataFrame).
        """
        self._broker = broker
        self._data = data
        self._tick = 0
        self._db_manager = get_db_manager()
        self.executed_orders: deque[dict[str, Any]] = deque()
        self._executed_orders_by_symbol: defaultdict[str, deque[dict[str, Any]]] = (
            defaultdict(deque)
        )
        self._history_order_limit = 100
        self._history_time_window_ms = 1 * 24 * 60 * 60 * 1000  # 1 day window
        self.pending_orders: list[
            dict[str, Any]
        ] = []  # Stores pending orders during backtest
        self._virtual_historical_orders: list[dict[str, Any]] = []
        self._order_id_counter = 1  # Reset each backtest session per design

        # Locked balances for current backtest symbol assets
        self._locked: dict[str, float] = {}

    def update_tick(self, new_tick: int | pd.Timestamp) -> None:
        """
        Updates the internal tick to synchronize with the backtest engine.
        Pending orders are no longer processed automatically here; the caller
        decides when to evaluate fills for the current candle.

        Args:
            new_tick: Either an integer index or a pandas Timestamp (for efficient iteration).
        """
        self._tick = new_tick

    def _current_open_price(self) -> float:
        """Return the open price of the current tick candle."""
        if hasattr(self._tick, "to_pydatetime"):
            return float(self._data.loc[self._tick, "open"])
        if isinstance(self._tick, int):
            return float(self._data["open"].iloc[self._tick])
        # Assume datetime-like object usable as index
        return float(self._data.loc[self._tick, "open"])

    def _current_close_price(self) -> float:
        """Return the close price of the current tick candle."""
        if hasattr(self._tick, "to_pydatetime"):
            return float(self._data.loc[self._tick, "close"])
        if isinstance(self._tick, int):
            return float(self._data["close"].iloc[self._tick])
        # Assume datetime-like object usable as index
        return float(self._data.loc[self._tick, "close"])

    def process_pending_orders_now(self) -> None:
        """Re-evaluate pending orders using the current tick's candle data."""
        self._process_pending_orders()

    def _get_assets(self, symbol: str) -> tuple[str, str]:
        info = get_symbol_info(symbol)
        return info.base_asset, info.quote_asset

    def _get_totals(self, symbol: str) -> tuple[float, float]:
        _base_asset, _ = self._get_assets(symbol)
        base_total = float(
            self._broker.positions.get(symbol, 0)
        )  # positions tracked by symbol in Broker
        quote_total = float(self._broker.cash)
        return base_total, quote_total

    # ------------------------------------------------------------------
    # Simple wrappers to satisfy production client interface
    # ------------------------------------------------------------------

    def funding_wallet(
        self, asset: str | None = None, **_: Any
    ) -> list[dict[str, str]]:
        """Backtest环境不区分资金账户, 返回空列表"""
        return []

    def _request_margin_api(
        self,
        method: str,
        endpoint: str,
        signed: bool = False,
        data: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        """提供 Simple Earn 等接口的空数据响应"""
        if endpoint == "simple-earn/flexible/position":
            return {"rows": []}
        raise NotImplementedError(
            f"MockBinanceClient does not implement margin endpoint {endpoint}"
        )

    def _ensure_locked_keys(self, symbol: str) -> None:
        base_asset, quote_asset = self._get_assets(symbol)
        if base_asset not in self._locked:
            self._locked[base_asset] = 0.0
        if quote_asset not in self._locked:
            self._locked[quote_asset] = 0.0

    @staticmethod
    def _raise_insufficient_balance() -> None:
        # Emulate python-binance exception signature: (response, status_code, text)
        # Provide JSON text body with code and msg to populate e.code and e.message
        payload = '{"code": -2010, "msg": "Account has insufficient balance for requested action"}'
        raise BinanceAPIException(None, 400, payload)

    @staticmethod
    def _raise_stop_would_trigger_immediately() -> None:
        payload = '{"code": -2010, "msg": "Stop price would trigger immediately."}'
        raise BinanceAPIException(None, 400, payload)

    def _process_pending_orders(self):
        """
        Processes pending orders against current market data.
        Executes orders when market conditions are met.
        """
        # Find the index of current tick in the data
        try:
            tick_index = self._data.index.get_loc(self._tick)
        except KeyError:
            return  # Tick not found in data

        if tick_index >= len(self._data):
            return

        current_candle = self._data.iloc[tick_index]
        current_time = (
            self._tick.to_pydatetime()
            if hasattr(self._tick, "to_pydatetime")
            else self._tick
        )

        # Process each pending order
        orders_to_remove = []
        for i, order in enumerate(self.pending_orders):
            if self._should_execute_order(order, current_candle):
                # Execute the order
                executed_order = self._execute_pending_order(
                    order, current_candle, current_time
                )
                if executed_order:
                    self._store_executed_order(executed_order)
                    orders_to_remove.append(i)

        # Remove executed orders from pending list (in reverse order to maintain indices)
        for i in reversed(orders_to_remove):
            self.pending_orders.pop(i)

    def _store_executed_order(self, order: dict[str, Any]) -> None:
        """Insert executed order while keeping internal list sorted by orderId."""
        try:
            _ = int(order["orderId"])
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid orderId in executed order: {order}") from exc

        symbol = order.get("symbol", "").upper()
        timestamp = self._extract_order_timestamp(order)

        self.executed_orders.append(order)
        self._trim_deque(self.executed_orders, timestamp)

        symbol_history = self._executed_orders_by_symbol[symbol]
        symbol_history.append(order)
        self._trim_deque(symbol_history, timestamp)

    def _extract_order_timestamp(self, order: dict[str, Any]) -> int | None:
        ts = order.get("updateTime") or order.get("time")
        if ts is None:
            return None
        try:
            return int(ts)
        except Exception:
            return None

    def _trim_deque(
        self, history: deque[dict[str, Any]], latest_timestamp: int | None
    ) -> None:
        while len(history) > self._history_order_limit:
            history.popleft()

        if latest_timestamp is None:
            return

        cutoff = latest_timestamp - self._history_time_window_ms
        while history:
            ts = self._extract_order_timestamp(history[0])
            if ts is None or ts >= cutoff:
                break
            history.popleft()

    def _should_execute_order(self, order: dict[str, Any], current_candle: Any) -> bool:
        """
        Determines if a pending order should be executed based on current market data.
        """
        order_type = order.get("type", "")
        side = order.get("side", "")
        stop_price = float(order.get("stopPrice", "0"))

        return bool(
            order_type == "STOP_LOSS"
            and (
                (side == "BUY" and current_candle["high"] >= stop_price)
                or (side == "SELL" and current_candle["low"] <= stop_price)
            )
        )

    def _execute_pending_order(
        self, order: dict[str, Any], current_candle: Any, current_time: datetime
    ) -> dict[str, Any] | None:
        """
        Executes a pending order and returns the filled order data.
        """
        try:
            symbol = order["symbol"]
            side = order["side"]
            quantity = float(order["origQty"])
            stop_price = float(order["stopPrice"])

            # Use stop price as execution price for stop-loss orders
            execution_price = stop_price

            # Execute through broker (no fees)
            if side == "BUY":
                self._broker.buy(symbol, quantity, execution_price)
            elif side == "SELL":
                self._broker.sell(symbol, quantity, execution_price)
            else:
                return None

            # Release locked on fill
            base_asset, quote_asset = self._get_assets(symbol)
            self._ensure_locked_keys(symbol)
            notional = quantity * execution_price
            if side == "BUY":
                self._locked[quote_asset] = max(
                    0.0, self._locked.get(quote_asset, 0.0) - notional
                )
            else:
                self._locked[base_asset] = max(
                    0.0, self._locked.get(base_asset, 0.0) - quantity
                )

            # Create filled order record per design
            filled_order_dict = {
                "symbol": symbol,
                "orderId": int(order["orderId"]),
                # clientOrderId only if provided
                **(
                    {"clientOrderId": order["clientOrderId"]}
                    if order.get("clientOrderId")
                    else {}
                ),
                "time": int(
                    order.get("time", int(current_time.timestamp() * 1000))
                ),  # creation time
                "updateTime": int(current_time.timestamp() * 1000),  # fill time
                "price": "0",
                "stopPrice": str(execution_price),
                "origQty": str(quantity),
                "executedQty": str(quantity),
                "cummulativeQuoteQty": str(notional),
                "status": "FILLED",
                "type": order.get("type", "STOP_LOSS"),
                "side": side.upper(),
            }

            return filled_order_dict

        except Exception as e:
            logger.error(f"Error executing pending order {order.get('orderId')}: {e}")
            return None

    def _generate_virtual_historical_orders(self) -> None:
        """
        Generates virtual historical orders for the symbol to simulate a real exchange.
        These orders represent past trading activity that would be returned by get_all_orders.
        """
        if self._should_skip_virtual_orders():
            return

        symbol = self._resolve_virtual_symbol()
        num_orders = self._determine_virtual_order_count()
        self._virtual_historical_orders.clear()

        for offset, candle, timestamp, side in self._iter_virtual_order_sources(
            num_orders
        ):
            price = self._select_virtual_price(side, candle)
            quantity = self._select_virtual_quantity(candle)
            order_id = self._virtual_order_id(num_orders, offset)
            client_order_id = self._virtual_client_order_id(order_id)
            historical_order = self._build_virtual_order(
                symbol,
                candle,
                timestamp,
                side,
                price,
                quantity,
                order_id,
                client_order_id,
            )
            self._virtual_historical_orders.append(historical_order)

        self._virtual_historical_orders.sort(key=lambda x: x["time"])

    def _should_skip_virtual_orders(self) -> bool:
        """Decide whether virtual orders should be generated."""
        return getattr(self._data, "empty", True)

    def _resolve_virtual_symbol(self) -> str:
        """Determine symbol name for virtual orders."""
        if hasattr(self._data, "name") and self._data.name:
            return str(self._data.name)
        return "ADAUSDC"

    def _determine_virtual_order_count(self) -> int:
        """Calculate how many virtual orders to generate."""
        data_length = len(self._data)
        return min(50, data_length // 10)

    def _iter_virtual_order_sources(
        self, num_orders: int
    ) -> list[tuple[int, Any, Any, str]]:
        """Yield source candle information for virtual orders."""
        sources: list[tuple[int, Any, Any, str]] = []
        if num_orders <= 0:
            return sources

        data_length = len(self._data)
        for offset in range(num_orders):
            tick_index = random.randint(0, data_length - 1)
            candle = self._data.iloc[tick_index]
            timestamp = self._data.index[tick_index]
            side = random.choice(["BUY", "SELL"])
            sources.append((offset, candle, timestamp, side))
        return sources

    @staticmethod
    def _select_virtual_price(side: str, candle: Any) -> float:
        """Select a realistic price for a virtual order."""
        price_span = float(candle["high"]) - float(candle["low"])
        adjustment = random.uniform(0, price_span * 0.3)
        if side == "BUY":
            return float(candle["low"]) + adjustment
        return float(candle["high"]) - adjustment

    @staticmethod
    def _select_virtual_quantity(candle: Any) -> float:
        """Select a realistic quantity for a virtual order."""
        base_volume = float(candle["volume"])
        return random.uniform(0.1, min(10.0, base_volume * 0.01))

    def _virtual_order_id(self, num_orders: int, offset: int) -> int:
        """Build a virtual order id relative to the current counter."""
        return self._order_id_counter - num_orders + offset

    @staticmethod
    def _virtual_client_order_id(order_id: int) -> str:
        """Generate a client order id similar to Binance format."""
        return f"x-{order_id:08d}-{random.randint(1000, 9999)}"

    @staticmethod
    def _build_virtual_order(
        symbol: str,
        candle: Any,
        timestamp: Any,
        side: str,
        price: float,
        quantity: float,
        order_id: int,
        client_order_id: str,
    ) -> dict[str, Any]:
        """Compose a virtual historical order payload."""
        quote_qty = quantity * price
        timestamp_ms = int(timestamp.timestamp() * 1000)
        formatted_qty = f"{quantity:.8f}"
        formatted_price = f"{price:.8f}"
        formatted_quote_qty = f"{quote_qty:.8f}"

        return {
            "symbol": symbol,
            "orderId": order_id,
            "clientOrderId": client_order_id,
            "price": formatted_price,
            "origQty": formatted_qty,
            "executedQty": formatted_qty,
            "cummulativeQuoteQty": formatted_quote_qty,
            "status": "FILLED",
            "timeInForce": "GTC",
            "type": "MARKET",
            "side": side,
            "stopPrice": "0.00000000",
            "icebergQty": "0.00000000",
            "time": timestamp_ms,
            "updateTime": timestamp_ms,
            "isWorking": False,
            "origQuoteOrderQty": formatted_quote_qty,
            "workingTime": timestamp_ms,
            "selfTradePreventionMode": "NONE",
        }

    # --- Mocked API Methods ---

    def get_asset_balance(self, asset: str) -> dict[str, str]:
        """Deprecated in backtest; prefer get_account. Returns computed free/locked for an asset."""
        asset = asset.upper()
        # Derive totals
        # We cannot infer symbol from asset reliably here; so return zeros unless asset matches known base/quote from current data name
        symbol = self._data.name if hasattr(self._data, "name") else None
        if not symbol:
            return {"free": "0", "locked": "0"}
        base_asset, quote_asset = self._get_assets(symbol)
        base_total, quote_total = self._get_totals(symbol)
        self._ensure_locked_keys(symbol)
        if asset == quote_asset:
            free = quote_total - self._locked.get(quote_asset, 0.0)
            return {
                "free": str(free),
                "locked": str(self._locked.get(quote_asset, 0.0)),
            }
        if asset == base_asset:
            free = base_total - self._locked.get(base_asset, 0.0)
            return {"free": str(free), "locked": str(self._locked.get(base_asset, 0.0))}
        return {"free": "0", "locked": "0"}

    def get_symbol_ticker(self, symbol: str) -> dict[str, str]:
        """Mocks the get_symbol_ticker method."""
        try:
            if hasattr(self._tick, "to_pydatetime"):
                # Tick is a Timestamp; use label-based access
                price = self._data.loc[self._tick, "close"]
            elif isinstance(self._tick, int):
                price = self._data["close"].iloc[self._tick]
            else:
                # Fallback: try loc
                price = self._data.loc[self._tick, "close"]
            return {"symbol": symbol, "price": str(float(price))}
        except Exception:
            logger.error(
                "Mock client failed to get current price for get_symbol_ticker."
            )
            return {"symbol": symbol, "price": "0"}

    def create_order(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: str,
        price: str | None = None,
        timeInForce: str | None = None,
        stopPrice: str | None = None,
        newClientOrderId: str | None = None,
    ):
        """Mocks create_order. Only STOP_LOSS is supported; reserves locked balances at order time."""
        symbol = symbol.upper()
        side = side.upper()
        if type != "STOP_LOSS":
            raise ValueError("Only STOP_LOSS is supported in backtest mock")

        qty = float(quantity)
        stop = float(stopPrice or 0)
        current_open_price = self._current_open_price()
        order_id = self._order_id_counter
        self._order_id_counter += 1

        if side == "BUY" and stop <= current_open_price:
            self._raise_stop_would_trigger_immediately()
        if side == "SELL" and stop >= current_open_price:
            self._raise_stop_would_trigger_immediately()

        # Reserve locked based on side; fail-fast on insufficient free
        base_asset, quote_asset = self._get_assets(symbol)
        self._ensure_locked_keys(symbol)
        base_total, quote_total = self._get_totals(symbol)
        if side == "BUY":
            need = qty * stop
            free_quote = quote_total - self._locked.get(quote_asset, 0.0)
            if free_quote < need:
                self._raise_insufficient_balance()
            self._locked[quote_asset] += need
        else:  # SELL
            free_base = base_total - self._locked.get(base_asset, 0.0)
            if free_base < qty:
                self._raise_insufficient_balance()
            self._locked[base_asset] += qty

        # Use current candle timestamp for order creation timestamp
        # Derive milliseconds robustly from either a Timestamp index value or a positional index
        if hasattr(self._tick, "to_pydatetime"):
            tick_dt = self._tick.to_pydatetime()
            current_time_ms = int(tick_dt.timestamp() * 1000)
        elif isinstance(self._tick, int):
            try:
                index_ts = self._data.index[self._tick]
                if hasattr(index_ts, "to_pydatetime"):
                    index_dt = index_ts.to_pydatetime()
                else:
                    index_dt = index_ts
                current_time_ms = int(index_dt.timestamp() * 1000)
            except Exception:
                current_time_ms = 0
        else:
            # Assume datetime-like
            current_time_ms = int(self._tick.timestamp() * 1000)
        pending_order: dict[str, Any] = {
            "symbol": symbol,
            "orderId": int(order_id),
            # Include clientOrderId only if provided
            **({"clientOrderId": newClientOrderId} if newClientOrderId else {}),
            "price": "0",
            "origQty": str(quantity),
            "executedQty": "0",
            "cummulativeQuoteQty": "0",
            "status": "NEW",
            "type": type,
            "side": side,
            "stopPrice": str(stopPrice) if stopPrice is not None else None,
            "time": current_time_ms,
            "updateTime": current_time_ms,
            "timeInForce": timeInForce or "GTC",
            "icebergQty": "0",
            "isWorking": True,
            "workingTime": current_time_ms,
            "origQuoteOrderQty": "0",
            "selfTradePreventionMode": "NONE",
        }
        self.pending_orders.append(pending_order)
        return pending_order

    def _record_filled_order(self, *args: Any, **kwargs: Any):
        """Deprecated: no external DB writes in backtest mock."""
        raise NotImplementedError

    def get_klines(
        self,
        symbol: str | None = None,
        interval: str | None = None,
        limit: int | None = 500,
        **kwargs: Any,
    ) -> list[Any]:
        """
        Strict DB passthrough per design.

        Rules:
        - Data comes directly from backtest_klines (no resample/fill/transform).
        - Always return in ascending order by open_time.
        - Strictly honor startTime/endTime/limit without implicit caps.
        - Fail-fast on invalid parameters.
        """
        # Validate inputs (fail-fast)
        if not symbol or not isinstance(symbol, str):
            raise ValueError("symbol is required and must be a string")
        if not interval or not isinstance(interval, str):
            raise ValueError("interval is required and must be a string")

        start_time = kwargs.get("startTime")
        end_time = kwargs.get("endTime")

        if start_time is not None and not isinstance(start_time, int):
            raise ValueError("startTime must be an integer (ms)")
        if end_time is not None and not isinstance(end_time, int):
            raise ValueError("endTime must be an integer (ms)")
        if start_time is not None and end_time is not None and start_time > end_time:
            raise ValueError("startTime must be <= endTime")

        if limit is not None:
            try:
                limit = int(limit)
            except Exception as e:  # pragma: no cover - defensive
                raise ValueError("limit must be an integer") from e
            if limit <= 0:
                # Interpret non-positive as no rows
                return []

        params: list[Any] = [symbol.upper(), interval]
        base_select = (
            "SELECT open_time, open_price, high_price, low_price, close_price, volume, close_time, "
            "quote_asset_volume, number_of_trades, taker_buy_base_asset_volume, taker_buy_quote_asset_volume "
            "FROM backtest_klines WHERE symbol = ? AND timeframe = ?"
        )

        # Decide ordering and limiting strategy to emulate Binance behavior while returning ASC:
        # - Only end_time provided (or only limit): choose the last `limit` rows up to end_time (or overall), then return ASC.
        # - start_time provided (with or without end_time): fetch ASC from start_time, apply end_time if provided, then LIMIT.
        rows = []
        if start_time is None:
            # No start_time: we want the last `limit` rows up to end_time (or overall)
            where = ""
            if end_time is not None:
                where = " AND open_time <= ?"
                params_q = [*params, int(end_time)]
            else:
                params_q = params

            query_desc = f"{base_select}{where} ORDER BY open_time DESC"
            if limit is not None:
                query_desc += f" LIMIT {limit}"
            with self._db_manager.get_connection() as conn:
                rows = conn.execute(query_desc, tuple(params_q)).fetchall()
            # Reverse to ASC for return
            rows = list(rows)[::-1]
        else:
            # start_time provided: fetch forward in ASC order
            where = " AND open_time >= ?"
            params_q = [*params, int(start_time)]
            if end_time is not None:
                where += " AND open_time <= ?"
                params_q.append(int(end_time))
            query_asc = f"{base_select}{where} ORDER BY open_time ASC"
            if limit is not None:
                query_asc += f" LIMIT {limit}"
            with self._db_manager.get_connection() as conn:
                rows = conn.execute(query_asc, tuple(params_q)).fetchall()

        # Map rows to Binance array format (no transformation of values apart from str/int casting)
        klines_data: list[Any] = []
        for r in rows:
            k = [
                int(r[0]),
                str(r[1]),
                str(r[2]),
                str(r[3]),
                str(r[4]),
                str(r[5]),
                int(r[6]),
                str(r[7]),
                int(r[8]),
                str(r[9]),
                str(r[10]),
                "0",
            ]
            klines_data.append(k)

        return klines_data

    def get_open_orders(
        self, symbol: str | None = None, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Mocks get_open_orders. Returns the list of pending orders."""
        orders = self.pending_orders
        if symbol:
            orders = [o for o in orders if o.get("symbol") == symbol.upper()]
        return orders

    def get_all_orders(
        self,
        symbol: str | None = None,
        limit: int | None = None,
        orderId: int | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Mocks get_all_orders. Returns only executed orders from backtest.

        Args:
            symbol: Trading pair symbol (filtered automatically)
            limit: Maximum number of orders to return
            orderId: Start from this order ID (for pagination)

        Returns:
            List of executed orders in Binance API format
        """
        if limit is not None:
            try:
                limit = int(limit)
            except Exception as exc:  # pragma: no cover - defensive
                raise ValueError("limit must be an integer") from exc
            if limit < 0:
                raise ValueError("limit must be non-negative")

        symbol_filter = symbol.upper() if symbol else None
        if orderId is not None:
            try:
                order_id_filter = int(orderId)
            except Exception as exc:  # pragma: no cover - defensive
                raise ValueError("orderId must be an integer") from exc
        else:
            order_id_filter = None

        history = (
            self._executed_orders_by_symbol[symbol_filter]
            if symbol_filter
            else self.executed_orders
        )

        if not history:
            return []

        results: list[dict[str, Any]] = []
        for order in history:
            if (
                order_id_filter is not None
                and int(order.get("orderId", 0)) < order_id_filter
            ):
                continue
            results.append(order)
            if limit is not None and len(results) >= limit:
                break
        return results

    def cancel_order(
        self,
        symbol: str,
        orderId: int | None = None,
        origClientOrderId: str | None = None,
    ) -> dict[str, Any]:
        """
        Mocks cancel_order. Releases locked balances and returns cancelled order dict.
        """
        symbol = symbol.upper()
        # Find the order to cancel (robust match by int orderId or clientOrderId)
        target = None
        idx = -1
        int_order_id: int | None = None
        if orderId is not None:
            try:
                int_order_id = int(orderId)
            except Exception:
                int_order_id = None
        for i, order in enumerate(self.pending_orders):
            oid = order.get("orderId")
            try:
                oid_int = int(oid) if oid is not None else None
            except Exception:
                oid_int = None
            if int_order_id is not None and oid_int == int_order_id:
                target = order
                idx = i
                break
            if (
                origClientOrderId is not None
                and order.get("clientOrderId") == origClientOrderId
            ):
                target = order
                idx = i
                break
        if target is None:
            # In backtest, treat cancel of non-existent order as idempotent no-op
            # to emulate robustness and avoid failing higher-level logic that
            # works with slightly stale snapshots. Return a synthetic canceled order.
            if hasattr(self._tick, "to_pydatetime"):
                tick_dt = self._tick.to_pydatetime()
                update_ms = int(tick_dt.timestamp() * 1000)
            elif isinstance(self._tick, int):
                try:
                    index_ts = self._data.index[self._tick]
                    if hasattr(index_ts, "to_pydatetime"):
                        index_dt = index_ts.to_pydatetime()
                    else:
                        index_dt = index_ts
                    update_ms = int(index_dt.timestamp() * 1000)
                except Exception:
                    update_ms = 0
            else:
                update_ms = int(self._tick.timestamp() * 1000)
            return {
                "symbol": symbol,
                "orderId": int_order_id if int_order_id is not None else None,
                "origClientOrderId": origClientOrderId,
                "status": "CANCELED",
                "type": "STOP_LOSS",
                "side": "BUY",
                "price": "0",
                "origQty": "0",
                "executedQty": "0",
                "cummulativeQuoteQty": "0",
                "updateTime": update_ms,
            }

        # Release locked
        base_asset, quote_asset = self._get_assets(symbol)
        self._ensure_locked_keys(symbol)
        qty = float(target["origQty"])
        stop = float(target.get("stopPrice") or 0)
        if target.get("side") == "BUY":
            self._locked[quote_asset] = max(
                0.0, self._locked.get(quote_asset, 0.0) - qty * stop
            )
        else:
            self._locked[base_asset] = max(0.0, self._locked.get(base_asset, 0.0) - qty)

        # Remove and return
        cancelled_order = self.pending_orders.pop(idx)
        cancelled_order["status"] = "CANCELED"
        # Robustly compute updateTime in ms
        if hasattr(self._tick, "to_pydatetime"):
            tick_dt = self._tick.to_pydatetime()
            update_ms = int(tick_dt.timestamp() * 1000)
        elif isinstance(self._tick, int):
            try:
                index_ts = self._data.index[self._tick]
                if hasattr(index_ts, "to_pydatetime"):
                    index_dt = index_ts.to_pydatetime()
                else:
                    index_dt = index_ts
                update_ms = int(index_dt.timestamp() * 1000)
            except Exception:
                update_ms = 0
        else:
            update_ms = int(self._tick.timestamp() * 1000)
        cancelled_order["updateTime"] = update_ms
        return cancelled_order

    def get_account(self) -> dict[str, Any]:
        """Return balances array with free/locked for base and quote assets."""
        symbol = self._data.name if hasattr(self._data, "name") else None
        if not symbol:
            return {"balances": []}
        base_asset, quote_asset = self._get_assets(symbol)
        base_total, quote_total = self._get_totals(symbol)
        self._ensure_locked_keys(symbol)
        base_free = base_total - self._locked.get(base_asset, 0.0)
        quote_free = quote_total - self._locked.get(quote_asset, 0.0)
        balances = [
            {
                "asset": base_asset,
                "free": str(base_free),
                "locked": str(self._locked.get(base_asset, 0.0)),
            },
            {
                "asset": quote_asset,
                "free": str(quote_free),
                "locked": str(self._locked.get(quote_asset, 0.0)),
            },
        ]
        return {"balances": balances}

    def get_exchange_info(self) -> dict[str, Any]:
        """Mocks get_exchange_info with basic precision."""
        return {
            "symbols": [
                {
                    "symbol": "ADAUSDC",
                    "baseAssetPrecision": 8,
                    "quoteAssetPrecision": 8,
                    "filters": [
                        {"filterType": "LOT_SIZE", "stepSize": "0.1"},
                        {"filterType": "PRICE_FILTER", "tickSize": "0.0001"},
                        {"filterType": "MIN_NOTIONAL", "minNotional": "10.0"},
                    ],
                }
            ]
        }
