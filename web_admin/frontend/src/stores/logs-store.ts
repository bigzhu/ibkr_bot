import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api } from 'src/services';
import { formatAmount } from 'src/utils/formatters';

export type TradingLog = {
  id: number;
  symbol: string;
  action_type: string;
  result: string;
  created_at: string;
  timeframe?: string | null;
  signal_value?: number | string | null;
  order_side?: string | null;
  order_price?: number | string | null;
  order_qty?: number | string | null;
  profit_lock_qty?: number | string | null;
  order_id?: string | null;
  error_message?: string | null;
  kline_time?: string | null;
  run_time?: string | null;
  demark_percentage_coefficient?: number | string | null;
  from_price?: number | string | null;
  user_balance?: number | string | null;
  price_change_percentage?: number | string | null;
  trade_value_display?: string | null;
  trade_value_is_neutral?: boolean;
} & Record<string, unknown>;

export interface SystemLog {
  id: number;
  timestamp: string;
  level: string;
  message: string;
  logger_name: string;
  function_name?: string;
  line_number?: number;
  extra_data?: unknown;
}

export interface LogsFilter {
  // 交易日志筛选
  symbolFilter: string;
  actionTypeFilter: string;
  resultFilter: string;
  timeRangeFilter: 'today' | 'yesterday' | 'week' | 'month' | 'custom';
  customDateRange: {
    start: string;
    end: string;
  };

  // 系统日志筛选
  logLevelFilter: string;
  loggerNameFilter: string;
  messageSearchFilter: string;
}

export interface LogsStats {
  tradingLogs: {
    total: number;
    today: number;
    success: number;
    failed: number;
    byAction: { [key: string]: number };
    bySymbol: { [key: string]: number };
  };
  systemLogs: {
    total: number;
    today: number;
    byLevel: { [key: string]: number };
    byLogger: { [key: string]: number };
  };
}

const TRADE_VALUE_NEUTRAL_DISPLAYS = new Set(['-', '0', '$0.00']);

const toFiniteNumber = (value: unknown): number | null => {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null;
  }

  if (typeof value === 'string') {
    const parsed = parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
};

const calculateTradeValueDisplay = (log: Partial<TradingLog>): string => {
  const price = toFiniteNumber(log.order_price);
  if (price === null || price <= 0) {
    return '-';
  }

  const side = (log.order_side || '').toString().toUpperCase();
  const quantityCandidates: Array<unknown> =
    side === 'BUY'
      ? [log.order_qty]
      : [log.profit_lock_qty, log.order_qty];

  let quantity: number | null = null;
  for (const candidate of quantityCandidates) {
    const numeric = toFiniteNumber(candidate);
    if (numeric !== null && numeric >= 0) {
      quantity = numeric;
      break;
    }
  }

  if (quantity === null || quantity < 0) {
    return '-';
  }

  const tradeValue = price * quantity;
  if (tradeValue === 0) {
    return '$0.00';
  }

  return `$${formatAmount(tradeValue)}`;
};

const applyTradeValueMeta = (log: Partial<TradingLog>): void => {
  const display = calculateTradeValueDisplay(log);
  log.trade_value_display = display;
  log.trade_value_is_neutral = TRADE_VALUE_NEUTRAL_DISPLAYS.has(display);
};

const isObject = (value: unknown): value is Record<string, unknown> => {
  return typeof value === 'object' && value !== null;
};

const asOptionalString = (value: unknown): string | null => {
  if (typeof value === 'string') {
    return value;
  }
  return null;
};

const asNumberOrStringOrNull = (value: unknown): number | string | null => {
  if (typeof value === 'number' || typeof value === 'string') {
    return value;
  }
  return null;
};

