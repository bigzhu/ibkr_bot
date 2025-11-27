# TD IVEN 指标规则与规划

## 规则拆解

- **Setup 计数 (1-9)**: `buySet` 当 `close < close[4]` 时递增, `sellSet` 当 `close > close[4]` 递增, 任一条件失效即归零; 触发 9 时会记录最近 9 根的最高/最低价用于后续支撑阻力.
- **Stealth 9**: 当 `buySet` 最近一次达到 8 且 `sellSet == 1`(或反向)时触发, 对应 TradingView 中 `ta.barssince(set == 8) <= 1` 的"隐形"信号.
- **支撑/阻力线**: `buySet == 9` 记录最近 9 根最高价为阻力, 若之后 `close` 高于该值则失效; `sellSet == 9` 对最低价做镜像逻辑作为支撑.
- **标准 Countdown**: 由 `buySet == 9`/`sellSet == 9` 开始, 条件分别为 `close < low[2]` 与 `close > high[2]`, 计数 1-13; 遇到反向 set==9 或支撑/阻力失效会直接重置为 14, 出现非合格 13 时以 `-12` 标识继续跟踪.
- **激进 Countdown**: 同样由 `buySet == 9`/`sellSet == 9` 触发, 但条件放宽为 `low < low[2]` / `high > high[2]`, 不做非合格 13 处理.
- **Alert 条件**: `ct9` 为任一 Setup == 9; `ct13` 为标准 Countdown == 13; `cta13` 为激进 Countdown == 13; `ct913` 为两者合集, 与 pine 脚本保持一致.

## Python 实现要点

- **数据依赖**: 需要至少 34 根完整 K 线以覆盖 9 Setup + 13 Countdown + 安全缓冲, 严格使用 `Decimal` 计算避免精度问题.
- **简化接口**: 暴露 `td_iven(klines) -> tuple[str, int, int]`, 仅返回 side(BUY/SELL/NONE),setup(1-9) 与标准 countdown(可超过 13), 与 `indicators.demark` 一致又便于扩展.
- **内部逻辑**: 虽然对外接口简洁, 内部仍保留非合格 13 与趋势线失效等 pine 细节, 确保信号与 TradingView 行为一致.

## 开发计划

1. **v1 (当前任务)**: 完成纯计算模块,币安封装,最小化单元测试与本文档.
2. **v2**: 视业务需要输出更多中间状态(如 stealth,趋势线值)或暴露更多参数.
3. **v3**: 支持更多 TradingView 选项(自定义 `lastN`, `showST` 等), 增强参数验证与可视化集成.
