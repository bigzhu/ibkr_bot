import { defineStore } from 'pinia';
import { ref } from 'vue';
import { api } from 'src/services';
import type { AxiosError } from 'axios';
import { mergeById } from 'src/utils/data-merge';

export interface MinSellCondition {
  id: string;
  pair: string;
  timeframe: string;
  holding_qty?: number | string;
  market_price?: number | string;
  cost?: number | string;
  balance?: number | string;
  quote_balance?: number | string;
  average_price?: number | string;
  min_buy_price?: number | string;
  sell_price?: number | string;
  quantity?: number | string;
  [key: string]: unknown;
}

interface MinSellConditionsResponse {
  success: boolean;
  data: Array<Record<string, unknown>>;
}

const CACHE_TIMEOUT = 30 * 1000; // 30 seconds

const normaliseConditions = (rows: Array<Record<string, unknown>>): MinSellCondition[] => {
  const result: MinSellCondition[] = [];

  for (const row of rows) {
    const rawPair = row.pair ?? row.symbol;
    const rawTimeframe = row.timeframe ?? row.kline_timeframe;
    let pair: string | null = null;
    let timeframe: string | null = null;

    if (typeof rawPair === 'string' && rawPair.trim() !== '') {
      pair = rawPair;
    } else if (typeof rawPair === 'number' || typeof rawPair === 'bigint') {
      pair = rawPair.toString();
    }

    if (typeof rawTimeframe === 'string' && rawTimeframe.trim() !== '') {
      timeframe = rawTimeframe;
    }

    if (!pair || !timeframe) {
      continue;
    }

    result.push({
      ...row,
      id: `${pair}-${timeframe}`,
      pair,
      timeframe,
    } as MinSellCondition);
  }

  return result;
};

export const useMinSellConditionsStore = defineStore(
  'min-sell-conditions',
  () => {
    const conditions = ref<MinSellCondition[]>([]);
    const loading = ref(false);
    const lastFetchTime = ref<number>(0);

    const fetchConditions = async (forceRefresh = false): Promise<void> => {
      if (!forceRefresh && conditions.value.length > 0) {
        if (Date.now() - lastFetchTime.value < CACHE_TIMEOUT) {
          return;
        }
      }

      loading.value = true;
      try {
        const response = await api.get<MinSellConditionsResponse>(
          '/api/v1/binance-filled-orders/min-sell-conditions',
          {
            timeout: 25000,
            params: {
              _t: Date.now(),
            },
          },
        );

        const payload = response.data;

        if (payload?.success && Array.isArray(payload.data)) {
          const normalised = normaliseConditions(payload.data);
          conditions.value = mergeById(forceRefresh ? [] : conditions.value, normalised, {
            pruneMissing: true,
          });
          lastFetchTime.value = Date.now();
        }
      } catch (error) {
        console.error('❌ 获取最低SELL条件失败:', error);
        if ((error as AxiosError)?.code === 'ECONNABORTED') {
          throw new Error('请求超时,请稍后重试');
        }
        throw error;
      } finally {
        loading.value = false;
      }
    };

    const refresh = async (): Promise<void> => {
      await fetchConditions(true);
    };

    return {
      conditions,
      loading,
      lastFetchTime,
      fetchConditions,
      refresh,
    };
  },
  {
    persist: {
      key: 'min-sell-conditions-store',
      storage: localStorage,
      paths: ['conditions', 'lastFetchTime'],
    },
  },
);
