import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiService } from 'src/services';
import { mergeById } from 'src/utils/data-merge';

export interface SellOrder {
  id: number;
  order_no: string;
  pair: string;
  side: string;
  time: string;
  client_order_id?: string;
  order_amount?: number | string;
  average_price?: number | string;
  trading_total?: number | string;
  profit?: number | string;
  commission?: number | string;
  [key: string]: unknown;
}

export interface SellOrdersFilters {
  symbol?: string;
  orderNo?: string;
  startDate?: string;
  endDate?: string;
  quoteAsset?: string;
}

export interface SellOrdersRequest {
  page: number;
  rowsPerPage: number;
  filters: SellOrdersFilters;
}

const DEFAULT_PAGINATION = {
  page: 1,
  rowsPerPage: 0,
  rowsPerPageOptions: [0, 10, 20, 50, 100],
  rowsNumber: 0,
};

const CACHE_TIMEOUT = 60 * 1000; // 60 seconds

const getQueryKey = (request: SellOrdersRequest): string => {
  const { page, rowsPerPage, filters } = request;
  return [
    page,
    rowsPerPage,
    filters.symbol ?? '',
    filters.orderNo ?? '',
    filters.startDate ?? '',
    filters.endDate ?? '',
    filters.quoteAsset ?? '',
  ].join('|');
};

const needsRefresh = (lastQueryKey: string, currentQueryKey: string, lastFetchTime: number): boolean => {
  if (!lastQueryKey) {
    return true;
  }
  if (lastQueryKey !== currentQueryKey) {
    return true;
  }
  return Date.now() - lastFetchTime > CACHE_TIMEOUT;
};

export const useSellOrdersStore = defineStore(
  'sell-orders',
  () => {
    const orders = ref<SellOrder[]>([]);
    const pagination = ref({ ...DEFAULT_PAGINATION });
    const loading = ref(false);
    const lastFetchTime = ref<number>(0);
    const lastQueryKey = ref<string>('');
    const lastFilters = ref<SellOrdersFilters>({});

    const fetchSellOrders = async (
      request: SellOrdersRequest,
      forceRefresh = false,
    ): Promise<void> => {
      const queryKey = getQueryKey(request);
      const shouldFetch =
        forceRefresh || orders.value.length === 0 || needsRefresh(lastQueryKey.value, queryKey, lastFetchTime.value);

      if (!shouldFetch) {
        pagination.value = {
          ...pagination.value,
          page: request.page,
          rowsPerPage: request.rowsPerPage,
        };
        return;
      }

      loading.value = true;
      try {
        const resolvedLimit = request.rowsPerPage > 0 ? request.rowsPerPage : undefined;

        const payload = await apiService.profitAnalysis.getSellOrders({
          page: request.page,
          limit: resolvedLimit,
          symbol: request.filters.symbol,
          order_no: request.filters.orderNo,
          start_date: request.filters.startDate,
          end_date: request.filters.endDate,
          quote_asset: request.filters.quoteAsset,
        });

        if (payload?.success && Array.isArray(payload.data)) {
          if (forceRefresh) {
            // 强制刷新时直接替换数据
            orders.value = payload.data;
          } else {
            // 正常更新时合并数据
            orders.value = mergeById(orders.value, payload.data, {
              pruneMissing: true,
              maxItems: resolvedLimit,
            });
          }

          pagination.value = {
            ...pagination.value,
            page: request.page,
            rowsPerPage: request.rowsPerPage,
            rowsNumber: payload.total ?? pagination.value.rowsNumber,
          };

          lastFetchTime.value = Date.now();
          lastQueryKey.value = queryKey;
          lastFilters.value = { ...request.filters };
        }
      } catch (error) {
        console.error('❌ 获取盈亏清单失败:', error);
        throw error;
      } finally {
        loading.value = false;
      }
    };

    const refresh = async (): Promise<void> => {
      await fetchSellOrders(
        {
          page: pagination.value.page,
          rowsPerPage: pagination.value.rowsPerPage,
          filters: lastFilters.value,
        },
        true,
      );
    };

    return {
      orders,
      pagination,
      loading,
      lastFetchTime,
      lastQueryKey,
      lastFilters,
      fetchSellOrders,
      refresh,
    };
  },
  {
    persist: {
      key: 'sell-orders-store',
      storage: localStorage,
      paths: ['pagination', 'lastFilters'],
      afterHydrate: (context) => {
        const store = context.store as ReturnType<typeof useSellOrdersStore>;

        store.orders = [];
        store.lastFetchTime = 0;
        store.lastQueryKey = '';

        store.$persist();
      },
    },
  },
);
