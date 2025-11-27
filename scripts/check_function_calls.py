#!/usr/bin/env python3
"""
函数调用一致性检查工具

默认对全仓函数进行参数数量比对; 可通过 --focus/--preset 只检查指定函数.
"""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

SPECIFIC_FUNCTIONS = {
    "calculate_profit_lockable_quantity",
    "match_orders",
    "sync_orders_for_pair",
    "sync_and_match_orders",
    "get_unmatched_orders",
    "calculate_profit_lock",
}

PRESET_FUNCTIONS: dict[str, set[str]] = {
    "specific": SPECIFIC_FUNCTIONS,
}

PRESET_BEHAVIOR: dict[str, dict[str, bool]] = {
    "specific": {
        "allow_default_range": True,
        "include_same_file": True,
    }
}


@dataclass
class FunctionDef:
    """函数定义信息"""

    name: str
    file_path: str
    line_number: int
    parameters: list[str]
    module_path: str
    required_params: int
    total_params: int


@dataclass
class FunctionCall:
    """函数调用信息"""

    name: str
    file_path: str
    line_number: int
    total_args: int
    module_path: str


class FunctionCallChecker:
    """函数调用检查器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.function_defs: dict[str, list[FunctionDef]] = {}
        self.function_calls: list[FunctionCall] = []

    def collect_function_definitions(self) -> None:
        """收集所有函数定义"""
        for py_file in self._iter_python_files():
            tree = self._parse_ast(py_file)
            if tree is None:
                continue
            module_path = str(py_file.relative_to(self.project_root))
            self._record_function_definitions(tree, py_file, module_path)

    def collect_function_calls(self) -> None:
        """收集所有函数调用"""
        for py_file in self._iter_python_files():
            tree = self._parse_ast(py_file)
            if tree is None:
                continue
            module_path = str(py_file.relative_to(self.project_root))
            self._record_function_calls(tree, py_file, module_path)

    def check_mismatches(
        self,
        *,
        focus: set[str] | None,
        allow_default_ranges: bool,
        include_same_file: bool,
    ) -> list[tuple[FunctionCall, list[FunctionDef]]]:
        """检查参数不匹配的调用"""
        mismatches: list[tuple[FunctionCall, list[FunctionDef]]] = []

        for call in self.function_calls:
            if focus and call.name not in focus:
                continue

            definitions = self.function_defs.get(call.name)
            if not definitions:
                continue

            comparable_defs = self._filter_definitions(
                definitions, call.file_path, include_same_file
            )
            if not comparable_defs:
                continue

            if self._call_matches_definitions(
                call, comparable_defs, allow_default_ranges
            ):
                continue

            mismatches.append((call, comparable_defs))

        return mismatches

    def report_mismatches(
        self,
        mismatches: list[tuple[FunctionCall, list[FunctionDef]]],
        *,
        focus: set[str] | None,
        allow_default_ranges: bool,
    ) -> None:
        """报告不匹配的情况"""
        if not mismatches:
            if focus:
                logger.info("✅ 所有目标函数调用参数匹配正确!")
            else:
                logger.info("✅ 未发现函数调用参数不匹配问题")
            return

        logger.info(f"🚨 发现 {len(mismatches)} 个可能的函数调用参数不匹配:")
        logger.info("=" * 80)

        for call, func_defs in mismatches:
            logger.info(f"📍 函数: {call.name}")
            logger.info(f"   调用位置: {call.module_path}:{call.line_number}")
            logger.info(f"   实际参数: {call.total_args} 个")
            logger.info("   可能的定义:")
            for func_def in func_defs:
                expected_desc = (
                    f"{func_def.required_params}-{func_def.total_params}"
                    if allow_default_ranges
                    else f"{func_def.total_params}"
                )
                logger.info(f"     - {func_def.module_path}:{func_def.line_number}")
                logger.info(
                    f"       期望参数: {expected_desc} 个 {func_def.parameters}"
                )
            logger.info("-" * 80)

    def run_check(
        self,
        *,
        focus: set[str] | None,
        allow_default_ranges: bool,
        include_same_file: bool,
    ) -> bool:
        """运行完整检查"""
        logger.info("🔍 开始检查函数调用一致性...")
        logger.info(f"📁 项目根目录: {self.project_root}")

        if focus:
            logger.info(f"🎯 限定函数: {', '.join(sorted(focus))}")
            logger.info("")

        logger.info("📋 收集函数定义...")
        self.collect_function_definitions()
        logger.info(
            f"   发现 {sum(len(defs) for defs in self.function_defs.values())} 个函数定义"
        )

        logger.info("📋 收集函数调用...")
        self.collect_function_calls()
        logger.info(f"   发现 {len(self.function_calls)} 个函数调用")

        logger.info("🔎 检查参数匹配...")
        mismatches = self.check_mismatches(
            focus=focus,
            allow_default_ranges=allow_default_ranges,
            include_same_file=include_same_file,
        )

        self.report_mismatches(
            mismatches,
            focus=focus,
            allow_default_ranges=allow_default_ranges,
        )

        return len(mismatches) == 0

    # --- Helper methods -------------------------------------------------

    def _iter_python_files(self) -> Iterable[Path]:
        """遍历需要分析的 Python 文件"""
        skip_segments = {"archived", "__pycache__"}
        for py_file in self.project_root.rglob("*.py"):
            if skip_segments.intersection(set(py_file.parts)):
                continue
            yield py_file

    def _parse_ast(self, file_path: Path) -> ast.AST | None:
        """解析文件为 AST, 失败时记录日志"""
        try:
            with file_path.open(encoding="utf-8") as f:
                return ast.parse(f.read(), filename=str(file_path))
        except Exception as exc:  # pylint: disable=broad-except
            logger.info(f"警告: 解析文件 {file_path} 失败: {exc}")
            return None

    def _record_function_definitions(
        self, tree: ast.AST, file_path: Path, module_path: str
    ) -> None:
        """从 AST 中记录函数定义"""
        for node in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
            params = [
                arg.arg for arg in node.args.args if arg.arg not in {"self", "cls"}
            ]
            total_params = len(params)
            default_count = len(node.args.defaults)
            required_params = max(total_params - default_count, 0)
            func_def = FunctionDef(
                name=node.name,
                file_path=str(file_path),
                line_number=node.lineno,
                parameters=params,
                module_path=module_path,
                required_params=required_params,
                total_params=total_params,
            )
            self.function_defs.setdefault(node.name, []).append(func_def)

    def _record_function_calls(
        self, tree: ast.AST, file_path: Path, module_path: str
    ) -> None:
        """从 AST 中记录函数调用"""
        for node in (n for n in ast.walk(tree) if isinstance(n, ast.Call)):
            if isinstance(node.func, ast.Name):
                total_args = len(node.args) + len(node.keywords)
                func_call = FunctionCall(
                    name=node.func.id,
                    file_path=str(file_path),
                    line_number=node.lineno,
                    total_args=total_args,
                    module_path=module_path,
                )
                self.function_calls.append(func_call)

    @staticmethod
    def _filter_definitions(
        definitions: list[FunctionDef],
        call_file_path: str,
        include_same_file: bool,
    ) -> list[FunctionDef]:
        if include_same_file:
            return definitions
        return [d for d in definitions if d.file_path != call_file_path]

    @staticmethod
    def _call_matches_definitions(
        call: FunctionCall,
        definitions: list[FunctionDef],
        allow_default_ranges: bool,
    ) -> bool:
        for func_def in definitions:
            if allow_default_ranges:
                if func_def.required_params <= call.total_args <= func_def.total_params:
                    return True
            else:
                if call.total_args == func_def.total_params:
                    return True
        return False


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查函数调用与定义的参数数量是否匹配")
    parser.add_argument(
        "--focus",
        help="逗号分隔的函数名列表, 仅检查这些函数",
    )
    parser.add_argument(
        "--preset",
        choices=sorted(PRESET_FUNCTIONS.keys()),
        help="使用预设函数集合, 例如 --preset specific",
    )
    parser.add_argument(
        "--include-same-file",
        action="store_true",
        help="在比对时包含定义与调用位于同一文件的情况",
    )
    parser.add_argument(
        "--allow-default-range",
        action="store_true",
        help="允许参数数量在 [必需参数, 总参数] 范围内视为合法",
    )
    return parser.parse_args(argv)


def resolve_focus(args: argparse.Namespace) -> tuple[set[str] | None, dict[str, bool]]:
    focus: set[str] = set()
    if args.preset:
        focus.update(PRESET_FUNCTIONS.get(args.preset, set()))

    if args.focus:
        focus.update(name.strip() for name in args.focus.split(",") if name.strip())

    if not focus:
        return None, {}

    return focus, PRESET_BEHAVIOR.get(args.preset, {})


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    focus, preset_behavior = resolve_focus(args)
    allow_default_ranges = args.allow_default_range or preset_behavior.get(
        "allow_default_range", False
    )
    include_same_file = args.include_same_file or preset_behavior.get(
        "include_same_file", False
    )

    project_root = Path(__file__).parent.parent
    checker = FunctionCallChecker(project_root)
    success = checker.run_check(
        focus=focus,
        allow_default_ranges=allow_default_ranges,
        include_same_file=include_same_file,
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