const mapToTradingLog = (log: unknown): TradingLog | null => {
  if (!isObject(log)) {
    return null;
  }

  const id = log.id;
  const symbol = log.symbol;
  const createdAt = log.created_at;

  if (typeof id !== 'number' || typeof symbol !== 'string' || typeof createdAt !== 'string') {
    return null;
  }

  const actionType =
    typeof log.action_type === 'string'
      ? log.action_type
      : typeof log.side === 'string'
        ? log.side
        : 'UNKNOWN';

  const result =
    typeof log.result === 'string'
      ? log.result
      : typeof log.status === 'string'
        ? log.status
        : 'unknown';

  return {
    id,
    symbol,
    action_type: actionType,
    result,
    created_at: createdAt,
    timeframe: typeof log.kline_timeframe === 'string' ? log.kline_timeframe : null,
    signal_value: asNumberOrStringOrNull(log.demark),
    order_side: typeof log.side === 'string' ? log.side : null,
    order_price: asNumberOrStringOrNull(log.price),
    order_qty: asNumberOrStringOrNull(log.qty),
    profit_lock_qty: asNumberOrStringOrNull(log.profit_lock_qty),
    order_id: asOptionalString(log.order_id),
    error_message: asOptionalString(log.error ?? log.error_message),
    kline_time: asOptionalString(log.kline_time),
    run_time: asOptionalString(log.run_time),
    demark_percentage_coefficient: asNumberOrStringOrNull(log.demark_percentage_coefficient),
    from_price: asNumberOrStringOrNull(log.from_price),
    user_balance: asNumberOrStringOrNull(log.user_balance),
    price_change_percentage: asNumberOrStringOrNull(log.price_change_percentage),
  };
};

const mapToSystemLog = (log: unknown): SystemLog | null => {
  if (!isObject(log)) {
    return null;
  }

  const id = log.id;
  const timestamp = log.timestamp;
  const level = log.level;
  const message = log.message;
  const loggerName = log.logger_name;

  if (
    typeof id !== 'number' ||
    typeof timestamp !== 'string' ||
    typeof level !== 'string' ||
    typeof message !== 'string' ||
    typeof loggerName !== 'string'
  ) {
    return null;
  }

  return {
    id,
    timestamp,
    level,
    message,
    logger_name: loggerName,
    function_name: asOptionalString(log.function_name),
    line_number: typeof log.line_number === 'number' ? log.line_number : undefined,
    extra_data: log.extra_data,
  };
};

