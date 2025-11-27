"""Timeframe utilities

Provide consistent helpers for matching and generating client order id
variants derived from timeframe, e.g. "15m" and "15m_1".
"""

from __future__ import annotations


def timeframe_candidates(timeframe: str) -> list[str]:
    """Return preferred client order id candidates for a timeframe.

    The first item is the base timeframe, the second is the suffixed
    alternative ("_1"). This mirrors how the system generates unique
    client order ids when the base is already taken.
    """

    tf = timeframe.lower()
    return [tf, f"{tf}_1"]


def is_timeframe_match(client_id: str, timeframe: str) -> bool:
    """Check if a client order id matches a timeframe family.

    A match occurs when the id equals the base timeframe or its
    alternative with the "_1" suffix, case-insensitive.
    """

    if not client_id or not timeframe:
        return False

    cid = client_id.lower()
    base, alt = timeframe_candidates(timeframe)
    return cid in (base, alt)


def base_timeframe(client_id: str) -> str:
    """Extract the base timeframe by stripping the optional "_1" suffix.

    Examples:
    - "5m_1" -> "5m"
    - "15m" -> "15m"
    """
    if not client_id:
        return client_id
    return client_id[:-2] if client_id.endswith("_1") else client_id
