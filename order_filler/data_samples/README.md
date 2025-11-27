# 样本数据文件

此目录存储用于测试和开发的样本数据文件.

## 文件说明

### binance_sample_orders.csv
币安交易所导出的订单样本数据,用于测试 CSV 导入功能.

**使用示例:**
```bash
p order_filler/csv_importer.py order_filler/data_samples/binance_sample_orders.csv
```

**文件格式:**
- BOM 编码的 UTF-8 CSV
- 包含币安标准的订单字段
- 状态为 CANCELED (示例数据,非真实交易)

## 注意事项

- 所有样本数据仅用于测试,不包含真实账户信息
- 导入前应先备份主数据库
- 确保数据库已通过 `scripts/migrate_database.py` 初始化
