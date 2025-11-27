"""Backtesting Strategy定义."""

if __name__ == "__main__" and __package__ is None:
    raise RuntimeError(
        "请在项目根目录使用 `p -m backtester.strategy` 运行该模块, 无需手动修改 sys.path"
    )

import contextlib
from collections.abc import Callable, Iterator, Sequence
from typing import Any

from binance.exceptions import BinanceAPIException
from loguru import logger

# Important: Import the modules to be patched
from order_builder.app import run_order_builder
from shared.clock import BacktestClock, override_clock


class Strategy:
    """
    Base class for all trading strategies.
    """

    def __init__(self, broker, data, mock_client):
        self.broker = broker
        self.data = data
        self.mock_client = mock_client
        self.tick = 0

    def init(self):
        """
        Initialize the strategy. Called once before the backtest starts.
        """
        pass

    def next(self):
        """
        Step the strategy forward. Called for each data point (K-line).
        """
        self.tick += 1
        pass


class DemarkStrategy(Strategy):
    """
    An adapter strategy that runs the project's existing run_order_builder
    function within the backtesting engine.
    """

    def __init__(self, broker, data, mock_client, symbol: str, timeframe: str):
        """Store symbol/timeframe context alongside broker, data and client."""
        super().__init__(broker, data, mock_client)
        self.symbol = symbol.upper()
        self.timeframe = timeframe.lower()
        # Cache for processed kline times to avoid repeated database queries
        self._processed_kline_times: set[int] = set()

    def init(self):
        """
        Monkey-patches the real client getter to return the mock client.
        """
        super().init()
        mock_getter = self._inject_mock_client()
        self._patch_klines()
        self._patch_client_consumers(mock_getter)
        self._disable_async_notifications()
        self._cache_symbol_metadata()
        self._cache_kline_check()

    def next(self):
        """
        On each candle, run the original trading logic.
        The engine is responsible for updating the mock client's tick.
        """
        super().next()

        if self.tick < 20:
            return

        try:
            with (
                override_clock(BacktestClock(self._current_open_datetime())),
                self._suppress_notifications(),
            ):
                result = run_order_builder(
                    symbol=self.data.name, timeframe=self.timeframe
                )
                # Record processed K-line if order was placed successfully
                if hasattr(result, "order_id") and result.order_id:
                    # Extract K-line time from signal klines
                    try:
                        from indicators.demark.binance_demark import (
                            demark_with_ibkr_api,
                        )

                        _, _, _, signal_klines = demark_with_ibkr_api(
                            self.data.name, self.timeframe
                        )
                        kline_time = int(signal_klines[-1]["open_time"])
                        self._record_processed_kline(kline_time)
                    except Exception:
                        pass
        except (ValueError, BinanceAPIException):
            # Suppress expected business validation errors and API errors
            pass
        except Exception:
            # Only log unexpected errors
            logger.exception("Error in run_order_builder at tick %s", self.tick)

    # --- Helper methods -------------------------------------------------

    def _inject_mock_client(self) -> Callable[[], Any]:
        """Replace the global client getter so strategy code uses mock client."""
        import ibkr_api.common as common_module

        def get_mock_client() -> Any:
            return self.mock_client

        with contextlib.suppress(Exception):
            common_module._client_cache = self.mock_client  # type: ignore[attr-defined]
        common_module.get_configured_client = get_mock_client
        return get_mock_client

    def _patch_klines(self) -> None:
        """Ensure all kline helpers respect the mock client's current tick."""
        import ibkr_api.get_klines as get_klines_module
        import indicators.atr.binance_atr as atr_binance_module
        import indicators.demark.binance_demark as demark_binance_module
        import indicators.ema.binance_ema as ema_binance_module
        import indicators.supertrend.binance_supertrend as supertrend_binance_module
        import indicators.td_iven.binance_td_iven as td_iven_binance_module

        patched = self._patched_klines
        get_klines_module.klines = patched
        if hasattr(demark_binance_module, "klines"):
            demark_binance_module.klines = patched
        if hasattr(td_iven_binance_module, "klines"):
            td_iven_binance_module.klines = patched
        if hasattr(atr_binance_module, "klines"):
            atr_binance_module.klines = patched
        if hasattr(ema_binance_module, "klines"):
            ema_binance_module.klines = patched
        if hasattr(supertrend_binance_module, "klines"):
            supertrend_binance_module.klines = patched

    def _patched_klines(
        self,
        client: Any,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
    ) -> list[dict[str, object]]:
        """Adapter for klines that truncates history to the active backtest tick."""
        end_ms = self._derive_end_timestamp()
        kwargs = {"endTime": end_ms} if end_ms is not None else {}
        raw_klines = client.get_klines(
            symbol=symbol.upper(), interval=interval, limit=limit, **kwargs
        )
        return [self._format_kline_row(kline) for kline in raw_klines]

    def _derive_end_timestamp(self) -> int | None:
        """Compute the endTime parameter based on the mock client's tick pointer."""
        tick = getattr(self.mock_client, "_tick", None)
        try:
            if hasattr(tick, "to_pydatetime"):
                return int(tick.to_pydatetime().timestamp() * 1000)
            if isinstance(tick, int):
                index_ts = self.data.index[tick]
                if hasattr(index_ts, "to_pydatetime"):
                    return int(index_ts.to_pydatetime().timestamp() * 1000)
                return int(index_ts.timestamp() * 1000)
            if tick is not None:
                return int(tick.timestamp() * 1000)
        except Exception:
            return None
        return None

    def _format_kline_row(self, kline: Sequence[object]) -> dict[str, object]:
        """Convert raw kline arrays to dict shape consumed by strategy helpers."""
        return {
            "open_time": kline[0],
            "open": kline[1],
            "high": kline[2],
            "low": kline[3],
            "close": kline[4],
            "volume": kline[5],
            "close_time": kline[6],
            "quote_asset_volume": kline[7],
            "number_of_trades": kline[8],
            "taker_buy_base_asset_volume": kline[9],
            "taker_buy_quote_asset_volume": kline[10],
        }

    def _patch_client_consumers(self, mock_getter: Callable[[], Any]) -> None:
        """Rebind helper modules that cached the real get_configured_client."""
        import ibkr_api.cancel_order as cancel_order_module
        import ibkr_api.get_account as get_account_module
        import ibkr_api.get_all_orders
        import ibkr_api.get_balance as get_balance_module
        import ibkr_api.get_exchange_info as get_exchange_info_module
        import ibkr_api.get_open_orders as get_open_orders_module
        import ibkr_api.get_symbol_ticker as get_symbol_ticker_module
        import indicators.atr.binance_atr as atr_binance_module
        import indicators.demark.binance_demark
        import indicators.ema.binance_ema as ema_binance_module
        import indicators.supertrend.binance_supertrend
        import order_builder.order.stop_market as stop_market_module
        import order_checker.common

        modules_to_patch = (
            ema_binance_module,
            indicators.demark.binance_demark,
            atr_binance_module,
            order_checker.common,
            indicators.supertrend.binance_supertrend,
            stop_market_module,
            ibkr_api.get_all_orders,
            get_balance_module,
            get_account_module,
            get_symbol_ticker_module,
            get_open_orders_module,
            cancel_order_module,
            get_exchange_info_module,
        )
        for module in modules_to_patch:
            if hasattr(module, "get_configured_client"):
                module.get_configured_client = mock_getter  # type: ignore[assignment]

        with contextlib.suppress(Exception):
            get_balance_module.get_configured_client()

    def _disable_async_notifications(self) -> None:
        """Silence async notifier side-effects during backtests."""
        import database.trading_log_crud as trading_log_crud_module
        import shared.async_notifier as async_notifier_module

        def _noop(*_: object, **__: object) -> None:
            return None

        async_notifier_module.enqueue_trading_log_created = _noop  # type: ignore
        async_notifier_module.enqueue_trading_log_updated = _noop  # type: ignore
        trading_log_crud_module.enqueue_trading_log_created = _noop  # type: ignore
        trading_log_crud_module.enqueue_trading_log_updated = _noop  # type: ignore
        return None

    def _cache_symbol_metadata(self) -> None:
        """Cache frequently accessed symbol information for repeated calls."""
        try:
            import database.crud as crud_module
            import database.symbol_crud as symbol_crud_module
            import order_builder.app as order_builder_app_module
            import order_builder.calculation as calculation_module
            import order_checker.common
            import order_checker.signal_validation as signal_validation_module

            original_get_symbol_info = crud_module.get_symbol_info
            original_get_symbol_timeframe_config = (
                crud_module.get_symbol_timeframe_config
            )
            original_get_validated_min_notional = (
                symbol_crud_module.get_validated_min_notional
            )

            cached_symbol_info = original_get_symbol_info(self.symbol)
            cached_tf_config = original_get_symbol_timeframe_config(
                self.symbol, self.timeframe
            )
            cached_min_notional = original_get_validated_min_notional(self.symbol)

            def cached_get_symbol_info(symbol: str):
                if symbol.upper() == self.symbol:
                    return cached_symbol_info
                return original_get_symbol_info(symbol)

            def cached_get_symbol_timeframe_config(symbol: str, timeframe: str):
                if (
                    symbol.upper() == self.symbol
                    and timeframe.lower() == self.timeframe
                ):
                    return cached_tf_config
                return original_get_symbol_timeframe_config(symbol, timeframe)

            def cached_get_validated_min_notional(symbol: str):
                if symbol.upper() == self.symbol:
                    return cached_min_notional
                return original_get_validated_min_notional(symbol)

            crud_module.get_symbol_info = cached_get_symbol_info
            crud_module.get_symbol_timeframe_config = cached_get_symbol_timeframe_config
            symbol_crud_module.get_validated_min_notional = (
                cached_get_validated_min_notional
            )

            order_builder_app_module.get_symbol_info = cached_get_symbol_info
            order_builder_app_module.get_symbol_timeframe_config = (
                cached_get_symbol_timeframe_config
            )
            order_builder_app_module.get_validated_min_notional = (
                cached_get_validated_min_notional
            )

            calculation_module.get_symbol_info = cached_get_symbol_info
            calculation_module.get_symbol_timeframe_config = (
                cached_get_symbol_timeframe_config
            )

            signal_validation_module.get_symbol_timeframe_config = (
                cached_get_symbol_timeframe_config
            )

            order_checker.common.get_symbol_info = cached_get_symbol_info

        except Exception:  # pragma: no cover - best effort fallback
            return None

    def _cache_kline_check(self) -> None:
        """Cache check_kline_already_processed() to avoid repeated database queries.

        Instead of querying the database for every K-line, we intercept the function
        and maintain an in-memory set of processed K-line times. When run_order_builder()
        successfully completes and places an order, we add the K-line time to the cache.
        """
        try:
            import database.trading_log_crud as trading_log_crud_module

            original_check = trading_log_crud_module.check_kline_already_processed

            def cached_check(symbol: str, timeframe: str, kline_time: int) -> bool:
                # Only cache for the current symbol/timeframe being backtested
                if symbol.upper() != self.symbol or timeframe.lower() != self.timeframe:
                    return original_check(symbol, timeframe, kline_time)

                # Return cached result if available
                return kline_time in self._processed_kline_times

            # Replace the function with cached version
            trading_log_crud_module.check_kline_already_processed = cached_check

            # Also replace in order_builder module if it's already imported
            try:
                import order_builder.app as order_builder_app_module

                order_builder_app_module.check_kline_already_processed = cached_check
            except Exception:
                pass

        except Exception:  # pragma: no cover - best effort fallback
            return None

    def _record_processed_kline(self, kline_time: int) -> None:
        """Record a successfully processed K-line to prevent re-processing."""
        self._processed_kline_times.add(kline_time)

    def _current_open_datetime(self):
        """Return datetime corresponding to the current mock tick."""
        tick = getattr(self.mock_client, "_tick", None)
        try:
            if hasattr(tick, "to_pydatetime"):
                return tick.to_pydatetime()
            if isinstance(tick, int):
                index_value = self.data.index[tick]
            else:
                index_value = tick or self.data.index[-1]
            if hasattr(index_value, "to_pydatetime"):
                return index_value.to_pydatetime()
            return index_value
        except Exception:
            fallback = self.data.index[-1]
            return (
                fallback.to_pydatetime()
                if hasattr(fallback, "to_pydatetime")
                else fallback
            )

    @contextlib.contextmanager
    def _suppress_notifications(self) -> Iterator[None]:
        """Temporarily disable trading log side-effects while executing a tick."""
        try:
            import database.trading_log_crud as trading_log_crud_module
        except Exception:
            yield
            return

        orig_created = getattr(
            trading_log_crud_module, "publish_trading_log_event", None
        )
        orig_updated = getattr(
            trading_log_crud_module, "publish_trading_log_updated", None
        )
        orig_requests = getattr(trading_log_crud_module, "requests", None)

        trading_log_crud_module.publish_trading_log_event = (  # type: ignore[assignment]
            lambda *_args, **_kwargs: None
        )
        trading_log_crud_module.publish_trading_log_updated = None  # type: ignore[assignment]
        trading_log_crud_module.requests = None  # type: ignore[assignment]
        try:
            yield
        finally:
            if orig_created is not None:
                trading_log_crud_module.publish_trading_log_event = orig_created  # type: ignore[assignment]
            if orig_updated is not None or hasattr(
                trading_log_crud_module, "publish_trading_log_updated"
            ):
                trading_log_crud_module.publish_trading_log_updated = orig_updated  # type: ignore[assignment]
            trading_log_crud_module.requests = orig_requests  # type: ignore[assignment]
