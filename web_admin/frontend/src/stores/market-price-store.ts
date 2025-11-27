import { defineStore } from 'pinia';
import { ref } from 'vue';

const DEFAULT_TTL_MS = 60 * 1000; // 1 minute

interface MarketPriceEntry {
  value: string;
  updatedAt: number;
}

const normaliseSymbol = (symbol: string): string => symbol.trim().toUpperCase();

export const useMarketPriceStore = defineStore(
  'market-price-store',
  () => {
    const prices = ref<Record<string, MarketPriceEntry>>({});
    const loading = ref<Record<string, boolean>>({});

    const setPrice = (symbol: string, value: string | null): void => {
      const key = normaliseSymbol(symbol);
      if (!key) {
        return;
      }
      prices.value = {
        ...prices.value,
        [key]: {
          value: value ?? '0',
          updatedAt: Date.now(),
        },
      };
    };

    const setLoading = (symbol: string, state: boolean): void => {
      const key = normaliseSymbol(symbol);
      if (!key) {
        return;
      }
      loading.value = {
        ...loading.value,
        [key]: state,
      };
    };

    const isLoading = (symbol: string): boolean => {
      const key = normaliseSymbol(symbol);
      return loading.value[key] === true;
    };

    const getPrice = (symbol: string): string | null => {
      const key = normaliseSymbol(symbol);
      const entry = prices.value[key];
      return entry ? entry.value : null;
    };

    const isFresh = (symbol: string, ttlMs: number = DEFAULT_TTL_MS): boolean => {
      const key = normaliseSymbol(symbol);
      const entry = prices.value[key];
      if (!entry) {
        return false;
      }
      return Date.now() - entry.updatedAt <= ttlMs;
    };

    return {
      prices,
      loading,
      setPrice,
      setLoading,
      isLoading,
      getPrice,
      isFresh,
    };
  },
  {
    persist: {
      key: 'market-price-store',
      storage: localStorage,
      paths: ['prices'],
    },
  },
);
