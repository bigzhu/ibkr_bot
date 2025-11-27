#!/usr/bin/env python3
"""
修复项目中的中文标点符号
将中文标点符号替换为英文标点符号
使用Unicode转义码避免脚本运行时替换自身代码
"""

import sys
from pathlib import Path

from loguru import logger

# 中文标点符号映射表 - 使用Unicode转义码避免自我替换
PUNCTUATION_MAP = {
    # 基本标点符号
    "\uff0c": ",",  # 中文逗号 → 英文逗号
    "\u3002": ".",  # 中文句号 → 英文句号
    "\uff1b": ";",  # 中文分号 → 英文分号
    "\uff1a": ":",  # 中文冒号 → 英文冒号
    "\uff01": "!",  # 中文感叹号 → 英文感叹号
    "\uff1f": "?",  # 中文问号 → 英文问号
    # 引号
    "\u201c": '"',  # 中文左双引号 → 英文双引号
    "\u201d": '"',  # 中文右双引号 → 英文双引号
    "\u2018": "'",  # 中文左单引号 → 英文单引号
    "\u2019": "'",  # 中文右单引号 → 英文单引号
    "\uff02": '"',  # 全角双引号 → 英文双引号
    "\uff07": "'",  # 全角单引号 → 英文单引号
    # 括号
    "\uff08": "(",  # 中文左括号 → 英文左括号
    "\uff09": ")",  # 中文右括号 → 英文右括号
    "\u3010": "[",  # 中文左方括号 → 英文左方括号
    "\u3011": "]",  # 中文右方括号 → 英文右方括号
    "\uff3b": "[",  # 全角左方括号 → 英文左方括号
    "\uff3d": "]",  # 全角右方括号 → 英文右方括号
    "\uff5b": "{",  # 全角左大括号 → 英文左大括号
    "\uff5d": "}",  # 全角右大括号 → 英文右大括号
    "\u3008": "<",  # 中文左书名号 → 英文小于号
    "\u3009": ">",  # 中文右书名号 → 英文大于号
    # 其他符号
    "\u3001": ",",  # 中文顿号 → 英文逗号
    "\uff5e": "~",  # 全角波浪号 → 英文波浪号
    "\uff0d": "-",  # 全角减号 → 英文减号
    "\uff0b": "+",  # 全角加号 → 英文加号
    "\uff1d": "=",  # 全角等号 → 英文等号
    "\uff0a": "*",  # 全角星号 → 英文星号
    "\uff0f": "/",  # 全角斜杠 → 英文斜杠
    "\uff5c": "|",  # 全角竖线 → 英文竖线
    "\uff06": "&",  # 全角和号 → 英文和号
    "\uff05": "%",  # 全角百分号 → 英文百分号
    "\uff04": "$",  # 全角美元符 → 英文美元符
    "\uff03": "#",  # 全角井号 → 英文井号
    "\uff20": "@",  # 全角at符 → 英文at符
    "\u2026": "...",  # 中文省略号 → 英文省略号
    "\u2014": "--",  # 中文破折号 → 英文双减号
    # 额外的全角字符
    "\uff1c": "<",  # 全角小于号 → 英文小于号
    "\uff1e": ">",  # 全角大于号 → 英文大于号
    "\uff3e": "^",  # 全角插入符 → 英文插入符
    "\uff40": "`",  # 全角反引号 → 英文反引号
    "\uff3f": "_",  # 全角下划线 → 英文下划线
}

# 要处理的文件扩展名
FILE_EXTENSIONS = {
    ".py",  # Python文件
    ".md",  # Markdown文件
    ".txt",  # 文本文件
    ".yml",  # YAML文件
    ".yaml",  # YAML文件
    ".json",  # JSON文件
    ".toml",  # TOML文件
    ".cfg",  # 配置文件
    ".ini",  # INI文件
    ".sh",  # Shell脚本
    ".bat",  # 批处理文件
    ".ps1",  # PowerShell脚本
    ".js",  # JavaScript文件
    ".ts",  # TypeScript文件
    ".html",  # HTML文件
    ".css",  # CSS文件
    ".vue",  # Vue文件
    ".jsx",  # JSX文件
    ".tsx",  # TSX文件
}

# 要跳过的目录
SKIP_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    ".next",
    "dist",
    "build",
    ".venv",
    "venv",
    ".env",
}


