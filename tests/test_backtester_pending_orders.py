import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backtester.broker import Broker
from backtester.mock_client import MockBinanceClient


def _sample_klines() -> pd.DataFrame:
    index = pd.to_datetime(
        [1762992600000, 1762992900000],
        unit="ms",
        utc=True,
    )
    data = pd.DataFrame(
        {
            "open": [1.9754, 1.9706],
            "high": [1.9760, 1.9780],
            "low": [1.9685, 1.9702],
            "close": [1.9712, 1.9752],
            "volume": [1000, 1000],
            "quote_asset_volume": [1000, 1000],
            "taker_buy_base_asset_volume": [500, 500],
            "taker_buy_quote_asset_volume": [500, 500],
        },
        index=index,
    )
    data.index.name = "open_time"
    data.name = "SUIUSDC"
    return data


def test_stop_order_executes_within_same_candle(monkeypatch):
    monkeypatch.setattr(
        "backtester.mock_client.get_symbol_info",
        lambda symbol: SimpleNamespace(base_asset="SUI", quote_asset="USDC"),
    )
    broker = Broker(initial_cash=10_000)
    data = _sample_klines()
    client = MockBinanceClient(broker, data)

    current_tick = data.index[1]
    client.update_tick(current_tick)

    client.create_order(
        symbol="SUIUSDC",
        side="BUY",
        type="STOP_LOSS",
        quantity="3",
        stopPrice="1.978",
        newClientOrderId="5m",
    )

    assert client.pending_orders  # queued before processing

    client.process_pending_orders_now()

    assert not client.pending_orders
    assert client.executed_orders
    executed_order = client.executed_orders[-1]
    assert executed_order["side"] == "BUY"
    assert executed_order["status"] == "FILLED"
