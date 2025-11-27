"""
shared.path_utils 测试
"""

import sys

from shared.path_utils import add_project_root_to_path, get_project_root


def test_get_project_root_is_parent():
    root = get_project_root()
    assert root.exists()
    # 根目录应包含 pyproject.toml
    assert (root / "pyproject.toml").exists()


def test_add_project_root_to_path_idempotent(monkeypatch):
    root = get_project_root()
    # 确保起始不包含,便于测试
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != str(root)])
    before = list(sys.path)
    add_project_root_to_path()
    after = list(sys.path)
    assert len(after) == len(before) + 1
    assert after[0] == str(root)
    # 再次添加不会重复
    add_project_root_to_path()
    assert sys.path.count(str(root)) == 1
