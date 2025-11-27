"""
shared.time_utils 时间函数测试
"""

from shared.time_utils import (
    get_utc_datetime,
    get_utc_timestamp_ms,
    timestamp_ms_to_utc_str,
)


def test_get_utc_timestamp_ms_monotonic():
    t1 = get_utc_timestamp_ms()
    t2 = get_utc_timestamp_ms()
    assert isinstance(t1, int) and isinstance(t2, int)
    assert t2 >= t1


def test_get_utc_datetime_tz():
    dt = get_utc_datetime()
    # 必须带时区信息,且为 UTC
    assert dt.tzinfo is not None
    assert str(dt.tzinfo) == "UTC"


def test_timestamp_ms_to_utc_str_format():
    ts = 0  # 1970-01-01 00:00:00 UTC
    s = timestamp_ms_to_utc_str(ts)
    assert s == "1970-01-01 00:00:00"
