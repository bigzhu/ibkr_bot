# GEMINI.md - ibkr_bot 开发指南

ibkr_bot 是支持多交易所的自动交易机器人,采用简化设计和模块化架构,当前正从币安(Binance) 迁移到 IBKR.

## 🌟 核心编程原则 (Guiding Principles)

这是我们合作的顶层思想,指导所有具体的行为.

### 设计原则与开发方法论

**核心原则 (The Zen of Python):**

- **Simple is better than complex.** - 简单优于复杂,代码应该像诗一样优美
- **Explicit is better than implicit.** - 显式优于隐式,清晰胜过模糊
- **Readability counts.** - 可读性很重要,优于其他考量
- **Errors should never pass silently.** - 错误不应该被静默忽略,fail-fast 保护数据

**设计范式:**

- **DRY (Don't Repeat Yourself):** 通过函数,类,模块消除重复,充分利用 Python 的抽象能力
- **高内聚,低耦合:** 利用 Python 模块系统实现清晰的代码组织
- **领域驱动设计 (DDD):** 采用 Domain Model 结合类型注解,以业务领域为核心组织代码
- **测试驱动开发 (TDD):** 使用 pytest 框架,每完成功能模块就立即编写测试
- **渐进式验证:** 利用 REPL/Jupyter 逐步验证每个组件
- **静态分析:** 使用 pyright/ruff 和 AI 工具提升代码质量

## 🚨 核心约束与原则 - 零容忍执行

### ⚠️ 对 Claude Code 的强制要求

**在编写任何代码之前,Claude Code 必须逐条检查以下规则.违反任何一条都必须立即重写.**

### 绝对禁止 - 发现即停止

1. **使用默认值掩盖错误** - 不检查None,让AttributeError自然发生
2. **使用相对导入** - 必须使用绝对导入
3. **创建超过 3 层的目录嵌套** - 保持扁平结构
4. **🚨 代码蔓延** - 禁止技术模块混入业务逻辑,业务模块混入技术实现
   - **技术模块**: demark(指标), ibkr_api(API,迁移中), database(数据访问)
   - **业务模块**: order_builder(交易), order_checker(风险), scheduler(调度)
   - **违规后果**: 职责混乱,维护成本激增

5. **🔄 重构规范** - 彻底重构,安全检查,拆分任务,消除重复
   - **彻底重构**: 根本解决问题,优先架构清晰度,不保留旧接口
   - **删除冗余**: 避免渐进式重构导致技术债务
   - **安全检查**: 重构前列出核心功能(数据库写入,API调用,计算逻辑,状态更新),重构后验证
   - **拆分任务**: 每个任务完成后征求用户确认
   - **消除重复**: 立即重构,用DRY原则(三元表达式,统一函数,公共逻辑)
   - **风险控制**: 多模块改动,大量文件变更,复杂架构调整必须拆分

6. **🚫 禁止无意义的函数封装** - 直接调用目标函数,避免中间层
   - **违规**: 函数内只有一行return,无额外逻辑
   - **例子**: `def get_price(symbol): return fetch_price(symbol)` ❌
   - **正确**: 直接调用 `fetch_price(symbol)` ✅

7. **🔧 函数内导入** - 除特殊场景外必须使用顶部导入
   - **特殊场景**: 循环导入避免,条件导入,延迟导入,插件架构
   - **正确做法**: 所有导入按 PEP 8 标准在文件顶部

8. **🔒 禁止自行提交 git commit** - 所有变更由用户明确要求才能提交
   - **工作流程**: 修改代码 → 质量检查 → 报告变更摘要 → 等待用户指示

### 强制要求 - 必须执行

1. **中文规范** - 用户沟通用中文,代码术语用英文,标点用英文半角
   - 用户沟通(注释,文档,交互)必须中文,代码实体(变量名,函数名,类名)必须英文
   - 仅允许英文标点 (,.;:!?""''()[]<>),禁止中文标点,违规使用 `scripts/fix_chinese_punctuation.py` 自动修复

2. **代码结构规范** - 单一职责,纯函数,完整注解
   - 每个文件只做一件事,每个 Python 文件都有 `if __name__ == "__main__":` 入口
   - 优先使用纯函数,所有参数和返回值必须有完整类型注解
   - 禁止全局变量和单例模式,利用函数参数和返回值传递数据

3. **数据与日志规范** - Pydantic 验证,loguru 记录,事务保障
   - 所有数据模型使用 Pydantic 进行严格验证
   - 所有日志必须使用 loguru.logger,禁止 print();除调试外禁止自行输出日志,由上层统一处理
   - 所有数据库操作使用事务保证一致性;修改数据模型后必须同步更新 database/schema.py,Pydantic 模型,API 接口

4. **库与优化** - 优先复用,避免造轮子
   - 有合适的第三方库时主动建议使用,避免重复实现

5. **代码质量检查** - 修改完毕后强制执行 (P0 优先级)
   - 按顺序执行: `uv run ruff format .` → `uv run ruff check --fix .` → `uv run pyright .`
   - 所有检查必须通过,违规代码不能提交

### 核心原则 - 不可妥协

**数据完整性 > 程序稳定性**

- **fail-fast:** 异常时立即终止,保护资金安全
- **职责清晰:** 每个函数专注单一职责,异常由上层决定如何处理
- **信任调用方:** 参数验证仅在入口点进行,内部函数不做重复验证或二次加工
- **零容忍:** 发现违规立即停止,重新设计

### Claude Code 执行检查清单

在编写每个函数前必须逐一确认以下核心类别:

#### 代码质量 (Code Quality)

- [ ] 是否使用了中文标点 (,.;:!?""''()[]等)?
- [ ] 是否使用了 print() 而不是 logger?

#### 异常与错误处理 (Exception Handling)

- [ ] 是否使用了禁止的 try-except(仅允许导入路径处理)?
- [ ] 是否遵循 fail-fast 原则?
- [ ] 是否用默认值掩盖了可能的None错误?

#### 参数与职责分离 (Responsibility Separation)

- [ ] 是否在内部函数中进行了不必要的参数验证?
- [ ] 是否在内部函数中进行了参数二次加工?
- [ ] 是否出现代码蔓延(技术混入业务,业务混入技术)?
- [ ] 是否存在无意义的函数封装(一行return调用)?
- [ ] 是否在函数内使用了不必要的导入语句?

#### 重构与优化 (Refactoring)

- [ ] 重构是否彻底(删除旧代码,不保留兼容)?
- [ ] 是否识别并消除了重复代码(DRY原则)?
- [ ] 是否使用三元表达式简化if-else分支?
- [ ] 是否合并了重复的日志记录?

#### 任务管理 (Task Management)

- [ ] 重构时是否列出并验证了所有核心业务功能?
- [ ] 是否在每个小任务完成后征求了用户确认?

#### 提交前检查 (Pre-commit Checks)

- [ ] 修改完毕后是否执行了 `uv run ruff format .`?
- [ ] 修改完毕后是否执行了 `uv run ruff check --fix .`?
- [ ] 修改完毕后是否执行了 `uv run pyright .`?
- [ ] 完成后是否报告变更摘要并等待用户指示才提交?

### 边界层异常策略(例外条款)

仅在边界层允许捕获特定异常用于资源清理或返回规范化错误,但必须遵循 fail-fast:

**允许捕获:**

- WebSocket 连接: 仅捕获连接关闭类异常,用于清理;未知异常必须上抛
- HTTP 路由入口: 仅校验可预期的输入错误或鉴权失败;不可预期异常交由框架处理
- 事务回滚层: 仅用于回滚,不屏蔽根因;必须重新抛出

**禁止与必须:**

- ❌ 在业务核心算法,数据校验,领域逻辑中使用 `try/except`
- ❌ 捕获 `Exception` 后无条件吞没或返回默认值
- ✅ 捕获的异常必须用 `loguru.logger` 记录上下文信息
- ✅ 处理后必须 `raise` 或让框架接管,保持失败可见

## 🚀 架构设计原则

- **最小依赖:** 只保留必要的第三方库
- **扁平结构:** 避免过深目录嵌套(最多 3 层),模块职责明确
- **领域驱动:** 以业务领域为核心组织代码,明确领域边界

### 模块结构

```text
ibkr_bot/
├── backtester/          # 回测系统
│   ├── result_docs/     # 回测结果文档
│   └── tests/           # 回测测试
├── binance_api/         # IBKR API 调用(迁移中, 原 Binance 封装)
├── database/            # 数据库操作和连接管理
│   └── models/          # 数据库模型定义
├── data/                # 数据存储
│   ├── backups/         # 数据库备份
│   ├── imports/         # 导入数据
│   └── logs/            # 数据日志
├── indicators/          # 技术指标计算(统一指标包)
│   ├── atr/             # 平均真实波幅 (ATR)
│   ├── demark/          # DeMark 14 指标
│   ├── ema/             # 指数移动平均线 (EMA)
│   ├── supertrend/      # SuperTrend 指标
│   └── td_iven/         # TD DeMark IV指标
├── logs/                # 应用日志存储
├── order_builder/       # 订单构建和交易逻辑
│   ├── calculation/     # 订单计算逻辑
│   └── order/           # 订单管理
├── order_checker/       # 订单风险检查
├── order_filler/        # IBKR 订单处理(迁移中)
│   ├── data_access/     # 数据访问层
│   ├── data_samples/    # 数据样本
│   ├── matching/        # 订单撮合逻辑
│   ├── sync/            # 同步逻辑
│   └── workflows/       # 业务流程
├── scheduler/           # 定时任务调度
├── scripts/             # 工具脚本 (包含 migrate_database.py 等)
├── shared/              # 共享工具和配置
│   └── types/           # 共享类型定义
├── tests/               # 单元测试
├── typings/             # 第三方库类型存根
│   ├── apscheduler/     # APScheduler 类型定义
│   ├── binance/         # 历史 Binance 类型定义(将替换为 IBKR/ibapi)
│   ├── loguru/          # loguru 类型定义
│   ├── pandas/          # pandas 类型定义
│   └── shared/          # 共享库类型定义
└── web_admin/           # Web 管理界面
    ├── api/             # FastAPI 后端
    ├── frontend/        # Vue.js 前端
    ├── logs/            # Web 日志
    └── nginx/           # Nginx 配置
```

## 📋 技术栈

### 核心依赖

- ib_insync/ibapi - IBKR API 调用
- pydantic - 数据模型和验证
- loguru - 日志系统
- sqlite3 - 数据库
- fastapi - Web API 框架
- quasar/vue - 前端界面框架
- apscheduler - 定时任务调度引擎
- pandas - 数据处理和分析

### 数据库配置

- **主数据库文件**: `data/bot.db` - 项目的唯一数据库,存储所有业务数据
- **SQL语法要求**: 使用 `<>` 作为不等于操作符,禁止使用 `!=`
  - ✅ 正确: `WHERE status <> 'FILLED'`
  - ❌ 禁止: `WHERE status != 'FILLED'`

#### 重要字段说明

- **demark_buy**: DeMark买入信号阈值 (默认值: 9)
- **demark_sell**: DeMark卖出信号阈值 (默认值: 9)
  - 支持独立配置买卖信号的强度要求
  - 业务逻辑根据信号类型自动选择对应阈值
  - 全栈实现: 数据库→后端API→前端界面

### 开发工具

- ruff - 代码检查,格式化与自动修复
- pyright - 类型检查
- uv - 包管理和依赖管理
- pytest - 测试框架
- coverage.py - 测试覆盖率
  (如需 ESLint/前端相关,请在 web_admin 内单独配置)

### 测试驱动开发 (TDD) 规范

- **pytest 优先:** 充分利用 fixture 和参数化功能,使用 `pytest.raises` 验证异常
- **Red-Green-Refactor:** 编写失败的测试 → 最少代码通过 → 优化重构
- **测试覆盖率:** 使用 coverage.py 确保达到 90% 以上,在文档字符串中包含可执行示例

### AI 辅助开发指导原则

- **静态分析集成:** 使用 ruff 与 pyright 确保代码质量
- **IDE 增强:** 利用 AI 辅助的代码补全和重构建议
- **代码审查:** 对 AI 生成的代码进行 Pythonic 原则检查

### 命令映射

- `p` - 映射到 `uv run python`,用于快速执行Python脚本

### 工具脚本

- `scripts/fix_chinese_punctuation.py` - 修复中文标点: `uv run python scripts/fix_chinese_punctuation.py` 或自动模式 `--auto`
- `scripts/migrate_database.py` - 数据库迁移: `p scripts/migrate_database.py [--status|--target-version N|--rebuild]`
  - **重要**: 每次数据库变更都必须在此文件中添加新的迁移函数

## 🛠️ 模块规范

### 基本约定

1. **独立运行** - 每个模块都有`if __name__ == "__main__":`入口
2. **明确接口** - `__init__.py`中用`__all__`导出主要功能
3. **双重用途** - 既可import使用,也可独立运行;无参数=默认行为,有参数=按需执行

### 关键模块职责说明

**order_builder** - 订单编排器 (Orchestrator):

- 获取 DeMark 信号,检查 K 线是否已处理(防止重复下单)
- 同步和清理订单数据(调用 order_filler 的同步功能)
- 计算订单数量和价格参数
- 执行所有风险检查(调用 order_checker.check())
- 执行订单并更新交易日志
- 编排完整的订单生命周期: 信号获取 → 数据清理 → 参数计算 → 风险检查 → 订单执行

**order_checker** - 风险检查系统:

- 统一入口: `check(symbol, timeframe, side, demark, qty, entry_price, symbol_info, min_notional, open_orders)`
- 执行以下 5 个检查(严格顺序):
  1. DeMark 信号强度验证
  2. 交易所下单限制检查(数量,金额精度)
  3. 操作模式验证(当前模式是否允许买入/卖出)
  4. BUY 价格卫士(不高于已有未成交的 BUY 订单)
  5. SELL 价格卫士(不低于已有未成交的 SELL 订单)
- 异常抛出则拒绝下单,无异常则通过

**order_filler** - 订单管理系统 (同步,撮合,利润):

- **订单同步**: 从 IBKR API 获取已成交订单,存储到数据库
- **订单撮合**: SELL 订单与买单池撮合,按价格优先原则(最便宜先)
- **代理撮合**: 1m 时间周期为其他周期代理撮合操作
- **利润锁定**: 根据买入价格和目标利润率,计算可安全卖出的数量
- **CSV 导入**: 支持批量导入 IBKR 报表/历史订单数据
- 注意: order_filler 不执行下单,下单由 order_builder 负责

### 代码示例

```python
# ✅ 原子函数:异常向上传播(fail-fast)
def get_current_price(client, contract: object) -> Decimal:
    ticker = client.get_last_price(contract)
    return Decimal(str(ticker))

# ✅ 双重用途模块:导入路径处理 + 参数验证在入口
try:
    from ibkr_api.common import get_configured_client
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from common import get_configured_client

def main() -> None:
    symbol = sys.argv[1].strip().upper()  # 入口验证参数
    if not symbol:
        show_usage()
        return
    process(symbol)
```

---

**核心理念**:简化一切可以简化的,优化一切可以优化的,确保系统既强大又简洁.
