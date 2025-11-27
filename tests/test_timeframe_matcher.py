import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TIMEFRAME_MATCHER_PATH = PROJECT_ROOT / "scheduler" / "timeframe_matcher.py"

spec = importlib.util.spec_from_file_location(
    "scheduler.timeframe_matcher", TIMEFRAME_MATCHER_PATH
)
if spec is None or spec.loader is None:
    raise RuntimeError("无法加载 scheduler.timeframe_matcher 模块")

timeframe_matcher = importlib.util.module_from_spec(spec)
sys.modules["scheduler.timeframe_matcher"] = timeframe_matcher
spec.loader.exec_module(timeframe_matcher)


def test_get_matched_timeframes_queries_database_every_call(monkeypatch) -> None:
    call_results = [["1m"], ["1m", "5m"], ["1m", "5m", "15m"]]
    call_count = {"value": 0}

    def fake_loader() -> list[str]:
        idx = call_count["value"]
        call_count["value"] += 1
        return call_results[idx]

    monkeypatch.setattr(
        timeframe_matcher, "_load_active_timeframes_from_db", fake_loader
    )

    now = datetime(2024, 1, 1, tzinfo=UTC)
    first_call = timeframe_matcher.get_matched_timeframes(now)
    second_call = timeframe_matcher.get_matched_timeframes(now)
    third_call = timeframe_matcher.get_matched_timeframes(now)

    assert first_call == ["1m"]
    assert second_call == ["1m", "5m"]
    assert third_call == ["1m", "5m", "15m"]
    assert call_count["value"] == 3


def test_get_matched_timeframes_returns_empty_list(monkeypatch) -> None:
    monkeypatch.setattr(
        timeframe_matcher, "_load_active_timeframes_from_db", lambda: []
    )

    result = timeframe_matcher.get_matched_timeframes(datetime(2024, 1, 1, tzinfo=UTC))

    assert result == []