export const useLogsStore = defineStore(
  'logs-store',
  () => {
    const MAX_TRADING_LOGS = 5000; // 大幅增加缓存容量,避免筛选时重要记录被剪裁
    const MAX_SYSTEM_LOGS = 2000;

    // 状态
    const tradingLogs = ref<TradingLog[]>([]);
    const systemLogs = ref<SystemLog[]>([]);
    const tradingLogsLoading = ref(false);
    const systemLogsLoading = ref(false);
    const lastTradingLogsFetch = ref<number>(0);
    const lastSystemLogsFetch = ref<number>(0);
    const cacheTimeout = 30 * 1000; // 30秒缓存(日志变化较快)

    // 筛选条件状态
    const filters = ref<LogsFilter>({
      symbolFilter: '',
      actionTypeFilter: '',
      resultFilter: '',
      timeRangeFilter: 'today',
      customDateRange: {
        start: '',
        end: '',
      },
      logLevelFilter: '',
      loggerNameFilter: '',
      messageSearchFilter: '',
    });

    // 分页状态
    const tradingLogsPagination = ref({
      sortBy: 'created_at',
      descending: true,
      page: 1,
      rowsPerPage: 50,
    });

    const systemLogsPagination = ref({
      sortBy: 'timestamp',
      descending: true,
      page: 1,
      rowsPerPage: 50,
    });

    // 计算属性
    const needsTradingLogsRefresh = computed((): boolean => {
      return Date.now() - lastTradingLogsFetch.value > cacheTimeout;
    });

    const needsSystemLogsRefresh = computed((): boolean => {
      return Date.now() - lastSystemLogsFetch.value > cacheTimeout;
    });

    const stats = computed((): LogsStats => {
      // 使用浏览器本地时区获取今日日期
      const today = new Date().toLocaleDateString('sv-SE'); // YYYY-MM-DD 格式

      // 交易日志统计
      const tradingTotal = tradingLogs.value.length;
      const tradingToday = tradingLogs.value.filter((log) => {
        if (typeof log.created_at !== 'string') {
          return false;
        }
        return log.created_at.startsWith(today);
      }).length;
      const tradingSuccess = tradingLogs.value.filter((log) => log.result === 'success').length;
      const tradingFailed = tradingTotal - tradingSuccess;

      const byAction: { [key: string]: number } = {};
      const bySymbol: { [key: string]: number } = {};
      tradingLogs.value.forEach((log) => {
        byAction[log.action_type] = (byAction[log.action_type] || 0) + 1;
        bySymbol[log.symbol] = (bySymbol[log.symbol] || 0) + 1;
      });

      // 系统日志统计
      const systemTotal = systemLogs.value.length;
      const systemToday = systemLogs.value.filter((log) => {
        if (typeof log.timestamp !== 'string') {
          return false;
        }
        return log.timestamp.startsWith(today);
      }).length;

      const byLevel: { [key: string]: number } = {};
      const byLogger: { [key: string]: number } = {};
      systemLogs.value.forEach((log) => {
        byLevel[log.level] = (byLevel[log.level] || 0) + 1;
        byLogger[log.logger_name] = (byLogger[log.logger_name] || 0) + 1;
      });

      return {
        tradingLogs: {
          total: tradingTotal,
          today: tradingToday,
          success: tradingSuccess,
          failed: tradingFailed,
          byAction,
          bySymbol,
        },
        systemLogs: {
          total: systemTotal,
          today: systemToday,
          byLevel,
          byLogger,
        },
      };
    });

    const filteredTradingLogs = computed((): TradingLog[] => {
      let result = tradingLogs.value;

      // 交易对过滤
      if (filters.value.symbolFilter) {
        result = result.filter((log) => log.symbol === filters.value.symbolFilter);
      }

      // 操作类型过滤
      if (filters.value.actionTypeFilter) {
        result = result.filter((log) => log.action_type === filters.value.actionTypeFilter);
      }

      // 结果过滤
      if (filters.value.resultFilter) {
        result = result.filter((log) => log.result === filters.value.resultFilter);
      }

      // 时间范围过滤
      if (filters.value.timeRangeFilter !== 'custom') {
        const now = new Date();
        let startDate: Date;

        switch (filters.value.timeRangeFilter) {
          case 'today':
            startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            break;
          case 'yesterday':
            startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
            break;
          case 'week':
            startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            break;
          case 'month':
            startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
            break;
          default:
            startDate = new Date(0);
        }

        result = result.filter((log) => new Date(log.created_at) >= startDate);
      } else if (filters.value.customDateRange.start && filters.value.customDateRange.end) {
        const startDate = new Date(filters.value.customDateRange.start);
        const endDate = new Date(filters.value.customDateRange.end);
        result = result.filter((log) => {
          const logDate = new Date(log.created_at);
          return logDate >= startDate && logDate <= endDate;
        });
      }

      return result;
    });

    const filteredSystemLogs = computed((): SystemLog[] => {
      let result = systemLogs.value;

      // 日志级别过滤
      if (filters.value.logLevelFilter) {
        result = result.filter((log) => log.level === filters.value.logLevelFilter);
      }

      // Logger名称过滤
      if (filters.value.loggerNameFilter) {
        result = result.filter((log) => log.logger_name === filters.value.loggerNameFilter);
      }

      // 消息搜索过滤
      if (filters.value.messageSearchFilter.trim()) {
        const query = filters.value.messageSearchFilter.toLowerCase();
        result = result.filter((log) => log.message.toLowerCase().includes(query));
      }

      return result;
    });

    const availableSymbols = computed((): string[] => {
      const symbols = new Set<string>();
      tradingLogs.value.forEach((log) => symbols.add(log.symbol));
      return Array.from(symbols).sort();
    });

    const availableActionTypes = computed((): string[] => {
      const actionTypes = new Set<string>();
      tradingLogs.value.forEach((log) => actionTypes.add(log.action_type));
      return Array.from(actionTypes).sort();
    });

    const availableLogLevels = computed((): string[] => {
      const levels = new Set<string>();
      systemLogs.value.forEach((log) => levels.add(log.level));
      return Array.from(levels).sort();
    });

    const availableLoggers = computed((): string[] => {
      const loggers = new Set<string>();
      systemLogs.value.forEach((log) => loggers.add(log.logger_name));
      return Array.from(loggers).sort();
    });

    // 方法 - 获取交易日志
    const setTradingLogs = (logs: TradingLog[], limit = MAX_TRADING_LOGS): void => {
      const dedupedMap = new Map<number, TradingLog>();
      logs.forEach((log) => {
        const mergedLog = {
          ...dedupedMap.get(log.id),
          ...log,
        } as TradingLog;
        applyTradeValueMeta(mergedLog);
        dedupedMap.set(log.id, mergedLog);
      });

      tradingLogs.value = Array.from(dedupedMap.values()).slice(0, limit);
    };

    const prependTradingLog = (log: TradingLog, limit = MAX_TRADING_LOGS): void => {
      const existingIndex = tradingLogs.value.findIndex((item) => item.id === log.id);
      if (existingIndex !== -1) {
        tradingLogs.value.splice(existingIndex, 1);
      }
      const enrichedLog = { ...log } as TradingLog;
      applyTradeValueMeta(enrichedLog);
      tradingLogs.value.unshift(enrichedLog);
      if (tradingLogs.value.length > limit) {
        tradingLogs.value.length = limit;
      }
    };

    const updateTradingLogEntry = (id: number, fields: Partial<TradingLog>): boolean => {
      const index = tradingLogs.value.findIndex((log) => log.id === id);
      if (index !== -1) {
        const updatedLog = {
          ...tradingLogs.value[index],
          ...fields,
        } as TradingLog;
        applyTradeValueMeta(updatedLog);
        tradingLogs.value[index] = updatedLog;
        return true;
      }
      return false;
    };

    if (tradingLogs.value.length > 0) {
      setTradingLogs(tradingLogs.value);
    }

    const fetchTradingLogs = async (forceRefresh = false): Promise<void> => {
      if (!forceRefresh && !needsTradingLogsRefresh.value && tradingLogs.value.length > 0) {
        return;
      }

      tradingLogsLoading.value = true;
      try {
        const response = await api.get('/api/v1/trading-logs/logs', {
          params: {
            limit: MAX_TRADING_LOGS,
            page: 1,
          },
        });

        if (response.data?.success) {
          const normalizedLogs = (Array.isArray(response.data.logs) ? response.data.logs : [])
            .map(mapToTradingLog)
            .filter((log): log is TradingLog => log !== null);
          setTradingLogs(normalizedLogs);
          lastTradingLogsFetch.value = Date.now();
        } else {
          throw new Error('获取交易日志失败');
        }
      } catch (error) {
        console.error('❌ 获取交易日志出错:', error);
        throw error;
      } finally {
        tradingLogsLoading.value = false;
      }
    };

    // 方法 - 获取系统日志
    const setSystemLogs = (logs: SystemLog[], limit = MAX_SYSTEM_LOGS): void => {
      const dedupedMap = new Map<number, SystemLog>();
      logs.forEach((log) => {
        dedupedMap.set(log.id, {
          ...dedupedMap.get(log.id),
          ...log,
        });
      });

      systemLogs.value = Array.from(dedupedMap.values())
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        .slice(0, limit);
    };

    const fetchSystemLogs = async (forceRefresh = false): Promise<void> => {
      if (!forceRefresh && !needsSystemLogsRefresh.value && systemLogs.value.length > 0) {
        return;
      }

      systemLogsLoading.value = true;
      try {
        const response = await api.get('/api/v1/logs', {
          params: {
            limit: MAX_SYSTEM_LOGS,
            offset: 0,
          },
        });

        if (response.data?.success) {
          const normalizedLogs = (Array.isArray(response.data.logs) ? response.data.logs : [])
            .map(mapToSystemLog)
            .filter((log): log is SystemLog => log !== null);
          setSystemLogs(normalizedLogs);
          lastSystemLogsFetch.value = Date.now();
        } else {
          throw new Error('获取系统日志失败');
        }
      } catch (error) {
        console.error('❌ 获取系统日志出错:', error);
        throw error;
      } finally {
        systemLogsLoading.value = false;
      }
    };

    // 方法 - 清理交易日志
    const clearTradingLogs = async (): Promise<void> => {
      try {
        const response = await api.post('/api/v1/trading-logs/clear-all');

        if (response.data?.success) {
          setTradingLogs([]);
          lastTradingLogsFetch.value = Date.now();
        } else {
          throw new Error(response.data?.message || '清理交易日志失败');
        }
      } catch (error) {
        console.error('❌ 清理交易日志出错:', error);
        throw error;
      }
    };

    // 方法 - 清理系统日志
    const clearSystemLogs = async (): Promise<void> => {
      try {
        const response = await api.post('/api/v1/logs/clear');

        if (response.data?.success) {
          setSystemLogs([]);
          lastSystemLogsFetch.value = Date.now();
        } else {
          throw new Error(response.data?.message || '清理系统日志失败');
        }
      } catch (error) {
        console.error('❌ 清理系统日志出错:', error);
        throw error;
      }
    };

    // 方法 - 导出系统日志
    const exportSystemLogs = async (): Promise<Blob> => {
      try {
        const response = await api.get('/api/v1/logs/export', {
          responseType: 'blob',
        });
        return response.data;
      } catch (error) {
        console.error('❌ 导出系统日志出错:', error);
        throw error;
      }
    };

    // 方法 - 更新筛选条件
    const updateFilter = <K extends keyof LogsFilter>(key: K, value: LogsFilter[K]): void => {
      filters.value[key] = value;
    };

    // 方法 - 重置筛选条件
    const resetFilters = (): void => {
      filters.value = {
        symbolFilter: '',
        actionTypeFilter: '',
        resultFilter: '',
        timeRangeFilter: 'today',
        customDateRange: {
          start: '',
          end: '',
        },
        logLevelFilter: '',
        loggerNameFilter: '',
        messageSearchFilter: '',
      };
    };

    // 方法 - 更新交易日志分页设置
    const updateTradingLogsPagination = (
      newPagination: Partial<typeof tradingLogsPagination.value>,
    ): void => {
      Object.assign(tradingLogsPagination.value, newPagination);
    };

    // 方法 - 更新系统日志分页设置
    const updateSystemLogsPagination = (
      newPagination: Partial<typeof systemLogsPagination.value>,
    ): void => {
      Object.assign(systemLogsPagination.value, newPagination);
    };

    // 方法 - 清除缓存
    const clearCache = (): void => {
      lastTradingLogsFetch.value = 0;
      lastSystemLogsFetch.value = 0;
    };

    // 方法 - 获取今日交易日志数量
    const getTodayTradingLogsCount = (): number => {
      // 使用浏览器本地时区获取今日日期
      const today = new Date().toLocaleDateString('sv-SE'); // YYYY-MM-DD 格式
      return tradingLogs.value.filter((log) => {
        const createdAt = log.created_at;

        if (createdAt === null || createdAt === undefined) {
          return false;
        }

        const dateCandidate =
          createdAt instanceof Date
            ? createdAt
            : new Date(createdAt as string | number | Date);

        if (!Number.isNaN(dateCandidate.getTime())) {
          const localized = dateCandidate.toLocaleDateString('sv-SE');
          return localized === today;
        }

        const normalized = String(createdAt);
        return normalized.startsWith(today);
      }).length;
    };

    return {
      // 状态
      tradingLogs,
      systemLogs,
      tradingLogsLoading,
      systemLogsLoading,
      filters,
      tradingLogsPagination,
      systemLogsPagination,

      // 计算属性
      stats,
      filteredTradingLogs,
      filteredSystemLogs,
      availableSymbols,
      availableActionTypes,
      availableLogLevels,
      availableLoggers,
      needsTradingLogsRefresh,
      needsSystemLogsRefresh,

      // 方法
      fetchTradingLogs,
      fetchSystemLogs,
      setTradingLogs,
      prependTradingLog,
      updateTradingLogEntry,
      setSystemLogs,
      clearTradingLogs,
      clearSystemLogs,
      exportSystemLogs,
      updateFilter,
      resetFilters,
      updateTradingLogsPagination,
      updateSystemLogsPagination,
      clearCache,
      getTodayTradingLogsCount,
    };
  },
  {
    persist: {
      key: 'logs-store',
      storage: localStorage,
      paths: ['filters', 'tradingLogsPagination', 'systemLogsPagination'],
      afterHydrate: (context) => {
        const store = context.store as ReturnType<typeof useLogsStore>;

        store.tradingLogs = [];
        store.systemLogs = [];
        store.lastTradingLogsFetch = 0;
        store.lastSystemLogsFetch = 0;

        store.$persist();
      },
    },
  },
);
