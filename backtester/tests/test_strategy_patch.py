import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import indicators.td_iven.binance_td_iven as td_module
from backtester.strategy import DemarkStrategy


def test_patch_klines_updates_td_iven_module() -> None:
    strategy = DemarkStrategy(
        broker=SimpleNamespace(),
        data=SimpleNamespace(name="ADAUSDC"),
        mock_client=SimpleNamespace(),
        symbol="ADAUSDC",
        timeframe="1h",
    )

    strategy._patch_klines()

    assert td_module.klines == strategy._patched_klines
