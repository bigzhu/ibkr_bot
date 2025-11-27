#!/usr/bin/env python3
"""
数据库迁移管理工具
统一管理所有数据库表结构变更,支持版本化迁移

使用方法:
- 开发环境: p scripts/migrate_database.py
- 指定版本: p scripts/migrate_database.py --target-version 3
- 查看状态: p scripts/migrate_database.py --status
- 强制重建: p scripts/migrate_database.py --rebuild
"""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import contextlib

from loguru import logger

from database.db_config import get_db_manager


class DatabaseMigrator:
    """数据库迁移管理器"""

    def __init__(self, db_manager: Any) -> None:
        self.db_manager = db_manager
        self.migrations: list[tuple[int, str, Callable[..., Any]]] = []
        self.init_migrations()

    def init_migrations(self) -> None:
        """注册所有迁移函数"""
        for version, description, func in self._initial_migration_definitions():
            self.register_migration(version, description, func)

    def _initial_migration_definitions(
        self,
    ) -> list[tuple[int, str, Callable[[], None]]]:
        """初始化迁移定义列表"""
        return [
            (
                1,
                "重命名 binance_order_filler 表为 filled_orders",
                self.migration_v1_rename_table,
            ),
            (
                2,
                "为 filled_orders 表添加 profit 和 commission 字段",
                self.migration_v2_add_fields,
            ),
            (
                3,
                "删除 symbol_timeframe_configs 表的 demark_base_percentage 字段",
                self.migration_v3_remove_demark_base_percentage,
            ),
            (
                4,
                "重命名 demark_max_percentage 为 daily_max_percentage 并更新默认值",
                self.migration_v4_rename_demark_max_percentage,
            ),
            (
                5,
                "为 trading_symbols 表添加 base_asset_balance 字段",
                self.migration_v5_add_base_asset_balance,
            ),
            (
                6,
                "为 trading_logs 表添加 price_change_percentage 字段",
                self.migration_v6_add_price_change_percentage,
            ),
            (
                7,
                "为 trading_symbols 表添加 quote_asset_balance 字段并移除 balance_updated_at",
                self.migration_v7_add_quote_asset_balance,
            ),
            (8, "删除无用的 trading_state 表", self.migration_v8_drop_trading_state),
            (
                9,
                "为 trading_symbols 表添加运行模式字段",
                self.migration_v9_add_trading_mode,
            ),
            (
                10,
                "为 filled_orders 表添加 client_order_id 字段",
                self.migration_v10_add_client_order_id,
            ),
            (
                11,
                "创建 order_matches 撮合详情表",
                self.migration_v11_create_order_matches_table,
            ),
            (
                12,
                "为 trading_symbols 表添加最大套住百分比字段",
                self.migration_v12_add_max_trapped_percentage,
            ),
            (
                13,
                "将 daily_max_percentage 字段类型从 INTEGER 改为 REAL 以支持小数",
                self.migration_v13_change_daily_max_percentage_type,
            ),
            (
                14,
                "删除 order_matches 表的 commission 字段",
                self.migration_v14_remove_commission_field,
            ),
            (
                15,
                "为 order_matches 表添加 sell_order_no 和 buy_order_no 的唯一索引",
                self.migration_v15_add_unique_index,
            ),
            (
                16,
                "重命名 symbol_timeframe_configs 表的 demark_min_signal_value 为 demark_buy",
                self.migration_v16_rename_demark_min_signal_value,
            ),
            (
                17,
                "为 symbol_timeframe_configs 表添加 demark_sell 字段",
                self.migration_v17_add_demark_sell,
            ),
            (
                18,
                "为 symbol_timeframe_configs 表添加 max_buy_amount_period 字段",
                self.migration_v18_add_max_buy_amount_period,
            ),
            (
                19,
                "创建 backtest_klines 表用于存储回测K线数据",
                self.migration_v19_create_backtest_klines_table,
            ),
            (
                20,
                "为 symbol_timeframe_configs 表添加 buy_interval_minutes 字段",
                self.migration_v20_add_buy_interval_minutes,
            ),
            (
                21,
                "为 symbol_timeframe_configs 表添加 minimum_price_change_percentage 字段",
                self.migration_v21_add_minimum_price_change_percentage,
            ),
            (
                22,
                "为 filled_orders 表添加 matched_time 字段并补齐历史数据",
                self.migration_v22_add_matched_time,
            ),
            (
                23,
                "为 filled_orders 和 trading_logs 添加高频查询索引",
                self.migration_v23_add_permanent_indexes,
            ),
            (
                24,
                "将 filled_orders.unmatched_qty 改为 REAL 类型",
                self.migration_v24_convert_unmatched_qty_to_real,
            ),
            (
                25,
                "为 trading_logs 表创建 run_time 索引",
                self.migration_v25_add_trading_logs_run_time_index,
            ),
            (
                26,
                "将 filled_orders.average_price 改为 REAL 类型",
                self.migration_v26_convert_average_price_to_real,
            ),
            (
                27,
                "为 trading_logs 表添加 open/high/low/close 字段",
                self.migration_v27_add_trading_logs_ohlc,
            ),
            (
                28,
                "为回测热点查询补充复合索引",
                self.migration_v28_add_backtest_perf_indexes,
            ),
            (
                29,
                "创建历史订单表 filled_his_orders 及索引",
                self.migration_v29_create_filled_his_orders,
            ),
            (
                30,
                "补充 filled_his_orders 基础索引",
                self.migration_v30_add_indexes_filled_his_orders,
            ),
            (
                31,
                "删除 symbol_timeframe_configs 表的 entry_coefficient_multiplier 字段",
                self.migration_v31_remove_entry_coefficient_multiplier,
            ),
            (
                32,
                "删除 symbol_timeframe_configs 表的 buy_interval_minutes, demark_percentage_coefficient, max_buy_amount_period 字段",
                self.migration_v32_remove_unused_configs,
            ),
            (
                33,
                "删除 trading_symbols 表的 max_trapped_percentage 字段",
                self.migration_v33_remove_max_trapped_percentage,
            ),
            (
                34,
                "删除 trading_symbols 表的 trading_mode 字段",
                self.migration_v34_remove_trading_mode,
            ),
            (
                35,
                "删除 symbol_timeframe_configs 表的 minimum_price_change_percentage 字段",
                self.migration_v35_remove_minimum_price_change_percentage,
            ),
        ]

    def register_migration(
        self, version: int, description: str, func: Callable[[], None]
    ) -> None:
        """注册迁移函数"""
        self.migrations.append((version, description, func))

    def get_current_version(self) -> int:
        """获取当前数据库版本"""
        try:
            # 检查版本表是否存在
            if not self.table_exists("db_version"):
                self.create_version_table()
                return 0

            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT version FROM db_version ORDER BY id DESC LIMIT 1"
                )
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"获取数据库版本失败: {e}")
            return 0

    def set_version(self, version: int) -> None:
        """设置数据库版本"""
        try:
            with self.db_manager.transaction() as conn:
                conn.execute(
                    "INSERT INTO db_version (version, migrated_at) VALUES (?, datetime('now'))",
                    (version,),
                )
            logger.info(f"✅ 数据库版本已更新为 {version}")
        except Exception as e:
            logger.error(f"设置数据库版本失败: {e}")
            raise

    def create_version_table(self) -> None:
        """创建版本管理表"""
        try:
            with self.db_manager.transaction() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS db_version (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version INTEGER NOT NULL,
                        migrated_at DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
            logger.info("✅ 版本管理表已创建")
        except Exception as e:
            logger.error(f"创建版本管理表失败: {e}")
            raise

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,),
                )
                return cursor.fetchone() is not None
        except Exception:
            return False

    def column_exists(self, table_name: str, column_name: str) -> bool:
        """检查字段是否存在"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                return column_name in column_names
        except Exception:
            return False

    def migrate_to_version(self, target_version: int) -> None:
        """迁移到指定版本"""
        current_version = self.get_current_version()
        logger.info(f"当前数据库版本: {current_version}")
        logger.info(f"目标版本: {target_version}")

        if current_version == target_version:
            logger.info("✅ 数据库已是最新版本")
            return

        if target_version < current_version:
            logger.warning("⚠️ 不支持数据库降级")
            return

        # 执行迁移
        for version, description, migration_func in self.migrations:
            if version <= current_version:
                continue
            if version > target_version:
                break

            logger.info(f"📝 执行迁移 v{version}: {description}")
            try:
                migration_func()
                self.set_version(version)
                logger.info(f"✅ 迁移 v{version} 完成")
            except Exception as e:
                logger.error(f"❌ 迁移 v{version} 失败: {e}")
                raise

    def get_latest_version(self) -> int:
        """获取最新可用版本"""
        return (
            max(version for version, _, _ in self.migrations) if self.migrations else 0
        )

    def show_status(self) -> None:
        """显示迁移状态"""
        current_version = self.get_current_version()
        latest_version = self.get_latest_version()

        logger.info("🗄️ 数据库迁移状态")
        logger.info("=" * 50)
        logger.info(f"当前版本: {current_version}")
        logger.info(f"最新版本: {latest_version}")
        logger.info(f"数据库路径: {self.db_manager.config.db_path}")

        logger.info("\n可用迁移:")
        for version, description, _ in self.migrations:
            status = "✅ 已应用" if version <= current_version else "⏳ 待应用"
            logger.info(f"  v{version}: {description} ({status})")

    def rebuild_database(self) -> None:
        """重建数据库(危险操作)"""
        logger.warning("⚠️ 即将重建数据库,所有数据将丢失!")

        try:
            # 删除所有相关表
            tables_to_drop = ["filled_orders", "binance_order_filler", "db_version"]

            with self.db_manager.transaction() as conn:
                for table in tables_to_drop:
                    if self.table_exists(table):
                        conn.execute(f"DROP TABLE {table}")
                        logger.info(f"删除表: {table}")

            # 重新创建并迁移到最新版本
            latest_version = self.get_latest_version()
            self.migrate_to_version(latest_version)

            logger.info("✅ 数据库重建完成")

        except Exception as e:
            logger.error(f"❌ 数据库重建失败: {e}")
            raise

    # ================================
    # 迁移函数定义区域
    # ================================

    def migration_v1_rename_table(self) -> None:
        """迁移 v1: 重命名 binance_order_filler 表为 order_filler"""
        self._ensure_can_rename_table(
            source_table="binance_order_filler", target_table="filled_orders"
        )
        with self.db_manager.transaction() as conn:
            conn.execute("ALTER TABLE binance_order_filler RENAME TO filled_orders")
            logger.info("表已重命名: binance_order_filler -> filled_orders")
            self._refresh_indexes_after_rename(conn)

    def _ensure_can_rename_table(self, source_table: str, target_table: str) -> None:
        """确认表重命名的前置条件"""
        if not self.table_exists(source_table):
            if self.table_exists(target_table):
                logger.info(f"表 {target_table} 已存在,跳过重命名")
                return
            logger.error(f"表 {source_table} 不存在,无法重命名")
            raise ValueError("源表不存在")

        if self.table_exists(target_table):
            logger.error(f"表 {target_table} 已存在,无法重命名")
            raise ValueError("目标表已存在")

    def _refresh_indexes_after_rename(self, conn: Any) -> None:
        """删除旧索引并创建新索引"""
        for index_name in self._old_filled_order_indexes():
            with contextlib.suppress(Exception):
                conn.execute(f"DROP INDEX IF EXISTS {index_name}")

        for index_sql in self._new_filled_order_indexes():
            conn.execute(index_sql)

        logger.info("索引已更新")

    @staticmethod
    def _old_filled_order_indexes() -> list[str]:
        """旧的 filled orders 相关索引名"""
        return [
            "idx_binance_order_filler_pair",
            "idx_binance_order_filler_status",
            "idx_binance_order_filler_time",
            "idx_binance_order_filler_order_no",
            "idx_binance_order_filler_side",
        ]

    @staticmethod
    def _new_filled_order_indexes() -> list[str]:
        """新的 filled orders 相关索引 SQL"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_filled_orders_pair ON filled_orders(pair);",
            "CREATE INDEX IF NOT EXISTS idx_filled_orders_status ON filled_orders(status);",
            "CREATE INDEX IF NOT EXISTS idx_filled_orders_time ON filled_orders(time);",
            "CREATE INDEX IF NOT EXISTS idx_filled_orders_order_no ON filled_orders(order_no);",
            "CREATE INDEX IF NOT EXISTS idx_filled_orders_side ON filled_orders(side);",
        ]

    def migration_v2_add_fields(self) -> None:
        """迁移 v2: 为 filled_orders 表添加 profit 和 commission 字段"""
        if not self.table_exists("filled_orders"):
            logger.error("表 filled_orders 不存在")
            raise ValueError("表不存在")

        # 添加字段
        fields_to_add = [
            ("profit", "TEXT DEFAULT '0'"),
            ("commission", "TEXT DEFAULT '0'"),
        ]

        with self.db_manager.transaction() as conn:
            for field_name, field_definition in fields_to_add:
                if self.column_exists("filled_orders", field_name):
                    logger.info(f"字段 {field_name} 已存在,跳过添加")
                    continue

                sql = f"ALTER TABLE filled_orders ADD COLUMN {field_name} {field_definition}"
                conn.execute(sql)
                logger.info(f"字段已添加: {field_name}")

    def migration_v3_remove_demark_base_percentage(self) -> None:
        """迁移 v3: 删除 symbol_timeframe_configs 表的 demark_base_percentage 字段"""
        if not self.table_exists("symbol_timeframe_configs"):
            logger.error("表 symbol_timeframe_configs 不存在")
            raise ValueError("表不存在")

        # 检查字段是否存在
        if not self.column_exists("symbol_timeframe_configs", "demark_base_percentage"):
            logger.info("字段 demark_base_percentage 不存在,跳过删除")
            return

        # SQLite 不支持直接删除字段,需要重建表
        with self.db_manager.transaction() as conn:
            conn.execute(
                "ALTER TABLE symbol_timeframe_configs DROP COLUMN demark_base_percentage"
            )
            logger.info("字段 demark_base_percentage 已删除")

    def migration_v4_rename_demark_max_percentage(self) -> None:
        """迁移 v4: 重命名 demark_max_percentage 为 daily_max_percentage 并更新默认值"""
        if not self.table_exists("symbol_timeframe_configs"):
            logger.error("表 symbol_timeframe_configs 不存在")
            raise ValueError("表不存在")

        # 检查旧字段是否存在
        if not self.column_exists("symbol_timeframe_configs", "demark_max_percentage"):
            logger.info("字段 demark_max_percentage 不存在,跳过重命名")
            return

        # 检查新字段是否已存在
        if self.column_exists("symbol_timeframe_configs", "daily_max_percentage"):
            logger.info("字段 daily_max_percentage 已存在,跳过重命名")
            return

        with self.db_manager.transaction() as conn:
            # SQLite 不支持直接重命名字段,使用 ALTER TABLE 添加新字段然后复制数据
            conn.execute(
                "ALTER TABLE symbol_timeframe_configs ADD COLUMN daily_max_percentage INTEGER DEFAULT 24"
            )
            conn.execute(
                "UPDATE symbol_timeframe_configs SET daily_max_percentage = demark_max_percentage"
            )
            conn.execute(
                "ALTER TABLE symbol_timeframe_configs DROP COLUMN demark_max_percentage"
            )
            logger.info("字段已重命名: demark_max_percentage -> daily_max_percentage")

    def migration_v5_add_base_asset_balance(self) -> None:
        """迁移 v5: 为 trading_symbols 表添加 base_asset_balance 字段"""
        if not self.table_exists("trading_symbols"):
            logger.error("表 trading_symbols 不存在")
            raise ValueError("表 trading_symbols 不存在")

        # 检查字段是否已存在
        if self.column_exists("trading_symbols", "base_asset_balance"):
            logger.info("字段 base_asset_balance 已存在,跳过添加")
            return

        with self.db_manager.transaction() as conn:
            # 添加基础资产余额字段,默认值为0.0
            conn.execute(
                """
                ALTER TABLE trading_symbols
                ADD COLUMN base_asset_balance REAL DEFAULT 0.0
            """
            )
            logger.info("✅ 已为 trading_symbols 表添加 base_asset_balance 字段")

    def migration_v6_add_price_change_percentage(self) -> None:
        """迁移 v6: 为 trading_logs 表添加 price_change_percentage 字段"""
        if not self.table_exists("trading_logs"):
            logger.error("表 trading_logs 不存在")
            raise ValueError("表 trading_logs 不存在")

        # 检查字段是否已存在
        if self.column_exists("trading_logs", "price_change_percentage"):
            logger.info("字段 price_change_percentage 已存在, 跳过添加")
            return

        with self.db_manager.transaction() as conn:
            # 添加价格变化百分比字段
            conn.execute(
                """
                ALTER TABLE trading_logs
                ADD COLUMN price_change_percentage REAL DEFAULT NULL
            """
            )
            logger.info("✅ 已为 trading_logs 表添加 price_change_percentage 字段")

    def migration_v7_add_quote_asset_balance(self) -> None:
        """迁移 v7: 为 trading_symbols 表添加 quote_asset_balance 字段并移除 balance_updated_at"""
        if not self.table_exists("trading_symbols"):
            logger.error("表 trading_symbols 不存在")
            raise ValueError("表 trading_symbols 不存在")

        with self.db_manager.transaction() as conn:
            # 添加计价资产余额字段
            if not self.column_exists("trading_symbols", "quote_asset_balance"):
                conn.execute(
                    """
                    ALTER TABLE trading_symbols
                    ADD COLUMN quote_asset_balance REAL DEFAULT 0.0
                """
                )
                logger.info("✅ 已为 trading_symbols 表添加 quote_asset_balance 字段")
            else:
                logger.info("字段 quote_asset_balance 已存在,跳过添加")

            # 移除不必要的 balance_updated_at 字段 (如果存在)
            if self.column_exists("trading_symbols", "balance_updated_at"):
                conn.execute(
                    "ALTER TABLE trading_symbols DROP COLUMN balance_updated_at"
                )
                logger.info("✅ 已移除 trading_symbols 表的 balance_updated_at 字段")
            else:
                logger.info("字段 balance_updated_at 不存在,跳过移除")

    def migration_v8_drop_trading_state(self) -> None:
        """迁移 v8: 删除无用的 trading_state 表"""
        if not self.table_exists("trading_state"):
            logger.info("表 trading_state 不存在,跳过删除")
            return

        with self.db_manager.transaction() as conn:
            # 删除 trading_state 表
            conn.execute("DROP TABLE trading_state")
            logger.info("✅ 已删除无用的 trading_state 表")

    def migration_v9_add_trading_mode(self) -> None:
        """迁移 v9: 为 trading_symbols 表添加运行模式字段"""
        if not self.table_exists("trading_symbols"):
            logger.error("表 trading_symbols 不存在")
            raise ValueError("表 trading_symbols 不存在")

        # 检查字段是否已存在
        if self.column_exists("trading_symbols", "trading_mode"):
            logger.info("字段 trading_mode 已存在,跳过添加")
            return

        with self.db_manager.transaction() as conn:
            # 添加运行模式字段
            # 默认为arbitrage(套利模式),因为现有交易策略更适合快速回收资金
            conn.execute(
                """
                ALTER TABLE trading_symbols
                ADD COLUMN trading_mode TEXT DEFAULT 'arbitrage'
            """
            )
            logger.info("✅ 已为 trading_symbols 表添加 trading_mode 字段")
            logger.info("📝 字段说明:")
            logger.info("  - arbitrage: SELL时以10倍百分比例卖出,力求尽快回收资金")
            logger.info("  - hodl: SELL时以正常比例卖出,与计价货币逐渐趋近持平")

    def migration_v10_add_client_order_id(self) -> None:
        """迁移 v10: 为 filled_orders 表添加 client_order_id 字段"""
        if not self.table_exists("filled_orders"):
            logger.error("表 filled_orders 不存在")
            raise ValueError("表 filled_orders 不存在")

        # 检查字段是否已存在
        if self.column_exists("filled_orders", "client_order_id"):
            logger.info("字段 client_order_id 已存在,跳过添加")
            return

        with self.db_manager.transaction() as conn:
            # 添加客户端订单ID字段,允许为空
            conn.execute(
                """
                ALTER TABLE filled_orders
                ADD COLUMN client_order_id TEXT
            """
            )
            logger.info("✅ 已为 filled_orders 表添加 client_order_id 字段")
            logger.info(
                "📝 字段说明: 客户端订单ID,由API调用者设置,如 'myOrder1', 'abc123'"
            )

    def migration_v11_create_order_matches_table(self) -> None:
        """迁移 v11: 创建 order_matches 撮合详情表"""

        # 检查表是否已存在
        if self.table_exists("order_matches"):
            logger.info("表 order_matches 已存在,跳过创建")
            return

        with self.db_manager.transaction() as conn:
            self._create_order_matches_table(conn)
            self._create_order_matches_indexes(conn)

        logger.info("✅ 已创建 order_matches 撮合详情表")
        logger.info(
            "📝 表说明: 记录每笔SELL单与BUY单的撮合详情,包含价格,数量,利润等信息"
        )

    @staticmethod
    def _create_order_matches_indexes(conn: Any) -> None:
        """为 order_matches 表创建索引"""
        indices = [
            ("idx_order_matches_sell_order", "sell_order_no"),
            ("idx_order_matches_buy_order", "buy_order_no"),
            ("idx_order_matches_pair", "pair"),
            ("idx_order_matches_timeframe", "timeframe"),
            ("idx_order_matches_matched_at", "matched_at"),
        ]

        for index_name, column_name in indices:
            conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON order_matches({column_name})
            """
            )
            logger.info(f"✅ 已创建索引: {index_name}")

    @staticmethod
    def _create_order_matches_table(conn: Any) -> None:
        """创建 order_matches 表"""
        conn.execute(
            """
            CREATE TABLE order_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sell_order_no TEXT NOT NULL,
                buy_order_no TEXT NOT NULL,
                sell_price TEXT NOT NULL,
                buy_price TEXT NOT NULL,
                matched_qty TEXT NOT NULL,
                profit TEXT NOT NULL,
                commission TEXT NOT NULL,
                pair TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

    def migration_v12_add_max_trapped_percentage(self) -> None:
        """迁移 v12: 为 trading_symbols 表添加最大套住百分比字段"""
        if not self.table_exists("trading_symbols"):
            logger.error("表 trading_symbols 不存在")
            raise ValueError("表 trading_symbols 不存在")

        # 检查字段是否已存在
        if self.column_exists("trading_symbols", "max_trapped_percentage"):
            logger.info("字段 max_trapped_percentage 已存在,跳过添加")
            return

        with self.db_manager.transaction() as conn:
            # 添加最大套住百分比字段,默认值为20.0
            # 用于控制持仓风险,当当前价格相对买入均价下跌超过此百分比时停止新的买入操作
            conn.execute(
                """
                ALTER TABLE trading_symbols
                ADD COLUMN max_trapped_percentage REAL DEFAULT 20.0
            """
            )
            logger.info("✅ 已为 trading_symbols 表添加 max_trapped_percentage 字段")
            logger.info(
                "📝 字段说明: 最大套住百分比,用于风险控制,当持仓亏损超过此百分比时停止新的买入操作"
            )

    def migration_v34_remove_trading_mode(self) -> None:
        """迁移 v34: 删除 trading_symbols 表的 trading_mode 字段"""
        if not self.table_exists("trading_symbols"):
            logger.error("表 trading_symbols 不存在")
            raise ValueError("表 trading_symbols 不存在")

        # 检查字段是否存在
        if not self.column_exists("trading_symbols", "trading_mode"):
            logger.info("字段 trading_mode 不存在,跳过 v34")
            return

        with self.db_manager.transaction() as conn:
            # SQLite 不支持直接删除字段,需要重建表
            # 1. 创建新表 (不包含 trading_mode)
            conn.execute(
                """
                CREATE TABLE trading_symbols_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    base_asset TEXT NOT NULL,
                    quote_asset TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    description TEXT,
                    base_asset_precision INTEGER DEFAULT 8,
                    quote_asset_precision INTEGER DEFAULT 8,
                    current_price REAL DEFAULT 0,
                    volume_24h REAL DEFAULT 0,
                    volume_24h_quote REAL DEFAULT 0,
                    price_change_24h REAL DEFAULT 0,
                    high_24h REAL DEFAULT 0,
                    low_24h REAL DEFAULT 0,
                    min_qty REAL DEFAULT 0,
                    max_qty REAL DEFAULT 0,
                    step_size REAL DEFAULT 0,
                    min_notional REAL DEFAULT 0,
                    min_price REAL DEFAULT 0,
                    max_price REAL DEFAULT 0,
                    tick_size REAL DEFAULT 0,
                    last_updated_price DATETIME,
                    max_fund INTEGER DEFAULT NULL,
                    base_asset_balance REAL DEFAULT 0.0,
                    quote_asset_balance REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # 2. 复制数据 (排除 trading_mode)
            conn.execute(
                """
                INSERT INTO trading_symbols_new (
                    id, symbol, base_asset, quote_asset, is_active, description,
                    base_asset_precision, quote_asset_precision, current_price,
                    volume_24h, volume_24h_quote, price_change_24h, high_24h, low_24h,
                    min_qty, max_qty, step_size, min_notional, min_price, max_price,
                    tick_size, last_updated_price, max_fund, base_asset_balance,
                    quote_asset_balance, created_at, updated_at
                )
                SELECT
                    id, symbol, base_asset, quote_asset, is_active, description,
                    base_asset_precision, quote_asset_precision, current_price,
                    volume_24h, volume_24h_quote, price_change_24h, high_24h, low_24h,
                    min_qty, max_qty, step_size, min_notional, min_price, max_price,
                    tick_size, last_updated_price, max_fund, base_asset_balance,
                    quote_asset_balance, created_at, updated_at
                FROM trading_symbols
                """
            )

            # 3. 删除旧表
            conn.execute("DROP TABLE trading_symbols")

            # 4. 重命名新表
            conn.execute("ALTER TABLE trading_symbols_new RENAME TO trading_symbols")

            # 5. 重建索引
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trading_symbols_symbol ON trading_symbols(symbol)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trading_symbols_active ON trading_symbols(is_active)"
            )

            # 6. 重建触发器
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS update_trading_symbols_timestamp
                AFTER UPDATE ON trading_symbols
                BEGIN
                    UPDATE trading_symbols SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
                """
            )

            logger.info("✅ 已删除 trading_symbols 表的 trading_mode 字段")

    def migration_v13_change_daily_max_percentage_type(self) -> None:
        """迁移 v13: 将 daily_max_percentage 字段类型从 INTEGER 改为 REAL 以支持小数"""
        if not self.table_exists("symbol_timeframe_configs"):
            logger.error("表 symbol_timeframe_configs 不存在")
            raise ValueError("表 symbol_timeframe_configs 不存在")

        # 检查字段是否存在
        if not self.column_exists("symbol_timeframe_configs", "daily_max_percentage"):
            logger.error("字段 daily_max_percentage 不存在")
            raise ValueError("字段 daily_max_percentage 不存在")

        with self.db_manager.transaction() as conn:
            self._create_symbol_timeframe_table_clone(conn)
            self._copy_symbol_timeframe_data(conn)
            self._swap_symbol_timeframe_tables(conn)
            self._rebuild_symbol_timeframe_indexes(conn)
            self._rebuild_symbol_timeframe_triggers(conn)

        logger.info("✅ 已将 daily_max_percentage 字段类型从 INTEGER 改为 REAL")
        logger.info("📝 现在可以支持小数值,如 1.5,0.5 等")
        logger.info("⚠️ 注意: 外键约束已被移除,这不会影响系统正常运行")

    @staticmethod
    def _create_symbol_timeframe_table_clone(conn: Any) -> None:
        """创建 symbol_timeframe_configs 新表"""
        conn.execute(
            """
            CREATE TABLE symbol_timeframe_configs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trading_symbol TEXT NOT NULL,
                kline_timeframe TEXT DEFAULT '15m',
                demark_buy INTEGER DEFAULT 4,
                daily_max_percentage REAL DEFAULT 24.0,
                demark_percentage_coefficient REAL DEFAULT 1.0,
                monitor_delay REAL DEFAULT 0.8,
                oper_mode TEXT DEFAULT 'all',
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                minimum_profit_percentage REAL DEFAULT 0.4,
                UNIQUE(trading_symbol, kline_timeframe)
            )
        """
        )

    @staticmethod
    def _copy_symbol_timeframe_data(conn: Any) -> None:
        """复制旧表数据到新表并转换类型"""
        conn.execute(
            """
            INSERT INTO symbol_timeframe_configs_new
            SELECT
                id,
                trading_symbol,
                kline_timeframe,
                demark_buy,
                CAST(daily_max_percentage AS REAL),
                demark_percentage_coefficient,
                monitor_delay,
                oper_mode,
                is_active,
                created_at,
                updated_at,
                minimum_profit_percentage
            FROM symbol_timeframe_configs
        """
        )

    @staticmethod
    def _swap_symbol_timeframe_tables(conn: Any) -> None:
        """替换旧的 symbol_timeframe_configs 表"""
        conn.execute("DROP TABLE symbol_timeframe_configs")
        conn.execute(
            "ALTER TABLE symbol_timeframe_configs_new RENAME TO symbol_timeframe_configs"
        )

    @staticmethod
    def _rebuild_symbol_timeframe_indexes(conn: Any) -> None:
        """重建 symbol_timeframe_configs 索引"""
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_configs_symbol ON symbol_timeframe_configs(trading_symbol)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_configs_active ON symbol_timeframe_configs(is_active)"
        )

    @staticmethod
    def _rebuild_symbol_timeframe_triggers(conn: Any) -> None:
        """重建 symbol_timeframe_configs 触发器"""
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS update_timeframe_configs_timestamp
            AFTER UPDATE ON symbol_timeframe_configs
            BEGIN
                UPDATE symbol_timeframe_configs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END;
        """
        )

    def migration_v14_remove_commission_field(self) -> None:
        """迁移 v14: 删除 order_matches 表的 commission 字段"""
        if not self.table_exists("order_matches"):
            logger.error("表 order_matches 不存在")
            raise ValueError("表 order_matches 不存在")

        # 检查字段是否存在
        if not self.column_exists("order_matches", "commission"):
            logger.info("字段 commission 不存在,跳过删除")
            return

        with self.db_manager.transaction() as conn:
            # 直接删除 commission 字段
            conn.execute("ALTER TABLE order_matches DROP COLUMN commission")
            logger.info("✅ 已删除 order_matches 表的 commission 字段")
            logger.info("📝 撮合记录不再包含手续费信息,专注于价差利润计算")

    def migration_v15_add_unique_index(self) -> None:
        """迁移 v15: 为 order_matches 表添加 sell_order_no 和 buy_order_no 的唯一索引"""
        if not self.table_exists("order_matches"):
            logger.error("表 order_matches 不存在")
            raise ValueError("表 order_matches 不存在")

        with self.db_manager.transaction() as conn:
            # 检查是否已存在唯一索引
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name='idx_order_matches_unique_pair'
            """
            )
            if cursor.fetchone():
                logger.info("唯一索引 idx_order_matches_unique_pair 已存在,跳过创建")
                return

            # 创建唯一索引
            conn.execute(
                """
                CREATE UNIQUE INDEX idx_order_matches_unique_pair
                ON order_matches(sell_order_no, buy_order_no)
            """
            )
            logger.info(
                "✅ 已为 order_matches 表添加唯一索引 idx_order_matches_unique_pair"
            )
            logger.info("📝 防止同一对订单被重复撮合,确保数据唯一性")

    def migration_v16_rename_demark_min_signal_value(self) -> None:
        """迁移 v16: 重命名 symbol_timeframe_configs 表的 demark_min_signal_value 为 demark_buy"""
        if not self.table_exists("symbol_timeframe_configs"):
            logger.error("表 symbol_timeframe_configs 不存在")
            raise ValueError("表 symbol_timeframe_configs 不存在")

        # 检查旧字段是否存在
        if not self.column_exists(
            "symbol_timeframe_configs", "demark_min_signal_value"
        ):
            logger.info("字段 demark_min_signal_value 不存在,跳过重命名")
            return

        # 检查新字段是否已存在
        if self.column_exists("symbol_timeframe_configs", "demark_buy"):
            logger.info("字段 demark_buy 已存在,跳过重命名")
            return

        with self.db_manager.transaction() as conn:
            # 直接重命名字段
            conn.execute(
                "ALTER TABLE symbol_timeframe_configs RENAME COLUMN demark_min_signal_value TO demark_buy"
            )
            # 更新默认值为9(如果需要的话, 可以通过更新现有数据来模拟)
            conn.execute(
                "UPDATE symbol_timeframe_configs SET demark_buy = 9 WHERE demark_buy = 4"
            )
            logger.info("✅ 已将 demark_min_signal_value 字段重命名为 demark_buy")
            logger.info("📝 字段说明: DeMark买入信号阈值,默认值改为9")

    def migration_v17_add_demark_sell(self) -> None:
        """迁移 v17: 为 symbol_timeframe_configs 表添加 demark_sell 字段"""
        if not self.table_exists("symbol_timeframe_configs"):
            logger.error("表 symbol_timeframe_configs 不存在")
            raise ValueError("表 symbol_timeframe_configs 不存在")

        # 检查字段是否已存在
        if self.column_exists("symbol_timeframe_configs", "demark_sell"):
            logger.info("字段 demark_sell 已存在,跳过添加")
            return

        with self.db_manager.transaction() as conn:
            # 添加 demark_sell 字段,默认值为9
            conn.execute(
                "ALTER TABLE symbol_timeframe_configs ADD COLUMN demark_sell INTEGER DEFAULT 9"
            )
            logger.info("✅ 已为 symbol_timeframe_configs 表添加 demark_sell 字段")
            logger.info("📝 字段说明: DeMark卖出信号阈值,默认值为9")

    def migration_v18_add_max_buy_amount_period(self) -> None:
        """迁移 v18: 为 symbol_timeframe_configs 表添加 max_buy_amount_period 字段"""
        if not self.table_exists("symbol_timeframe_configs"):
            logger.error("表 symbol_timeframe_configs 不存在")
            raise ValueError("表 symbol_timeframe_configs 不存在")

        # 检查字段是否已存在
        if self.column_exists("symbol_timeframe_configs", "max_buy_amount_period"):
            logger.info("字段 max_buy_amount_period 已存在,跳过添加")
            return

        with self.db_manager.transaction() as conn:
            # 添加 max_buy_amount_period 字段,默认值为0.0
            conn.execute(
                "ALTER TABLE symbol_timeframe_configs ADD COLUMN max_buy_amount_period REAL DEFAULT 0.0"
            )
            logger.info(
                "✅ 已为 symbol_timeframe_configs 表添加 max_buy_amount_period 字段"
            )
            logger.info("📝 字段说明: 时间段内最大买入金额,默认值为0.0")

    def migration_v19_create_backtest_klines_table(self) -> None:
        """迁移 v19: 创建 backtest_klines 表用于存储回测K线数据"""
        if self.table_exists("backtest_klines"):
            logger.info("表 backtest_klines 已存在, 跳过创建")
            return

        with self.db_manager.transaction() as conn:
            # 创建回测K线数据表
            conn.execute(
                """
                CREATE TABLE backtest_klines (
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    open_time INTEGER NOT NULL,
                    open_price TEXT NOT NULL,
                    high_price TEXT NOT NULL,
                    low_price TEXT NOT NULL,
                    close_price TEXT NOT NULL,
                    volume TEXT NOT NULL,
                    close_time INTEGER NOT NULL,
                    quote_asset_volume TEXT NOT NULL,
                    number_of_trades INTEGER NOT NULL,
                    taker_buy_base_asset_volume TEXT NOT NULL,
                    taker_buy_quote_asset_volume TEXT NOT NULL,
                    PRIMARY KEY (symbol, timeframe, open_time)
                )
            """
            )
            logger.info("✅ 已创建 backtest_klines 表")

            # 创建索引
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_backtest_klines_symbol_timeframe_open_time
                ON backtest_klines(symbol, timeframe, open_time)
            """
            )
            logger.info("✅ 已为 backtest_klines 表创建索引")

    def migration_v20_add_buy_interval_minutes(self) -> None:
        """迁移 v20: 为 symbol_timeframe_configs 添加 buy_interval_minutes 字段"""
        if not self.table_exists("symbol_timeframe_configs"):
            logger.error("表 symbol_timeframe_configs 不存在")
            raise ValueError("表 symbol_timeframe_configs 不存在")

        # 已存在则跳过
        if self.column_exists("symbol_timeframe_configs", "buy_interval_minutes"):
            logger.info("字段 buy_interval_minutes 已存在,跳过添加")
            return

        with self.db_manager.transaction() as conn:
            conn.execute(
                "ALTER TABLE symbol_timeframe_configs ADD COLUMN buy_interval_minutes INTEGER DEFAULT 60"
            )
            logger.info(
                "✅ 已为 symbol_timeframe_configs 表添加 buy_interval_minutes 字段,默认60"
            )

    def migration_v21_add_minimum_price_change_percentage(self) -> None:
        """迁移 v21: 为 symbol_timeframe_configs 添加 minimum_price_change_percentage 字段"""
        table_name = "symbol_timeframe_configs"
        column_name = "minimum_price_change_percentage"

        if not self.table_exists(table_name):
            logger.error(f"表 {table_name} 不存在")
            raise ValueError(f"表 {table_name} 不存在")

        if self.column_exists(table_name, column_name):
            logger.info(f"字段 {column_name} 已存在,跳过添加")
            return

        with self.db_manager.transaction() as conn:
            conn.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} REAL DEFAULT 0.4"
            )
            conn.execute(
                f"UPDATE {table_name} SET {column_name} = 0.4 WHERE {column_name} IS NULL"
            )
            logger.info(f"✅ 已为 {table_name} 表添加 {column_name} 字段,默认0.4")

    def migration_v22_add_matched_time(self) -> None:
        """迁移 v22: 为 filled_orders 表增加撮合完成时间字段"""
        table_name = "filled_orders"
        column_name = "matched_time"

        if not self.table_exists(table_name):
            logger.error(f"表 {table_name} 不存在")
            raise ValueError(f"表 {table_name} 不存在")

        with self.db_manager.transaction() as conn:
            if not self.column_exists(table_name, column_name):
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT")
                logger.info(f"✅ 已为 {table_name} 表添加 {column_name} 字段")
            else:
                logger.info(f"字段 {column_name} 已存在,跳过添加")

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_filled_orders_matched_time ON filled_orders(matched_time)"
            )
            logger.info("✅ 已为 filled_orders.matched_time 创建索引")

            conn.execute(
                """
                UPDATE filled_orders
                SET matched_time = time
                WHERE matched_time IS NULL
                  AND side = 'BUY'
                  AND status = 'FILLED'
                  AND COALESCE(NULLIF(unmatched_qty, ''), '0') != ''
                  AND CAST(COALESCE(NULLIF(unmatched_qty, ''), '0') AS REAL) <= 0.0
                """
            )
            logger.info("✅ 已为历史BUY订单补齐 matched_time 数据")

    def migration_v23_add_permanent_indexes(self) -> None:
        """迁移 v23: 为填单和交易日志添加高频查询索引"""

        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_filled_orders_pair_side_status_time ON filled_orders(pair, side, status, time)",
            "CREATE INDEX IF NOT EXISTS idx_filled_orders_pair_status_client ON filled_orders(pair, status, client_order_id)",
            "CREATE INDEX IF NOT EXISTS idx_filled_orders_pair_status_unmatched ON filled_orders(pair, status, unmatched_qty)",
            "CREATE INDEX IF NOT EXISTS idx_filled_orders_pair_side_matched_time ON filled_orders(pair, side, matched_time)",
            "CREATE INDEX IF NOT EXISTS idx_trading_logs_symbol_timeframe_kline_time ON trading_logs(symbol, kline_timeframe, kline_time)",
        ]

        with self.db_manager.transaction() as conn:
            for statement in index_statements:
                conn.execute(statement)

        logger.info("✅ 高频索引创建完成")

    def migration_v24_convert_unmatched_qty_to_real(self) -> None:
        """迁移 v24: 将 filled_orders.unmatched_qty 改为 REAL"""

        table_name = "filled_orders"
        if not self.table_exists(table_name):
            logger.info("表 filled_orders 不存在, 跳过 v24")
            return

        with self.db_manager.transaction() as conn:
            conn.execute("DROP INDEX IF EXISTS idx_filled_orders_pair_status_unmatched")

            conn.execute(
                "ALTER TABLE filled_orders RENAME COLUMN unmatched_qty TO unmatched_qty_old"
            )
            conn.execute(
                "ALTER TABLE filled_orders ADD COLUMN unmatched_qty REAL DEFAULT 0"
            )
            conn.execute(
                "UPDATE filled_orders SET unmatched_qty = CAST(unmatched_qty_old AS REAL)"
            )

            with contextlib.suppress(Exception):
                conn.execute("ALTER TABLE filled_orders DROP COLUMN unmatched_qty_old")

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_filled_orders_pair_status_unmatched ON filled_orders(pair, status, unmatched_qty)"
            )

        logger.info("✅ unmatched_qty 字段已转换为 REAL")

    def migration_v25_add_trading_logs_run_time_index(self) -> None:
        """迁移 v25: 为 trading_logs 表创建 run_time 索引"""

        table_name = "trading_logs"
        if not self.table_exists(table_name):
            logger.info("表 trading_logs 不存在, 跳过 v25")
            return

        with self.db_manager.transaction() as conn:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trading_logs_run_time ON trading_logs(run_time DESC)"
            )

        logger.info("✅ 已为 trading_logs 表创建 run_time 索引")

    def migration_v26_convert_average_price_to_real(self) -> None:
        """迁移 v26: 将 filled_orders.average_price 改为 REAL"""

        table_name = "filled_orders"
        if not self.table_exists(table_name):
            logger.info("表 filled_orders 不存在, 跳过 v26")
            return

        with self.db_manager.transaction() as conn:
            conn.execute(
                "ALTER TABLE filled_orders RENAME COLUMN average_price TO average_price_old"
            )
            conn.execute(
                "ALTER TABLE filled_orders ADD COLUMN average_price REAL DEFAULT 0"
            )
            conn.execute(
                "UPDATE filled_orders SET average_price = CAST(average_price_old AS REAL)"
            )

            with contextlib.suppress(Exception):
                conn.execute("ALTER TABLE filled_orders DROP COLUMN average_price_old")

        logger.info("✅ average_price 字段已转换为 REAL")

    def migration_v27_add_trading_logs_ohlc(self) -> None:
        """迁移 v27: 为 trading_logs 表添加 OHLC 字段"""

        table_name = "trading_logs"
        if not self.table_exists(table_name):
            logger.info("表 trading_logs 不存在, 跳过 v27")
            return

        columns = [
            ("open", "REAL"),
            ("high", "REAL"),
            ("low", "REAL"),
            ("close", "REAL"),
        ]

        with self.db_manager.transaction() as conn:
            for column_name, column_definition in columns:
                if self.column_exists(table_name, column_name):
                    logger.info(f"字段 {column_name} 已存在, 跳过添加")
                    continue

                conn.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
                )
                logger.info(f"✅ 已为 trading_logs 表添加 {column_name} 字段")

    def migration_v28_add_backtest_perf_indexes(self) -> None:
        """迁移 v28: 为回测高频查询补充复合索引"""

        with self.db_manager.transaction() as conn:
            if self.table_exists("trading_logs"):
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_trading_logs_symbol_tf_kline_time
                    ON trading_logs(symbol, kline_timeframe, kline_time)
                    """
                )
                logger.info(
                    "✅ 已为 trading_logs 创建 idx_trading_logs_symbol_tf_kline_time"
                )
            else:
                logger.info("表 trading_logs 不存在, 跳过对应索引创建")

            if self.table_exists("filled_orders"):
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_filled_orders_pair_status_client_unmatched_time
                    ON filled_orders(pair, status, client_order_id, unmatched_qty, time)
                    """
                )
                logger.info(
                    "✅ 已为 filled_orders 创建 idx_filled_orders_pair_status_client_unmatched_time"
                )
            else:
                logger.info("表 filled_orders 不存在, 跳过对应索引创建")

    def migration_v29_create_filled_his_orders(self) -> None:
        """迁移 v29: 创建历史订单表及基础索引"""

        if self.table_exists("filled_his_orders"):
            logger.info("表 filled_his_orders 已存在, 跳过创建")
        else:
            with self.db_manager.transaction() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS filled_his_orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date_utc TEXT NOT NULL,
                        order_no TEXT NOT NULL UNIQUE,
                        pair TEXT NOT NULL,
                        order_type TEXT NOT NULL,
                        side TEXT NOT NULL,
                        order_price TEXT NOT NULL,
                        order_amount TEXT NOT NULL,
                        time TEXT NOT NULL,
                        executed TEXT NOT NULL,
                        trading_total TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        profit TEXT DEFAULT '0',
                        commission TEXT DEFAULT '0',
                        client_order_id TEXT,
                        matched_time TEXT,
                        unmatched_qty REAL DEFAULT 0,
                        average_price REAL DEFAULT 0
                    )
                    """
                )
                logger.info("✅ filled_his_orders 表创建完成")

        # 索引由 v30 负责

    def migration_v30_add_indexes_filled_his_orders(self) -> None:
        """迁移 v30: 为 filled_his_orders 补充基础索引"""

        if not self.table_exists("filled_his_orders"):
            logger.info("表 filled_his_orders 不存在, 跳过 v30")
            return

        index_statements = [
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_filled_his_orders_order_no ON filled_his_orders(order_no)",
            "CREATE INDEX IF NOT EXISTS idx_filled_his_orders_pair ON filled_his_orders(pair)",
            "CREATE INDEX IF NOT EXISTS idx_filled_his_orders_time ON filled_his_orders(time)",
            "CREATE INDEX IF NOT EXISTS idx_filled_his_orders_side ON filled_his_orders(side)",
            "CREATE INDEX IF NOT EXISTS idx_filled_his_orders_pair_side_time ON filled_his_orders(pair, side, time)",
        ]
        with self.db_manager.transaction() as conn:
            for statement in index_statements:
                conn.execute(statement)

        logger.info("✅ filled_his_orders 索引创建完成")

    def migration_v31_remove_entry_coefficient_multiplier(self) -> None:
        """迁移 v31: 删除 symbol_timeframe_configs 表的 entry_coefficient_multiplier 字段"""
        if not self.table_exists("symbol_timeframe_configs"):
            logger.error("表 symbol_timeframe_configs 不存在")
            raise ValueError("表 symbol_timeframe_configs 不存在")

        # 检查字段是否存在
        if not self.column_exists(
            "symbol_timeframe_configs", "entry_coefficient_multiplier"
        ):
            logger.info("字段 entry_coefficient_multiplier 不存在,跳过删除")
            return

        with self.db_manager.transaction() as conn:
            # SQLite 不支持直接删除字段,需要重建表
            # 1. 创建新表
            conn.execute(
                """
                CREATE TABLE symbol_timeframe_configs_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trading_symbol TEXT NOT NULL,
                    kline_timeframe TEXT DEFAULT '15m',
                    buy_interval_minutes INTEGER DEFAULT 60,
                    demark_buy INTEGER DEFAULT 9,
                    demark_sell INTEGER DEFAULT 9,
                    daily_max_percentage REAL DEFAULT 24.0,
                    demark_percentage_coefficient REAL DEFAULT 1.0,
                    monitor_delay REAL DEFAULT 0.8,
                    oper_mode TEXT DEFAULT 'all',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    minimum_profit_percentage REAL DEFAULT 0.4,
                    minimum_price_change_percentage REAL DEFAULT 0.4,
                    max_buy_amount_period REAL DEFAULT 0.0,
                    UNIQUE(trading_symbol, kline_timeframe)
                )
                """
            )

            # 2. 复制数据
            conn.execute(
                """
                INSERT INTO symbol_timeframe_configs_new (
                    id, trading_symbol, kline_timeframe, buy_interval_minutes,
                    demark_buy, demark_sell, daily_max_percentage,
                    demark_percentage_coefficient, monitor_delay, oper_mode,
                    is_active, created_at, updated_at, minimum_profit_percentage,
                    minimum_price_change_percentage, max_buy_amount_period
                )
                SELECT
                    id, trading_symbol, kline_timeframe, buy_interval_minutes,
                    demark_buy, demark_sell, daily_max_percentage,
                    demark_percentage_coefficient, monitor_delay, oper_mode,
                    is_active, created_at, updated_at, minimum_profit_percentage,
                    minimum_price_change_percentage, max_buy_amount_period
                FROM symbol_timeframe_configs
                """
            )

            # 3. 删除旧表
            conn.execute("DROP TABLE symbol_timeframe_configs")

            # 4. 重命名新表
            conn.execute(
                "ALTER TABLE symbol_timeframe_configs_new RENAME TO symbol_timeframe_configs"
            )

            # 5. 重建索引
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_configs_symbol ON symbol_timeframe_configs(trading_symbol)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_configs_active ON symbol_timeframe_configs(is_active)"
            )

            # 6. 重建触发器
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS update_timeframe_configs_timestamp
                AFTER UPDATE ON symbol_timeframe_configs
                BEGIN
                    UPDATE symbol_timeframe_configs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
                """
            )

            logger.info(
                "✅ 已删除 symbol_timeframe_configs 表的 entry_coefficient_multiplier 字段"
            )

    def migration_v32_remove_unused_configs(self) -> None:
        """迁移 v32: 删除 symbol_timeframe_configs 表的 buy_interval_minutes, demark_percentage_coefficient, max_buy_amount_period 字段"""
        if not self.table_exists("symbol_timeframe_configs"):
            logger.error("表 symbol_timeframe_configs 不存在")
            raise ValueError("表 symbol_timeframe_configs 不存在")

        # 检查字段是否存在 (只要有一个存在就执行迁移)
        fields_to_remove = [
            "buy_interval_minutes",
            "demark_percentage_coefficient",
            "max_buy_amount_period",
        ]
        has_any_field = False
        for field in fields_to_remove:
            if self.column_exists("symbol_timeframe_configs", field):
                has_any_field = True
                break

        if not has_any_field:
            logger.info("待删除字段均不存在,跳过 v32")
            return

        with self.db_manager.transaction() as conn:
            # SQLite 不支持直接删除字段,需要重建表
            # 1. 创建新表
            conn.execute(
                """
                CREATE TABLE symbol_timeframe_configs_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trading_symbol TEXT NOT NULL,
                    kline_timeframe TEXT DEFAULT '15m',
                    demark_buy INTEGER DEFAULT 9,
                    demark_sell INTEGER DEFAULT 9,
                    daily_max_percentage REAL DEFAULT 24.0,
                    monitor_delay REAL DEFAULT 0.8,
                    oper_mode TEXT DEFAULT 'all',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    minimum_profit_percentage REAL DEFAULT 0.4,
                    minimum_price_change_percentage REAL DEFAULT 0.4,
                    UNIQUE(trading_symbol, kline_timeframe)
                )
                """
            )

            # 2. 复制数据
            conn.execute(
                """
                INSERT INTO symbol_timeframe_configs_new (
                    id, trading_symbol, kline_timeframe,
                    demark_buy, demark_sell, daily_max_percentage,
                    monitor_delay, oper_mode,
                    is_active, created_at, updated_at, minimum_profit_percentage,
                    minimum_price_change_percentage
                )
                SELECT
                    id, trading_symbol, kline_timeframe,
                    demark_buy, demark_sell, daily_max_percentage,
                    monitor_delay, oper_mode,
                    is_active, created_at, updated_at, minimum_profit_percentage,
                    minimum_price_change_percentage
                FROM symbol_timeframe_configs
                """
            )

            # 3. 删除旧表
            conn.execute("DROP TABLE symbol_timeframe_configs")

            # 4. 重命名新表
            conn.execute(
                "ALTER TABLE symbol_timeframe_configs_new RENAME TO symbol_timeframe_configs"
            )

            # 5. 重建索引
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_configs_symbol ON symbol_timeframe_configs(trading_symbol)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_configs_active ON symbol_timeframe_configs(is_active)"
            )

            # 6. 重建触发器
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS update_timeframe_configs_timestamp
                AFTER UPDATE ON symbol_timeframe_configs
                BEGIN
                    UPDATE symbol_timeframe_configs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
                """
            )

            logger.info(
                "✅ 已删除 symbol_timeframe_configs 表的 buy_interval_minutes, demark_percentage_coefficient, max_buy_amount_period 字段"
            )

    def migration_v33_remove_max_trapped_percentage(self) -> None:
        """迁移 v33: 删除 trading_symbols 表的 max_trapped_percentage 字段"""
        if not self.table_exists("trading_symbols"):
            logger.error("表 trading_symbols 不存在")
            raise ValueError("表 trading_symbols 不存在")

        # 检查字段是否存在
        if not self.column_exists("trading_symbols", "max_trapped_percentage"):
            logger.info("字段 max_trapped_percentage 不存在,跳过 v33")
            return

        with self.db_manager.transaction() as conn:
            # SQLite 不支持直接删除字段,需要重建表
            # 1. 创建新表 (不包含 max_trapped_percentage)
            conn.execute(
                """
                CREATE TABLE trading_symbols_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    base_asset TEXT NOT NULL,
                    quote_asset TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    description TEXT,
                    base_asset_precision INTEGER DEFAULT 8,
                    quote_asset_precision INTEGER DEFAULT 8,
                    current_price REAL DEFAULT 0,
                    volume_24h REAL DEFAULT 0,
                    volume_24h_quote REAL DEFAULT 0,
                    price_change_24h REAL DEFAULT 0,
                    high_24h REAL DEFAULT 0,
                    low_24h REAL DEFAULT 0,
                    min_qty REAL DEFAULT 0,
                    max_qty REAL DEFAULT 0,
                    step_size REAL DEFAULT 0,
                    min_notional REAL DEFAULT 0,
                    min_price REAL DEFAULT 0,
                    max_price REAL DEFAULT 0,
                    tick_size REAL DEFAULT 0,
                    last_updated_price DATETIME,
                    max_fund INTEGER DEFAULT NULL,
                    base_asset_balance REAL DEFAULT 0.0,
                    quote_asset_balance REAL DEFAULT 0.0,
                    trading_mode TEXT DEFAULT 'arbitrage',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # 2. 复制数据 (排除 max_trapped_percentage)
            conn.execute(
                """
                INSERT INTO trading_symbols_new (
                    id, symbol, base_asset, quote_asset, is_active, description,
                    base_asset_precision, quote_asset_precision, current_price,
                    volume_24h, volume_24h_quote, price_change_24h, high_24h, low_24h,
                    min_qty, max_qty, step_size, min_notional, min_price, max_price,
                    tick_size, last_updated_price, max_fund, base_asset_balance,
                    quote_asset_balance, trading_mode, created_at, updated_at
                )
                SELECT
                    id, symbol, base_asset, quote_asset, is_active, description,
                    base_asset_precision, quote_asset_precision, current_price,
                    volume_24h, volume_24h_quote, price_change_24h, high_24h, low_24h,
                    min_qty, max_qty, step_size, min_notional, min_price, max_price,
                    tick_size, last_updated_price, max_fund, base_asset_balance,
                    quote_asset_balance, trading_mode, created_at, updated_at
                FROM trading_symbols
                """
            )

            # 3. 删除旧表
            conn.execute("DROP TABLE trading_symbols")

            # 4. 重命名新表
            conn.execute("ALTER TABLE trading_symbols_new RENAME TO trading_symbols")

            # 5. 重建索引
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trading_symbols_symbol ON trading_symbols(symbol)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trading_symbols_active ON trading_symbols(is_active)"
            )

            # 6. 重建触发器
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS update_trading_symbols_timestamp
                AFTER UPDATE ON trading_symbols
                BEGIN
                    UPDATE trading_symbols SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
                """
            )

            logger.info("✅ 已删除 trading_symbols 表的 max_trapped_percentage 字段")

    def migration_v35_remove_minimum_price_change_percentage(self) -> None:
        """迁移 v35: 删除 symbol_timeframe_configs 表的 minimum_price_change_percentage 字段"""
        if not self.table_exists("symbol_timeframe_configs"):
            logger.error("表 symbol_timeframe_configs 不存在")
            raise ValueError("表 symbol_timeframe_configs 不存在")

        # 检查字段是否存在
        if not self.column_exists(
            "symbol_timeframe_configs", "minimum_price_change_percentage"
        ):
            logger.info("字段 minimum_price_change_percentage 不存在,跳过 v35")
            return

        with self.db_manager.transaction() as conn:
            # 直接删除字段
            conn.execute(
                "ALTER TABLE symbol_timeframe_configs DROP COLUMN minimum_price_change_percentage"
            )
            logger.info(
                "✅ 已删除 symbol_timeframe_configs 表的 minimum_price_change_percentage 字段"
            )


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库迁移管理工具")
    _ = parser.add_argument("--target-version", type=int, help="目标版本号")
    _ = parser.add_argument("--status", action="store_true", help="显示迁移状态")
    _ = parser.add_argument("--rebuild", action="store_true", help="重建数据库(危险)")

    args = parser.parse_args()

    logger.info("🗄️ 数据库迁移管理工具")
    logger.info("=" * 50)

    # 获取数据库管理器
    db_manager = get_db_manager()
    migrator = DatabaseMigrator(db_manager)

    try:
        if args.status:
            migrator.show_status()
        elif args.rebuild:
            migrator.rebuild_database()
        else:
            target_version = args.target_version or migrator.get_latest_version()
            migrator.migrate_to_version(target_version)

    except Exception as e:
        logger.error(f"❌ 操作失败: {e}")
        sys.exit(1)

    logger.info("🎉 操作完成")


if __name__ == "__main__":
    main()
