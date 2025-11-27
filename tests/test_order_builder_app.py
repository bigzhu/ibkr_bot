import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import order_builder.app as order_builder_app
import shared.constants as shared_constants
from order_builder.unmatched_orders import count_effective_unmatched_orders


def _setup_run_order_builder_stubs(monkeypatch) -> SimpleNamespace:
    """Patch heavy dependencies so we can unit-test run_order_builder logic."""

    state = SimpleNamespace()
    state.symbol_config = SimpleNamespace(
        monitor_delay=0,
        demark_buy=9,
        demark_sell=9,
    )
    state.symbol_info = SimpleNamespace(
        min_notional="1",
        step_size="0.1",
        tick_size="0.1",
        min_qty="0.01",
        max_qty="1000000",
        min_price="0.0001",
        max_price="1000000",
    )
    state.unmatched_orders = [
        SimpleNamespace(
            unmatched_qty="1",
            average_price="2",
            order_no="ORDER-1",
            time="2023-01-01 00:00:00",
        ),
    ]
    state.signal_result = ("SELL", 10, False, [{"open_time": 1}])
    state.open_orders = [{"side": "SELL"}]

    monkeypatch.setattr(
        order_builder_app,
        "_validate_and_get_signal",
        lambda *args, **kwargs: state.signal_result,
    )
    monkeypatch.setattr(
        order_builder_app,
        "check_kline_already_processed",
        lambda *args, **kwargs: False,
    )

    def fake_sync(symbol: str, timeframe: str):
        return state.symbol_config, state.symbol_info, state.unmatched_orders

    monkeypatch.setattr(order_builder_app, "_sync_and_cleanup_orders", fake_sync)
    monkeypatch.setattr(
        order_builder_app,
        "create_preliminary_trading_log_record",
        lambda *args, **kwargs: 42,
    )
    monkeypatch.setattr(
        order_builder_app,
        "calculate_qty",
        lambda *args, **kwargs: (
            Decimal("1"),
            Decimal("3"),
            Decimal("0.01"),
        ),
    )
    monkeypatch.setattr(
        order_builder_app,
        "get_user_balance",
        lambda *args, **kwargs: Decimal("10"),
    )
    monkeypatch.setattr(order_builder_app, "update_trading_log", lambda *_, **__: None)
    monkeypatch.setattr(
        order_builder_app,
        "get_open_orders_by_symbol_timeframe",
        lambda *args, **kwargs: state.open_orders,
    )
    monkeypatch.setattr(order_builder_app, "check", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        order_builder_app,
        "execute_order",
        lambda *args, **kwargs: 999,
    )
    return state


def _stub_config(monkeypatch) -> None:
    monkeypatch.setattr(
        order_builder_app,
        "get_symbol_timeframe_config",
        lambda *_, **__: SimpleNamespace(
            monitor_delay=0,
            demark_buy=9,
            demark_sell=9,
        ),
    )
    monkeypatch.setattr(order_builder_app.time, "sleep", lambda *_: None)


def test_validate_signal_requires_threshold(monkeypatch) -> None:
    _stub_config(monkeypatch)
    monkeypatch.setattr(
        order_builder_app,
        "demark_with_binance_api",
        lambda *_, **__: ("BUY", 8, False, []),
    )

    assert order_builder_app._validate_and_get_signal("ADAUSDC", "15m") is None


def test_validate_signal_accepts_valid_buy_signal(monkeypatch) -> None:
    _stub_config(monkeypatch)
    monkeypatch.setattr(
        order_builder_app,
        "demark_with_binance_api",
        lambda *_, **__: ("BUY", 10, True, []),
    )

    result = order_builder_app._validate_and_get_signal("ADAUSDC", "15m")
    assert result == ("BUY", 10, True, [])


def test_validate_signal_accepts_sell_without_countdown(monkeypatch) -> None:
    _stub_config(monkeypatch)
    monkeypatch.setattr(
        order_builder_app,
        "demark_with_binance_api",
        lambda *_, **__: ("SELL", 10, False, []),
    )

    result = order_builder_app._validate_and_get_signal("ADAUSDC", "15m")
    assert result == ("SELL", 10, False, [])


