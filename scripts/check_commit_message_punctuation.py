#!/usr/bin/env python3
"""
Validate commit message for full-width Chinese punctuation.
Exit non-zero if found to block the commit.
"""

import re
import sys
from pathlib import Path

# 常见全角/中文标点字符范围与单点字符
FULLWIDTH_PATTERN = re.compile(
    r"[\uFF00-\uFFEF\u3000-\u303F\u2018\u2019\u201C\u201D\u2026]"
)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check_commit_message_punctuation.py <commit-msg-file>")
        return 2

    msg_path = Path(sys.argv[1])
    text = msg_path.read_text(encoding="utf-8", errors="ignore")

    if FULLWIDTH_PATTERN.search(text):
        print(
            "ERROR: Commit message contains full-width punctuation. "
            + "Please use ASCII punctuation.\n"
            + "Hint: See AGENTS.md punctuation rules."
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
