"""
共享输出工具模块

提供统一的控制台输出功能,消除代码重复
"""

import json
from typing import Any

from loguru import logger
from rich.console import Console
from rich.json import JSON


def print_json(data: Any) -> None:
    """打印带高亮的JSON数据

    Args:
        data: 要输出的数据
    """
    console = Console()
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    json_obj = JSON(json_str)
    console.print(json_obj)


if __name__ == "__main__":
    """测试输出功能"""
    # 测试数据
    test_data = {
        "name": "测试数据",
        "type": "json",
        "nested": {"key1": "value1", "key2": 123, "key3": True},
        "list": [1, 2, 3],
    }

    logger.info("测试 print_json 函数:")
    print_json(test_data)
