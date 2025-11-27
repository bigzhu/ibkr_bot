"""
项目路径管理工具

统一管理项目路径相关功能,消除重复代码
"""

import sys
from pathlib import Path

from loguru import logger


def add_project_root_to_path() -> None:
    """添加项目根目录到Python路径

    自动检测项目根目录并添加到sys.path,避免重复路径
    支持双重用途模块(既可import使用,也可独立运行)
    """
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def get_project_root() -> Path:
    """获取项目根目录路径

    Returns:
        Path: 项目根目录的Path对象
    """
    return Path(__file__).parent.parent


def ensure_project_root_for_script(current_file: str) -> None:
    """在脚本直跑场景下,将项目根目录加入 sys.path

    仅用于 `if __name__ == "__main__":` 场景,避免库导入时污染路径.

    查找规则:
    - 自当前文件向上查找,遇到包含 `pyproject.toml` 的目录即视为项目根
    - 若未找到,回退到 `Path(current_file).resolve().parents[1]`
    """
    cur = Path(current_file).resolve()
    root: Path | None = None

    for parent in [cur, *list(cur.parents)]:
        if (parent / "pyproject.toml").exists():
            root = parent
            break

    if root is None and len(cur.parents) >= 2:
        root = cur.parents[1]
    elif root is None:
        root = cur.parent

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


if __name__ == "__main__":
    """测试路径管理功能"""
    logger.info("🛠️ 项目路径管理工具测试")

    logger.info("1. 测试项目根目录获取")
    root = get_project_root()
    logger.info(f"   项目根目录: {root}")
    logger.info(f"   绝对路径: {root.absolute()}")

    logger.info("2. 测试添加到Python路径")
    original_path_len = len(sys.path)
    add_project_root_to_path()
    new_path_len = len(sys.path)

    if new_path_len > original_path_len:
        logger.info("   ✅ 成功添加到sys.path")
    else:
        logger.info("   ✅ 路径已存在,无需重复添加")

    logger.info(f"   当前sys.path长度: {len(sys.path)}")
    logger.info("   项目根目录在path中:", str(root) in sys.path)