def fix_chinese_punctuation_in_text(text: str) -> tuple[str, int]:
    """
    修复文本中的中文标点符号

    Args:
        text: 原始文本

    Returns:
        修复后的文本和替换次数
    """
    fixed_text = text
    total_replacements = 0

    for chinese_punct, english_punct in PUNCTUATION_MAP.items():
        if chinese_punct in fixed_text:
            count = fixed_text.count(chinese_punct)
            fixed_text = fixed_text.replace(chinese_punct, english_punct)
            total_replacements += count

    return fixed_text, total_replacements


def fix_chinese_punctuation_in_file(file_path: Path, auto_fix: bool = False) -> bool:
    """
    修复单个文件中的中文标点符号

    Args:
        file_path: 文件路径
        auto_fix: 是否自动修复

    Returns:
        是否进行了修复
    """
    try:
        original_content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.info(f"   ❌ 读取失败: {exc}")
        return False

    fixed_content, replacements = fix_chinese_punctuation_in_text(original_content)
    if replacements == 0:
        return False

    _log_discovery(file_path, replacements)
    if not _should_apply_fix(auto_fix):
        return False

    try:
        _ = file_path.write_text(fixed_content, encoding="utf-8")
    except OSError as exc:
        logger.info(f"   ❌ 写入失败: {exc}")
        return False

    logger.info(f"   ✅ 已修复 {replacements} 个标点符号")
    return True


def find_files_to_process(project_root: Path) -> list[Path]:
    """
    查找需要处理的文件

    Args:
        project_root: 项目根目录

    Returns:
        需要处理的文件列表
    """
    files_to_process: list[Path] = []

    for file_path in project_root.rglob("*"):
        # 跳过目录
        if file_path.is_dir():
            continue

        # 跳过指定目录中的文件
        if any(skip_dir in file_path.parts for skip_dir in SKIP_DIRECTORIES):
            continue

        # 检查文件扩展名
        if file_path.suffix not in FILE_EXTENSIONS:
            continue

        files_to_process.append(file_path)

    return files_to_process


def main() -> None:
    """主函数"""
    targets, auto_fix = _parse_arguments(sys.argv[1:])
    project_root = Path(__file__).parent.parent

    _log_run_settings(project_root, targets, auto_fix)
    files_to_process = _resolve_target_files(targets, project_root)
    logger.info(f"📋 待检查文件数: {len(files_to_process)}\n")

    fixed_files = sum(
        1
        for file_path in files_to_process
        if fix_chinese_punctuation_in_file(file_path, auto_fix)
    )
    _log_summary(fixed_files)


def _parse_arguments(argv: list[str]) -> tuple[list[str], bool]:
    targets: list[str] = []
    auto_fix = False
    for arg in argv:
        if arg == "--auto":
            auto_fix = True
        elif arg.startswith("-"):
            logger.warning(f"忽略未知参数: {arg}")
        else:
            targets.append(arg)
    return targets, auto_fix


def _resolve_target_files(targets: list[str], project_root: Path) -> list[Path]:
    if targets:
        return [Path(target).resolve() for target in targets]
    return find_files_to_process(project_root)


def _log_run_settings(project_root: Path, targets: list[str], auto_fix: bool) -> None:
    logger.info("🔧 开始修复项目中的中文标点符号...")
    if targets:
        logger.info(f"📄 按文件处理: {len(targets)} 个")
    else:
        logger.info(f"📁 项目根目录: {project_root}")
    logger.info("🤖 自动修复模式" if auto_fix else "👤 手动确认模式")
    logger.info("")


def _log_summary(fixed_files: int) -> None:
    logger.info("")
    if fixed_files > 0:
        logger.info(f"✨ 完成! 修复了 {fixed_files} 个文件中的中文标点符号")
    else:
        logger.info("✨ 所有文件已经使用正确的英文标点符号!")


def _log_discovery(file_path: Path, replacements: int) -> None:
    logger.info(f"📄 {file_path.relative_to(Path.cwd())}")
    logger.info(f"   发现 {replacements} 个中文标点符号")


def _should_apply_fix(auto_fix: bool) -> bool:
    if auto_fix:
        return True
    response = input("   是否修复? (y/N): ").strip().lower()
    if response in {"y", "yes"}:
        return True
    logger.info("   跳过")
    return False


if __name__ == "__main__":
    main()
