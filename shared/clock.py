"""
Shared clock utilities for injectable time source (UTC-aware).

Usage:
- Production: use default RealClock (datetime.now(UTC)).
- Backtest: override with BacktestClock that returns current candle time.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now_utc(self) -> datetime:  # pragma: no cover - protocol signature
        ...


class RealClock:
    def now_utc(self) -> datetime:
        return datetime.now(UTC)


class _ClockHolder:
    def __init__(self) -> None:
        self._local = threading.local()
        self._default = RealClock()

    def get(self) -> Clock:
        clk = getattr(self._local, "clock", None)
        return clk if clk is not None else self._default

    def set(self, clock: Clock | None) -> None:
        self._local.clock = clock


_holder = _ClockHolder()


def set_clock(clock: Clock) -> None:
    """Set current thread's clock implementation."""
    _holder.set(clock)


def reset_clock() -> None:
    """Reset to default clock for the current thread."""
    _holder.set(None)


def now_utc() -> datetime:
    """Get current UTC time from the active clock (tz-aware)."""
    return _holder.get().now_utc()


@contextmanager
def override_clock(clock: Clock):
    """Temporarily override the current clock within a context."""
    prev = _holder.get()
    set_clock(clock)
    try:
        yield
    finally:
        # Safely restore previous clock
        set_clock(prev)


class BacktestClock:
    """Simple clock that returns a fixed UTC datetime value."""

    def __init__(self, current_utc: datetime) -> None:
        # Ensure tz-aware UTC
        self._now = (
            current_utc
            if current_utc.tzinfo is not None
            else current_utc.replace(tzinfo=UTC)
        )

    def now_utc(self) -> datetime:
        return self._now
