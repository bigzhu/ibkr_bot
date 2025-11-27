import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { LocalStorage } from 'quasar';
import { apiService } from 'src/services';
import type {
  ManagedSymbol,
  SymbolCacheEntry,
  SymbolConfigStatsEntry,
} from 'src/types/symbols';
import type { SymbolSummary, TimeframeConfigSummary } from 'src/services';

const CACHE_KEY = 'symbols-store:list';
const CACHE_VERSION = '1.0';
const CACHE_TTL = 2 * 60 * 1000; // 2 minutes
const TIMEFRAME_CACHE_TTL = 60 * 1000; // 1 minute

interface CachedSymbolsPayload {
  version: string;
  timestamp: number;
  items: SymbolCacheEntry[];
}

const toBoolean = (value: unknown): boolean => value === true || value === 1;

const toNumberOrNull = (value: unknown): number | null => {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const createManagedSymbol = (symbol: SymbolSummary): ManagedSymbol => {
  const signalValue = toNumberOrNull(symbol.signal_value);
  const activeCount = toNumberOrNull(symbol.active_config_count) ?? 0;
  const inactiveCount = toNumberOrNull(symbol.inactive_config_count) ?? 0;
  const totalCount = toNumberOrNull(symbol.total_config_count) ?? activeCount + inactiveCount;

  return {
    id: symbol.id,
    symbol: symbol.symbol,
    signal_value: signalValue,
    is_active: toBoolean(symbol.is_active),
    base_asset: symbol.base_asset,
    quote_asset: symbol.quote_asset,
    current_price: symbol.current_price ?? null,
    price_change_24h: symbol.price_change_24h ?? null,
    active_config_count: activeCount,
    inactive_config_count: inactiveCount,
    total_config_count: totalCount,
    isToggling: false,
    isDeleting: false,
  };
};

const createManagedSymbolFromCache = (entry: SymbolCacheEntry): ManagedSymbol => ({
  id: entry.id,
  symbol: entry.symbol,
  signal_value: entry.signal_value ?? null,
  is_active: entry.is_active,
  base_asset: entry.base_asset,
  quote_asset: entry.quote_asset,
  current_price: entry.current_price ?? null,
  price_change_24h: entry.price_change_24h ?? null,
  active_config_count: entry.active_config_count ?? 0,
  inactive_config_count: entry.inactive_config_count ?? 0,
  total_config_count: entry.total_config_count ?? 0,
  isToggling: false,
  isDeleting: false,
});

const sanitizeSymbolsForCache = (items: ManagedSymbol[]): SymbolCacheEntry[] =>
  items.map((item) => ({
    id: item.id,
    symbol: item.symbol,
    signal_value: item.signal_value ?? null,
    is_active: item.is_active,
    base_asset: item.base_asset,
    quote_asset: item.quote_asset,
    current_price: item.current_price ?? null,
    price_change_24h: item.price_change_24h ?? null,
    active_config_count: item.active_config_count,
    inactive_config_count: item.inactive_config_count,
    total_config_count: item.total_config_count,
  }));

export const useSymbolsStore = defineStore('symbols-store', () => {
  const symbols = ref<ManagedSymbol[]>([]);
  const symbolStats = ref<Record<string, SymbolConfigStatsEntry>>({});
  const loading = ref(false);
  const error = ref<string | null>(null);
  const lastFetchTime = ref<number>(0);

  const stats = computed(() => {
    const total = symbols.value.length;
    const active = symbols.value.filter((symbol) => symbol.is_active).length;
    const inactive = total - active;
    const withTimeframes = symbols.value.filter((symbol) => symbol.active_config_count > 0).length;

    return { total, active, inactive, withTimeframes };
  });

  const needsRefresh = computed(() => Date.now() - lastFetchTime.value > CACHE_TTL);

  const loadCache = (): { items: ManagedSymbol[]; timestamp: number } | null => {
    const payload = LocalStorage.getItem<CachedSymbolsPayload | null>(CACHE_KEY);
    if (!payload || payload.version !== CACHE_VERSION) {
      return null;
    }

    const items = Array.isArray(payload.items)
      ? payload.items.map(createManagedSymbolFromCache)
      : [];

    return { items, timestamp: payload.timestamp };
  };

  const persistCache = () => {
    const payload: CachedSymbolsPayload = {
      version: CACHE_VERSION,
      timestamp: Date.now(),
      items: sanitizeSymbolsForCache(symbols.value),
    };

    LocalStorage.set(CACHE_KEY, payload);
  };

  const setSymbols = (items: ManagedSymbol[], timestamp: number | null = null) => {
    symbols.value = items;
    const statsMap: Record<string, SymbolConfigStatsEntry> = {};

    items.forEach((item) => {
      statsMap[item.symbol] = {
        active: item.active_config_count,
        inactive: item.inactive_config_count,
        total: item.total_config_count,
      };
    });

    symbolStats.value = statsMap;

    if (timestamp !== null) {
      lastFetchTime.value = timestamp;
    }
  };

  interface CachedTimeframeEntry {
    configs: TimeframeConfigSummary[];
    timestamp: number;
  }

  const timeframeConfigsCache = ref<Record<string, CachedTimeframeEntry>>({});

  const setTimeframeConfigsCache = (symbol: string, configs: TimeframeConfigSummary[]): void => {
    timeframeConfigsCache.value[symbol] = {
      configs: configs.map((config) => ({
        ...config,
        is_active: toBoolean(config.is_active),
      })),
      timestamp: Date.now(),
    };
  };

  const getTimeframeConfigsCache = (symbol: string): CachedTimeframeEntry | null => {
    return timeframeConfigsCache.value[symbol] ?? null;
  };

  const clearTimeframeConfigCache = (symbol?: string): void => {
    if (symbol) {
      delete timeframeConfigsCache.value[symbol];
    } else {
      timeframeConfigsCache.value = {};
    }
  };

  const recomputeSymbolStats = (symbol: string): void => {
    const cached = timeframeConfigsCache.value[symbol];
    if (!cached) {
      return;
    }

    const activeCount = cached.configs.filter((config) => toBoolean(config.is_active)).length;
    const inactiveCount = cached.configs.length - activeCount;

    updateSymbolStats(symbol, {
      active: activeCount,
      inactive: inactiveCount,
      total: cached.configs.length,
    });
  };

  const fetchTimeframeConfigs = async (
    symbol: string,
    forceRefresh = false,
  ): Promise<TimeframeConfigSummary[]> => {
    if (!forceRefresh) {
      const cached = getTimeframeConfigsCache(symbol);
      if (cached && Date.now() - cached.timestamp <= TIMEFRAME_CACHE_TTL) {
        return cached.configs;
      }
    }

    const response = await apiService.timeframeConfig.getConfigsBySymbol(symbol);
    if (!response.success || !Array.isArray(response.configs)) {
      throw new Error(response.message || '获取时间周期配置失败');
    }

    const normalized = response.configs.map((config) => ({
      ...config,
      is_active: toBoolean(config.is_active),
    }));

    setTimeframeConfigsCache(symbol, normalized);
    recomputeSymbolStats(symbol);

    return normalized;
  };

  const applyTimeframeConfigPatch = (
    symbol: string,
    configId: number,
    patch: Partial<TimeframeConfigSummary>,
  ): void => {
    const entry = getTimeframeConfigsCache(symbol);
    if (!entry) {
      return;
    }

    const index = entry.configs.findIndex((config) => config.id === configId);
    if (index === -1) {
      return;
    }

    const nextConfig = {
      ...entry.configs[index],
      ...patch,
    };
    nextConfig.is_active = toBoolean(nextConfig.is_active);
    entry.configs[index] = nextConfig;
    entry.timestamp = Date.now();

    recomputeSymbolStats(symbol);
  };

  const initializeFromCache = () => {
    const cached = loadCache();
    if (cached && cached.items.length > 0) {
      setSymbols(cached.items, cached.timestamp);
    }
  };

  const findSymbolIndexById = (id: number): number => symbols.value.findIndex((item) => item.id === id);
  const findSymbolIndexByName = (name: string): number =>
    symbols.value.findIndex((item) => item.symbol === name);

  const getSymbolById = (id: number): ManagedSymbol | undefined => {
    const index = findSymbolIndexById(id);
    return index === -1 ? undefined : symbols.value[index];
  };

  const getSymbolByName = (name: string): ManagedSymbol | undefined => {
    const index = findSymbolIndexByName(name);
    return index === -1 ? undefined : symbols.value[index];
  };

  const updateSymbolStats = (symbolName: string, statsEntry: SymbolConfigStatsEntry): void => {
    symbolStats.value[symbolName] = statsEntry;

    const target = getSymbolByName(symbolName);
    if (target) {
      target.active_config_count = statsEntry.active;
      target.inactive_config_count = statsEntry.inactive;
      target.total_config_count = statsEntry.total;
      persistCache();
    }
  };

  const fetchSymbols = async (forceRefresh = false): Promise<void> => {
    if (!forceRefresh && !needsRefresh.value && symbols.value.length > 0) {
      return;
    }

    loading.value = true;
    error.value = null;

    try {
      const response = await apiService.symbol.getSymbols();
      if (!response.success) {
        throw new Error(response.message || '获取交易对列表失败');
      }

      const mapped = response.symbols.map(createManagedSymbol);
      setSymbols(mapped, Date.now());
      persistCache();
    } catch (err) {
      const message = err instanceof Error ? err.message : '获取交易对列表失败';
      error.value = message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const refreshSymbolConfigStats = async (symbolName: string): Promise<void> => {
    const response = await apiService.timeframeConfig.getConfigsBySymbol(symbolName);
    if (!response.success || !Array.isArray(response.configs)) {
      return;
    }

    const normalized = response.configs.map((config: TimeframeConfigSummary) => ({
      ...config,
      is_active: toBoolean(config.is_active),
    }));

    const activeCount = normalized.filter((config) => config.is_active).length;
    const inactiveCount = normalized.length - activeCount;

    updateSymbolStats(symbolName, {
      active: activeCount,
      inactive: inactiveCount,
      total: normalized.length,
    });
  };

  const toggleSymbolStatus = async (symbol: ManagedSymbol): Promise<void> => {
    const index = findSymbolIndexById(symbol.id);
    if (index === -1) {
      return;
    }

    const target = symbols.value[index];
    if (target.isToggling) {
      return;
    }

    const previous = target.is_active;
    const nextStatus = !previous;
    target.isToggling = true;

    try {
      const response = await apiService.symbol.updateSymbol(symbol.id, {
        is_active: nextStatus,
      });

      if (!response.success) {
        throw new Error(response.message || '更新交易对状态失败');
      }

      target.is_active = nextStatus;
      persistCache();
    } catch (err) {
      target.is_active = previous;
      throw err;
    } finally {
      target.isToggling = false;
      persistCache();
    }
  };





  const deleteSymbol = async (symbol: ManagedSymbol): Promise<void> => {
    const index = findSymbolIndexById(symbol.id);
    if (index === -1) {
      return;
    }

    const response = await apiService.symbol.deleteSymbol(symbol.id);
    if (!response.success) {
      throw new Error(response.message || '删除交易对失败');
    }

    symbols.value.splice(index, 1);
    delete symbolStats.value[symbol.symbol];
    clearTimeframeConfigCache(symbol.symbol);
    persistCache();
  };

  const addSymbol = async (payload: {
    symbol: string;
    description?: string;
    max_fund?: number | null;
  }): Promise<void> => {
    const response = await apiService.symbol.addSymbol(payload);
    if (!response.success) {
      throw new Error(response.message || '添加交易对失败');
    }

    await fetchSymbols(true);
  };

  initializeFromCache();

  return {
    symbols,
    symbolStats,
    stats,
    loading,
    error,
    needsRefresh,
    fetchSymbols,
    fetchTimeframeConfigs,
    applyTimeframeConfigPatch,
    clearTimeframeConfigCache,
    refreshSymbolConfigStats,
    updateSymbolStats,
    toggleSymbolStatus,
    deleteSymbol,
    addSymbol,
    getSymbolById,
    getSymbolByName,
  };
});
