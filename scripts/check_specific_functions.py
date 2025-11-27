#!/usr/bin/env python3
"""
兼容入口: 复用 check_function_calls.py 的特定函数检测模式
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_function_calls import main as run_checks


def main() -> int:
    return run_checks(["--preset", "specific"])


if __name__ == "__main__":
    raise SystemExit(main())
