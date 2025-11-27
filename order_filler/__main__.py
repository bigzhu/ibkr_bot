"""
币安已成交订单模块命令行入口
"""

# 统一双重用途模块导入处理(仅处理 ImportError)
try:
    from shared.path_utils import add_project_root_to_path
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from shared.path_utils import add_project_root_to_path

add_project_root_to_path()

from order_filler import main

if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        # 有参数时执行一键同步和撮合
        symbol = sys.argv[1].upper()
        timeframe = sys.argv[2].lower()

        from order_filler.workflows.sync_and_match import main as sync_main

        # 设置命令行参数供workflows使用
        sys.argv = ["order_filler.workflows", symbol, timeframe]
        sync_main()
    else:
        # 无参数时显示模块功能
        main()