def test_run_order_builder_cancels_opposite_orders_when_enabled(monkeypatch) -> None:
    _setup_run_order_builder_stubs(monkeypatch)

    cancel_calls: list[tuple[str, str]] = []

    def fake_cancel(symbol: str, side: str) -> None:
        cancel_calls.append((symbol, side))

    monkeypatch.setattr(order_builder_app, "cancel_opposite_open_orders", fake_cancel)
    monkeypatch.setattr(
        shared_constants,
        "CANCEL_OPPOSITE_OPEN_ORDERS_AFTER_SIGNAL",
        True,
    )

    result = order_builder_app.run_order_builder("ADAUSDC", "15m")

    assert result["action"] == "ORDER_PLACED"
    assert cancel_calls == [("ADAUSDC", "SELL")]


def test_run_order_builder_skips_cancel_when_disabled(monkeypatch) -> None:
    _setup_run_order_builder_stubs(monkeypatch)

    cancel_calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        order_builder_app,
        "cancel_opposite_open_orders",
        lambda *args, **kwargs: cancel_calls.append(args),
    )
    monkeypatch.setattr(
        shared_constants,
        "CANCEL_OPPOSITE_OPEN_ORDERS_AFTER_SIGNAL",
        False,
    )

    result = order_builder_app.run_order_builder("ADAUSDC", "15m")

    assert result["action"] == "ORDER_PLACED"
    assert cancel_calls == []


def test_count_effective_unmatched_orders_filters_dust() -> None:
    min_notional = Decimal("10")
    orders = [
        SimpleNamespace(unmatched_qty="0.5", average_price="10"),  # below threshold
        SimpleNamespace(unmatched_qty="5", average_price="2"),  # meets threshold
        SimpleNamespace(unmatched_qty="1", average_price="0"),  # invalid price
    ]

    count = count_effective_unmatched_orders(orders, min_notional)

    assert count == 1


def test_collect_sub_minimal_unmatched_orders() -> None:
    min_notional = Decimal("10")
    orders = [
        SimpleNamespace(order_no="A", unmatched_qty="0.5", average_price="10"),
        SimpleNamespace(order_no="B", unmatched_qty="5", average_price="2"),
    ]
    result = order_builder_app._collect_sub_minimal_unmatched(orders, min_notional)
    assert result == [("A", Decimal("0.5"))]

    orders = [
        SimpleNamespace(order_no="C", unmatched_qty="0", average_price="1"),
        SimpleNamespace(order_no="D", unmatched_qty="5", average_price="2"),
    ]
    assert order_builder_app._collect_sub_minimal_unmatched(orders, min_notional) == []


