"""
DatabaseManager 最小 CRUD 测试(使用临时 SQLite 文件)
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from database.connection import DatabaseConfig, DatabaseManager


def test_db_manager_crud():
    with TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "t.db"
        mgr = DatabaseManager(DatabaseConfig(db_path=db_path))

        # 建表
        with mgr.transaction() as conn:
            _ = conn.execute(
                "CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
            )

        # 插入
        n = mgr.execute_update("INSERT INTO t (name) VALUES (?)", ("alice",))
        assert n == 1

        # 查询
        rows = mgr.execute_query("SELECT id, name FROM t WHERE name = ?", ("alice",))
        assert len(rows) == 1
        r = rows[0]
        assert r["name"] == "alice"
