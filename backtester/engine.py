"""
Backtesting Engine

The core component that orchestrates the backtest, bringing together the
data, strategy, and broker.
"""

import pandas as pd
from loguru import logger

from backtester.broker import Broker
from backtester.data_loader import load_klines_to_dataframe
from backtester.mock_client import MockBinanceClient
from backtester.strategy import Strategy


class BacktestEngine:
    """
    The main engine for running backtests.
    """

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        strategy_class: type[Strategy],
        initial_cash: float = 10_000.0,
        start_ts: int | None = None,
        end_ts: int | None = None,
        disable_trading_logs: bool = False,
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.strategy_class = strategy_class
        self.initial_cash = initial_cash
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.disable_trading_logs = disable_trading_logs

        self.broker = Broker(initial_cash=self.initial_cash)
        self.data: pd.DataFrame = pd.DataFrame()

    def _prepare_data(self):
        """Loads data using the DataLoader."""
        self.data = load_klines_to_dataframe(
            self.symbol,
            self.timeframe,
            start_ts=self.start_ts,
            end_ts=self.end_ts,
        )
        if self.data.empty:
            raise ValueError("No data loaded, cannot run backtest.")
        self.data.name = self.symbol

    def _clear_previous_orders(self):
        """No-op for external tables to avoid side effects in backtests.
        Backtests should not modify trading system tables.
        """
        return None

    def _install_trading_log_stubs(self):
        if not self.disable_trading_logs:
            return None

        import database.trading_log_crud as trading_log_crud

        originals_enabled = trading_log_crud.is_trading_log_enabled()
        trading_log_crud.set_trading_log_enabled(False)

        logger.debug("Trading log persistence disabled for backtest run")

        def restore() -> None:
            trading_log_crud.set_trading_log_enabled(originals_enabled)

        return restore

    def _check_pending_orders(self, candle, mock_client):
        """Checks and executes pending orders based on the current candle."""
        for order in mock_client.pending_orders[:]:
            if order["symbol"] != self.symbol:
                continue
            if not self._pending_order_triggered(order, candle):
                continue
            self._execute_pending_order(order, candle, mock_client)

    def _pending_order_triggered(self, order: dict, candle) -> bool:
        """Return True when a stop order is triggered by current candle highs/lows."""
        stop_price = float(order["stopPrice"])
        if order["side"] == "BUY":
            return candle["high"] >= stop_price
        return candle["low"] <= stop_price

    def _execute_pending_order(self, order: dict, candle, mock_client) -> None:
        """Execute a triggered pending order and record the fill."""
        stop_price = float(order["stopPrice"])
        qty = float(order["origQty"])
        if order["side"] == "BUY":
            self.broker.buy(order["symbol"], qty, stop_price)
        else:
            self.broker.sell(order["symbol"], qty, stop_price)

        _, filled = mock_client._record_filled_order(
            symbol=order["symbol"],
            side=order["side"],
            qty=qty,
            price=stop_price,
            timestamp=candle.name.to_pydatetime(),
            order_id=order["orderId"],
            client_order_id=order["clientOrderId"],
        )
        mock_client.executed_orders.append(filled)
        mock_client.pending_orders.remove(order)

    def run(self):
        """Runs the backtest."""
        restore_logs = None
        try:
            self._clear_previous_orders()
            self._prepare_data()

            restore_logs = self._install_trading_log_stubs()

            mock_client = MockBinanceClient(self.broker, self.data)
            strategy = self.strategy_class(
                self.broker,
                self.data,
                mock_client,
                symbol=self.symbol,
                timeframe=self.timeframe,
            )
            strategy.init()

            # Main event loop - use efficient iteration instead of iterrows()
            data_length = len(self.data)
            for i in range(data_length):
                # Get the index value (timestamp) for the current row
                tick_index = self.data.index[i]
                mock_client.update_tick(tick_index)
                # Strategy runs before evaluating fills so it can cancel/update orders
                strategy.next()
                mock_client.process_pending_orders_now()

            final_value = self.broker.get_portfolio_value(
                {self.symbol: self.data["close"].iloc[-1]}
            )
            return final_value
        finally:
            if restore_logs is not None:
                restore_logs()
