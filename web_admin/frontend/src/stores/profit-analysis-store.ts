import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { apiService } from 'src/services';

// 删除了SellOrder接口,现在只使用后端汇总数据

export interface DailyProfit {
  date: string;
  order_count: number;
  total_profit: number;
  total_commission: number;
  net_profit: number;
}

export interface MonthlyProfit {
  month: string;
  order_count: number;
  total_profit: number;
  total_commission: number;
  net_profit: number;
}

export interface SymbolProfit {
  symbol: string;
  order_count: number;
  total_profit: number;
  total_commission: number;
  net_profit: number;
}

export interface SymbolDailyProfit {
  symbol: string;
  date: string;
  order_count: number;
  total_profit: number;
  total_commission: number;
  net_profit: number;
}

export const useProfitAnalysisStore = defineStore(
  'profit-analysis',
  () => {
    // 状态
    const dailyProfitsData = ref<DailyProfit[]>([]);
    const monthlyProfitsData = ref<MonthlyProfit[]>([]);
    const symbolProfitsData = ref<SymbolProfit[]>([]);
    const symbolDailyProfitsData = ref<SymbolDailyProfit[]>([]);
    const dailyProfitsLoading = ref(false);
    const monthlyProfitsLoading = ref(false);
    const symbolProfitsLoading = ref(false);
    const symbolDailyProfitsLoading = ref(false);
    const lastDailyProfitsFetchTime = ref<number>(0);
    const lastMonthlyProfitsFetchTime = ref<number>(0);
    const lastSymbolProfitsFetchTime = ref<number>(0);
    const lastSymbolDailyProfitsFetchTime = ref<number>(0);
    const cacheTimeout = 5 * 60 * 1000; // 5分钟缓存
    const DEFAULT_QUOTE_ASSET = 'USDT';

    const normalizeQuoteAsset = (value?: string): string => {
      return (value || DEFAULT_QUOTE_ASSET).toUpperCase();
    };

    const lastDailyQuoteAsset = ref<string>(DEFAULT_QUOTE_ASSET);
    const lastMonthlyQuoteAsset = ref<string>(DEFAULT_QUOTE_ASSET);
    const lastSymbolQuoteAsset = ref<string>(DEFAULT_QUOTE_ASSET);
    const lastSymbolDailyQuoteAsset = ref<string>(DEFAULT_QUOTE_ASSET);

    // 计算属性 - 今日收益 (基于后端每日盈亏数据)
    const todayProfit = computed((): number => {
      const today = new Date().toLocaleDateString('sv-SE'); // YYYY-MM-DD格式
      const todayData = dailyProfitsData.value.find((d) => d.date === today);
      return todayData?.net_profit || 0;
    });

    // 计算属性 - 总收益 (基于后端每日盈亏数据)
    const totalProfit = computed((): number => {
      return dailyProfitsData.value.reduce((sum, daily) => sum + daily.net_profit, 0);
    });

    // 删除了前端获取全量数据的方法,现在只使用后端汇总接口

    // 方法 - 获取每日盈亏数据(直接从后端)
    const fetchDailyProfits = async (
      params?: {
        start_date?: string;
        end_date?: string;
        symbol?: string;
      },
      forceRefresh = false,
      quoteAsset: string = DEFAULT_QUOTE_ASSET,
    ): Promise<void> => {
      const resolvedQuoteAsset = normalizeQuoteAsset(quoteAsset);
      const hasFilters = Boolean(params && Object.keys(params).length > 0);

      if (
        !forceRefresh &&
        !hasFilters &&
        lastDailyQuoteAsset.value === resolvedQuoteAsset &&
        Date.now() - lastDailyProfitsFetchTime.value < cacheTimeout &&
        dailyProfitsData.value.length > 0
      ) {
        return;
      }

      dailyProfitsLoading.value = true;
      try {
        const requestParams = {
          ...(params ?? {}),
          quote_asset: resolvedQuoteAsset,
        };
        const response = await apiService.profitAnalysis.getDailyProfits(requestParams);

        if (response.success && response.data) {
          dailyProfitsData.value = Array.isArray(response.data) ? response.data : [];
          if (!hasFilters) {
            lastDailyProfitsFetchTime.value = Date.now();
            lastDailyQuoteAsset.value = resolvedQuoteAsset;
          }
        } else {
          console.warn('⚠️ 获取每日盈亏数据失败:', response);
        }
      } catch (error) {
        console.error('❌ 获取每日盈亏数据出错:', error);
      } finally {
        dailyProfitsLoading.value = false;
      }
    };

    const fetchMonthlyProfits = async (
      params?: {
        start_date?: string;
        end_date?: string;
        symbol?: string;
      },
      forceRefresh = false,
      quoteAsset: string = DEFAULT_QUOTE_ASSET,
    ): Promise<void> => {
      const resolvedQuoteAsset = normalizeQuoteAsset(quoteAsset);
      const hasFilters = Boolean(params && Object.keys(params).length > 0);

      if (
        !forceRefresh &&
        !hasFilters &&
        lastMonthlyQuoteAsset.value === resolvedQuoteAsset &&
        Date.now() - lastMonthlyProfitsFetchTime.value < cacheTimeout &&
        monthlyProfitsData.value.length > 0
      ) {
        return;
      }

      monthlyProfitsLoading.value = true;
      try {
        const requestParams = {
          ...(params ?? {}),
          quote_asset: resolvedQuoteAsset,
        };
        const response = await apiService.profitAnalysis.getMonthlyProfits(requestParams);

        if (response.success && response.data) {
          monthlyProfitsData.value = Array.isArray(response.data)
            ? response.data
            : [];
          if (!hasFilters) {
            lastMonthlyProfitsFetchTime.value = Date.now();
            lastMonthlyQuoteAsset.value = resolvedQuoteAsset;
          }
        } else {
          console.warn('⚠️ 获取每月盈亏数据失败:', response);
        }
      } catch (error) {
        console.error('❌ 获取每月盈亏数据出错:', error);
      } finally {
        monthlyProfitsLoading.value = false;
      }
    };

    // 方法 - 获取交易对盈亏数据(直接从后端)
    const fetchSymbolProfits = async (
      params?: {
        start_date?: string;
        end_date?: string;
      },
      forceRefresh = false,
      quoteAsset: string = DEFAULT_QUOTE_ASSET,
    ): Promise<void> => {
      const resolvedQuoteAsset = normalizeQuoteAsset(quoteAsset);
      const hasFilters = Boolean(params && Object.keys(params).length > 0);

      if (
        !forceRefresh &&
        !hasFilters &&
        lastSymbolQuoteAsset.value === resolvedQuoteAsset &&
        Date.now() - lastSymbolProfitsFetchTime.value < cacheTimeout &&
        symbolProfitsData.value.length > 0
      ) {
        return;
      }

      symbolProfitsLoading.value = true;
      try {
        const requestParams = {
          ...(params ?? {}),
          quote_asset: resolvedQuoteAsset,
        };
        const response = await apiService.profitAnalysis.getSymbolProfits(requestParams);

        if (response.success && response.data) {
          symbolProfitsData.value = Array.isArray(response.data) ? response.data : [];
          if (!hasFilters) {
            // 只有在无筛选条件时才更新缓存时间
            lastSymbolProfitsFetchTime.value = Date.now();
            lastSymbolQuoteAsset.value = resolvedQuoteAsset;
          }
        } else {
          console.warn('⚠️ 获取交易对盈亏数据失败:', response);
        }
      } catch (error) {
        console.error('❌ 获取交易对盈亏数据出错:', error);
      } finally {
        symbolProfitsLoading.value = false;
      }
    };

    // 方法 - 获取交易对每日盈亏数据
    const fetchSymbolDailyProfits = async (
      params?: {
        start_date?: string;
        end_date?: string;
        symbol?: string;
      },
      forceRefresh = false,
      quoteAsset: string = DEFAULT_QUOTE_ASSET,
    ): Promise<void> => {
      const resolvedQuoteAsset = normalizeQuoteAsset(quoteAsset);
      const hasFilters = Boolean(params && Object.keys(params).length > 0);

      if (
        !forceRefresh &&
        !hasFilters &&
        lastSymbolDailyQuoteAsset.value === resolvedQuoteAsset &&
        Date.now() - lastSymbolDailyProfitsFetchTime.value < cacheTimeout &&
        symbolDailyProfitsData.value.length > 0
      ) {
        return;
      }

      symbolDailyProfitsLoading.value = true;
      try {
        const requestParams = {
          ...(params ?? {}),
          quote_asset: resolvedQuoteAsset,
        };
        const response = await apiService.profitAnalysis.getSymbolDailyProfits(
          requestParams,
        );

        if (response.success && response.data) {
          symbolDailyProfitsData.value = Array.isArray(response.data) ? response.data : [];
          if (!hasFilters) {
            // 只有在无筛选条件时才更新缓存时间
            lastSymbolDailyProfitsFetchTime.value = Date.now();
            lastSymbolDailyQuoteAsset.value = resolvedQuoteAsset;
          }
        } else {
          console.warn('⚠️ 获取交易对每日盈亏数据失败:', response);
        }
      } catch (error) {
        console.error('❌ 获取交易对每日盈亏数据出错:', error);
      } finally {
        symbolDailyProfitsLoading.value = false;
      }
    };

    // 方法 - 强制刷新数据
    const refreshData = async (quoteAsset: string = DEFAULT_QUOTE_ASSET): Promise<void> => {
      await Promise.all([
        fetchDailyProfits(undefined, true, quoteAsset),
        fetchMonthlyProfits(undefined, true, quoteAsset),
        fetchSymbolProfits(undefined, true, quoteAsset),
        fetchSymbolDailyProfits(undefined, true, quoteAsset),
      ]);
    };

    return {
      // 状态
      dailyProfitsData,
      monthlyProfitsData,
      symbolProfitsData,
      symbolDailyProfitsData,
      dailyProfitsLoading,
      monthlyProfitsLoading,
      symbolProfitsLoading,
      symbolDailyProfitsLoading,

      // 计算属性
      todayProfit,
      totalProfit,

      // 方法
      fetchDailyProfits,
      fetchMonthlyProfits,
      fetchSymbolProfits,
      fetchSymbolDailyProfits,
      refreshData,
    };
  },
  {
    persist: {
      key: 'profit-analysis-store',
      storage: localStorage,
      paths: [],
      afterHydrate: (context) => {
        const store = context.store as ReturnType<typeof useProfitAnalysisStore>;

        store.dailyProfitsData = [];
        store.monthlyProfitsData = [];
        store.symbolProfitsData = [];
        store.symbolDailyProfitsData = [];
        store.lastDailyProfitsFetchTime = 0;
        store.lastMonthlyProfitsFetchTime = 0;
        store.lastSymbolProfitsFetchTime = 0;
        store.lastSymbolDailyProfitsFetchTime = 0;

        store.$persist();
      },
    },
  },
);