def test_run_order_builder_requires_setup_or_age(monkeypatch) -> None:
    state = _setup_run_order_builder_stubs(monkeypatch)
    now = datetime(2024, 1, 1, 10, tzinfo=UTC)
    monkeypatch.setattr(order_builder_app, "now_utc", lambda: now)

    recent_time = (now - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")

    def fake_sync(symbol: str, timeframe: str):
        symbol_config = SimpleNamespace()
        symbol_info = SimpleNamespace(min_notional="1")
        unmatched_orders = [
            SimpleNamespace(
                unmatched_qty="1",
                average_price="2",
                time=recent_time,
            ),
        ]
        return symbol_config, symbol_info, unmatched_orders

    monkeypatch.setattr(order_builder_app, "_sync_and_cleanup_orders", fake_sync)
    state.signal_result = ("SELL", 5, False, [{"open_time": 1}])
    result = order_builder_app.run_order_builder("ADAUSDC", "15m")
    assert result["action"] == "KLINE_ALREADY_PROCESSED"


def test_run_order_builder_allows_when_old_unmatched(monkeypatch) -> None:
    state = _setup_run_order_builder_stubs(monkeypatch)
    now = datetime(2024, 1, 1, 10, tzinfo=UTC)
    monkeypatch.setattr(order_builder_app, "now_utc", lambda: now)

    old_time = (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")

    def fake_sync(symbol: str, timeframe: str):
        symbol_config = SimpleNamespace()
        symbol_info = SimpleNamespace(min_notional="1")
        unmatched_orders = [
            SimpleNamespace(
                unmatched_qty="1",
                average_price="2",
                time=old_time,
            ),
        ]
        return symbol_config, symbol_info, unmatched_orders

    monkeypatch.setattr(order_builder_app, "_sync_and_cleanup_orders", fake_sync)
    state.signal_result = ("SELL", 2, False, [{"open_time": 1}])
    result = order_builder_app.run_order_builder("ADAUSDC", "15m")
    assert result["action"] == "ORDER_PLACED"


def test_run_order_builder_requires_unmatched_orders(monkeypatch) -> None:
    _setup_run_order_builder_stubs(monkeypatch)

    def fake_sync_no_orders(symbol: str, timeframe: str):
        symbol_config = SimpleNamespace()
        symbol_info = SimpleNamespace(min_notional="1")
        return symbol_config, symbol_info, []

    monkeypatch.setattr(
        order_builder_app, "_sync_and_cleanup_orders", fake_sync_no_orders
    )
    result = order_builder_app.run_order_builder("ADAUSDC", "15m")
    assert result["action"] == "KLINE_ALREADY_PROCESSED"


def test_run_order_builder_allows_when_setup_high(monkeypatch) -> None:
    state = _setup_run_order_builder_stubs(monkeypatch)
    now = datetime(2024, 1, 1, 10, tzinfo=UTC)
    monkeypatch.setattr(order_builder_app, "now_utc", lambda: now)

    recent_time = (now - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")

    def fake_sync(symbol: str, timeframe: str):
        symbol_config = SimpleNamespace()
        symbol_info = SimpleNamespace(min_notional="1")
        unmatched_orders = [
            SimpleNamespace(
                unmatched_qty="1",
                average_price="2",
                time=recent_time,
            ),
        ]
        return symbol_config, symbol_info, unmatched_orders

    monkeypatch.setattr(order_builder_app, "_sync_and_cleanup_orders", fake_sync)
    state.signal_result = ("BUY", 10, True, [{"open_time": 1}])

    result = order_builder_app.run_order_builder("ADAUSDC", "15m")

    assert result["action"] == "ORDER_PLACED"


def test_run_order_builder_allows_when_old_over_one_hour(monkeypatch) -> None:
    state = _setup_run_order_builder_stubs(monkeypatch)
    now = datetime(2024, 1, 1, 10, tzinfo=UTC)
    monkeypatch.setattr(order_builder_app, "now_utc", lambda: now)

    old_time = (now - timedelta(hours=1, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")

    def fake_sync(symbol: str, timeframe: str):
        symbol_config = SimpleNamespace()
        symbol_info = SimpleNamespace(min_notional="1")
        unmatched_orders = [
            SimpleNamespace(
                unmatched_qty="1",
                average_price="2",
                time=old_time,
            ),
        ]
        return symbol_config, symbol_info, unmatched_orders

    monkeypatch.setattr(order_builder_app, "_sync_and_cleanup_orders", fake_sync)
    state.signal_result = ("SELL", 9, False, [{"open_time": 1}])

    result = order_builder_app.run_order_builder("ADAUSDC", "15m")

    assert result["action"] == "ORDER_PLACED"


def test_run_order_builder_places_protective_sell(monkeypatch) -> None:
    state = _setup_run_order_builder_stubs(monkeypatch)
    state.open_orders = []  # 无SELL订单
    state.unmatched_orders = [
        SimpleNamespace(
            unmatched_qty="2",
            average_price="2",
            order_no="ORDER-STOP",
            time="2023-01-01 00:00:00",
        ),
    ]

    stop_calls: list[dict[str, str]] = []

    monkeypatch.setattr(
        order_builder_app,
        "get_trading_log_by_order_id",
        lambda order_id: SimpleNamespace(low=Decimal("1.5")),
    )
    monkeypatch.setattr(
        order_builder_app,
        "place_order_with_retry",
        lambda **kwargs: stop_calls.append(kwargs) or "STOP-ORDER",
    )

    result = order_builder_app.run_order_builder("ADAUSDC", "15m")

    assert result["action"] == "ORDER_PLACED"
    assert stop_calls, "should place protective SELL"
    assert stop_calls[0]["stop_price"] == "1.5"
