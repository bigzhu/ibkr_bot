import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { api } from 'src/services';
import { mergeById } from 'src/utils/data-merge';

export interface FilledOrder {
  id: number;
  time: string;
  date_utc: string;
  kline_time?: string | null;
  pair: string;
  side: string;
  order_type: string;
  status: string;
  order_price: number | string;
  order_amount: number | string;
  executed: number | string;
  average_price: number | string;
  trading_total: number | string;
  unmatched_qty: number | string;
  profit?: number | string;
  commission?: number | string;
  client_order_id?: string;
  [key: string]: unknown;
}

export interface FilledOrderStats {
  total_orders: number;
  unmatched_count: number;
  matched_count: number;
}

export interface FilledOrdersQuery {
  page: number;
  rowsPerPage: number;
  sortBy: string;
  descending: boolean;
  symbol?: string;
  side?: string;
}

interface FilledOrdersResponse {
  success: boolean;
  data: FilledOrder[];
  total?: number;
}

interface FilledOrdersStatsResponse {
  success: boolean;
  data: FilledOrderStats;
}

const DEFAULT_STATS: FilledOrderStats = {
  total_orders: 0,
  unmatched_count: 0,
  matched_count: 0,
};

const DEFAULT_PAGINATION: FilledOrdersQuery & { rowsNumber: number } = {
  page: 1,
  rowsPerPage: 20,
  sortBy: 'time',
  descending: true,
  symbol: undefined,
  side: undefined,
  rowsNumber: 0,
};

const CACHE_TIMEOUT = 60 * 1000; // 60 seconds

const getQueryKey = (query: FilledOrdersQuery): string => {
  return `${query.page}|${query.rowsPerPage}|${query.sortBy}|${query.descending}|${query.symbol || ''}|${query.side || ''}`;
};

const buildSorter = (sortBy: string, descending: boolean) => {
  return (a: FilledOrder, b: FilledOrder) => {
    const valueA = (a as Record<string, unknown>)[sortBy];
    const valueB = (b as Record<string, unknown>)[sortBy];

    const direction = descending ? -1 : 1;

    if (valueA === valueB) {
      return 0;
    }

    if (valueA === null || valueA === undefined) {
      return 1;
    }

    if (valueB === null || valueB === undefined) {
      return -1;
    }

    if (typeof valueA === 'number' && typeof valueB === 'number') {
      return valueA > valueB ? direction : -direction;
    }

    if (typeof valueA === 'string' && typeof valueB === 'string') {
      return valueA.localeCompare(valueB) * direction;
    }

    return 0;
  };
};

export const useFilledOrdersStore = defineStore(
  'filled-orders',
  () => {
    const orders = ref<FilledOrder[]>([]);
    const stats = ref<FilledOrderStats>({ ...DEFAULT_STATS });
    const pagination = ref({ ...DEFAULT_PAGINATION });
    const loadingOrders = ref(false);
    const loadingStats = ref(false);
    const lastFetchTime = ref<number>(0);
    const lastQueryKey = ref<string>('');

    const ordersForCurrentPage = computed(() => {
      const rowsPerPage = Math.max(1, Math.min(pagination.value.rowsPerPage, 1000));
      const start = (pagination.value.page - 1) * rowsPerPage;
      const end = start + rowsPerPage;
      return orders.value.slice(start, end);
    });

    const needsRefresh = (queryKey: string): boolean => {
      if (orders.value.length === 0) {
        return true;
      }
      return Date.now() - lastFetchTime.value > CACHE_TIMEOUT || queryKey !== lastQueryKey.value;
    };

    const fetchOrders = async (
      queryOverrides: Partial<FilledOrdersQuery> = {},
      forceRefresh = false,
    ): Promise<void> => {
      const nextQuery: FilledOrdersQuery = {
        page: queryOverrides.page ?? pagination.value.page,
        rowsPerPage: queryOverrides.rowsPerPage ?? pagination.value.rowsPerPage,
        sortBy: queryOverrides.sortBy ?? pagination.value.sortBy,
        descending: queryOverrides.descending ?? pagination.value.descending,
        symbol: 'symbol' in queryOverrides ? queryOverrides.symbol : pagination.value.symbol,
        side: 'side' in queryOverrides ? queryOverrides.side : pagination.value.side,
      };

      const clampedRowsPerPage = Math.max(1, Math.min(nextQuery.rowsPerPage, 1000));
      nextQuery.rowsPerPage = clampedRowsPerPage;

      const queryKey = getQueryKey(nextQuery);
      const isSameQuery = queryKey === lastQueryKey.value;
      const shouldForce = forceRefresh || !isSameQuery;

      if (!shouldForce && !needsRefresh(queryKey)) {
        pagination.value = { ...pagination.value, ...nextQuery };
        return;
      }

      loadingOrders.value = true;
      try {
        const params: Record<string, unknown> = {
          page: nextQuery.page,
          page_size: nextQuery.rowsPerPage,
          order_by: nextQuery.sortBy,
          order_direction: nextQuery.descending ? 'DESC' : 'ASC',
        };

        if (nextQuery.symbol) {
          params.symbol = nextQuery.symbol;
        }

        if (nextQuery.side) {
          params.side = nextQuery.side;
        }

        const response = await api.get<FilledOrdersResponse>('/api/v1/filled-orders/', {
          params,
        });

        const payload = response.data;

        if (payload?.success && Array.isArray(payload.data)) {
          const incoming = payload.data;
          const replaceExisting = !isSameQuery;
          const incomingIds = new Set(incoming.map((item) => item.id));
          const base = replaceExisting
            ? []
            : orders.value.filter((order) => !incomingIds.has(order.id));

          orders.value = mergeById(base, incoming, {
            sort: buildSorter(nextQuery.sortBy, nextQuery.descending),
            maxItems: Math.max(nextQuery.rowsPerPage * nextQuery.page, nextQuery.rowsPerPage),
            pruneMissing: replaceExisting,
          });

          pagination.value = {
            ...nextQuery,
            rowsNumber: payload.total ?? orders.value.length,
          };

          lastFetchTime.value = Date.now();
          lastQueryKey.value = queryKey;
        }
      } catch (error) {
        console.error('❌ 获取撮合订单失败:', error);
        throw error;
      } finally {
        loadingOrders.value = false;
      }
    };

    const fetchStats = async (forceRefresh = false): Promise<void> => {
      if (!forceRefresh && stats.value.total_orders > 0) {
        return;
      }

      loadingStats.value = true;
      try {
        const response = await api.get<FilledOrdersStatsResponse>('/api/v1/filled-orders/stats');
        const payload = response.data;

        if (payload?.success && payload.data) {
          stats.value = payload.data;
        }
      } catch (error) {
        console.error('❌ 获取撮合订单统计失败:', error);
        throw error;
      } finally {
        loadingStats.value = false;
      }
    };

    return {
      orders,
      stats,
      pagination,
      loadingOrders,
      loadingStats,
      ordersForCurrentPage,
      fetchOrders,
      fetchStats,
    };
  },
  {
    persist: {
      key: 'filled-orders-store',
      storage: localStorage,
      paths: ['pagination'],
      afterHydrate: (context) => {
        const store = context.store as ReturnType<typeof useFilledOrdersStore>;

        store.orders = [];
        store.stats = { ...DEFAULT_STATS };
        store.lastFetchTime = 0;
        store.lastQueryKey = '';

        store.$persist();
      },
    },
  },
);
