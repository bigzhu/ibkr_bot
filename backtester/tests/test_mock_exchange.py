import sys
from pathlib import Path

# Ensure project root on sys.path for package imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pandas as pd
import pytest
from binance.exceptions import BinanceAPIException

from backtester.broker import Broker
from backtester.mock_client import MockBinanceClient


@pytest.fixture
def sample_data():
    # Build 3 one-minute candles
    t0 = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)
    idx = pd.DatetimeIndex([t0, t0 + timedelta(minutes=1), t0 + timedelta(minutes=2)])
    df = pd.DataFrame(
        {
            "open": [4.0, 5.5, 6.0],
            "high": [4.5, 6.2, 6.5],
            "low": [3.5, 5.0, 5.5],
            "close": [4.2, 6.0, 6.1],
            "volume": [1000, 1000, 1000],
            "quote_asset_volume": [0, 0, 0],
            "taker_buy_base_asset_volume": [0, 0, 0],
            "taker_buy_quote_asset_volume": [0, 0, 0],
        },
        index=idx,
    )
    df.name = "ADAUSDC"
    return df


def patch_symbol_info(monkeypatch):
    # Patch get_symbol_info used inside MockBinanceClient
    import backtester.mock_client as mc

    def _fake_get_symbol_info(symbol: str):
        return SimpleNamespace(base_asset="ADA", quote_asset="USDC")

    monkeypatch.setattr(mc, "get_symbol_info", _fake_get_symbol_info)


def test_stop_loss_buy_fill_next_tick(monkeypatch, sample_data):
    patch_symbol_info(monkeypatch)

    broker = Broker(initial_cash=100.0)
    client = MockBinanceClient(broker, sample_data)

    # Tick 0: process any existing pending orders (none)
    t0 = sample_data.index[0]
    client.update_tick(t0)

    # Initial account: quote free=100, base free=0
    acct = client.get_account()
    usdc = next(b for b in acct["balances"] if b["asset"] == "USDC")
    ada = next(b for b in acct["balances"] if b["asset"] == "ADA")
    assert usdc["free"] == "100.0" or float(usdc["free"]) == 100.0
    assert float(ada["free"]) == 0.0

    # Place STOP_LOSS BUY qty=10 at stop=5 (reserve 50 USDC)
    order = client.create_order(
        symbol="ADAUSDC",
        side="BUY",
        type="STOP_LOSS",
        quantity="10",
        stopPrice="5",
    )
    assert order["status"] == "NEW"

    # After reservation: quote locked=50, free=50
    acct = client.get_account()
    usdc = next(b for b in acct["balances"] if b["asset"] == "USDC")
    assert pytest.approx(float(usdc["locked"])) == 50.0
    assert pytest.approx(float(usdc["free"])) == 50.0

    # Next tick (t1) should trigger as high >= 5
    t1 = sample_data.index[1]
    client.update_tick(t1)
    client.process_pending_orders_now()

    # Filled orders should contain one FILLED
    filled = client.get_all_orders(symbol="ADAUSDC")
    assert len(filled) == 1
    f = filled[0]
    assert f["status"] == "FILLED"
    assert f["price"] == "0"
    assert f["stopPrice"] == "5.0" or f["stopPrice"] == "5"
    assert f["executedQty"] == "10" or pytest.approx(float(f["executedQty"])) == 10.0
    assert pytest.approx(float(f["cummulativeQuoteQty"])) == 50.0

    # Account after fill: ADA +10, USDC 100-50, no locks
    acct = client.get_account()
    usdc = next(b for b in acct["balances"] if b["asset"] == "USDC")
    ada = next(b for b in acct["balances"] if b["asset"] == "ADA")
    assert pytest.approx(float(usdc["free"])) == 50.0
    assert pytest.approx(float(usdc["locked"])) == 0.0
    assert pytest.approx(float(ada["free"])) == 10.0


def test_cancel_releases_locked(monkeypatch, sample_data):
    patch_symbol_info(monkeypatch)

    broker = Broker(initial_cash=100.0)
    client = MockBinanceClient(broker, sample_data)

    # Tick 0
    client.update_tick(sample_data.index[0])

    # Place SELL STOP_LOSS qty=5 at 5 (reserve 5 ADA); first give ADA by buying directly via broker
    broker.positions["ADAUSDC"] = 10.0

    order = client.create_order(
        symbol="ADAUSDC",
        side="SELL",
        type="STOP_LOSS",
        quantity="5",
        stopPrice="3.8",
    )
    assert order["status"] == "NEW"

    # Check base locked
    acct = client.get_account()
    ada = next(b for b in acct["balances"] if b["asset"] == "ADA")
    assert pytest.approx(float(ada["locked"])) == 5.0

    # Cancel and ensure locked released
    cancelled = client.cancel_order(symbol="ADAUSDC", orderId=order["orderId"])
    assert cancelled["status"] == "CANCELED"

    acct = client.get_account()
    ada = next(b for b in acct["balances"] if b["asset"] == "ADA")
    assert pytest.approx(float(ada["locked"])) == 0.0


def test_reject_stop_that_would_trigger_immediately(monkeypatch, sample_data):
    patch_symbol_info(monkeypatch)
    broker = Broker(initial_cash=100.0)
    client = MockBinanceClient(broker, sample_data)

    # Set tick to first candle where close=4.2
    client.update_tick(sample_data.index[0])

    with pytest.raises(BinanceAPIException) as excinfo:
        client.create_order(
            symbol="ADAUSDC",
            side="BUY",
            type="STOP_LOSS",
            quantity="1",
            stopPrice="4.0",
        )
    assert "Stop price would trigger immediately" in str(excinfo.value)
    assert len(client.pending_orders) == 0
