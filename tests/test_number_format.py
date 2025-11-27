"""
shared.number_format 函数测试
"""

import sys
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.number_format import format_decimal, format_percentage


def test_format_decimal_variants():
    assert format_decimal(Decimal("0.78520000")) == "0.7852"
    assert format_decimal(Decimal("54.50000000")) == "54.5"
    assert format_decimal(Decimal("1.00000000")) == "1"
    assert format_decimal(Decimal("0.00000000")) == "0"
    assert format_decimal("12.3400") == "12.34"
    assert format_decimal(Decimal("0.5580000000000000515143483426")) == "0.558"


def test_format_percentage():
    assert format_percentage(0.5221599) == "0.52%"
    assert format_percentage(1.4) == "1.4%"
    assert format_percentage(0) == "0%"
