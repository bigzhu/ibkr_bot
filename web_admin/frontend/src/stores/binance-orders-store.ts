import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api } from 'src/services';
import { mergeById } from 'src/utils/data-merge';

export interface BinanceOrder {
  id: number;
  order_id: string;
  pair: string; // 统一使用pair字段名
  side: 'BUY' | 'SELL';
  type: string;
  order_amount: string; // 订单数量
  order_price: string; // 订单价格
  average_price: string; // 平均成交价格
  trading_total: string; // 成交总额
  commission: string;
  commission_asset: string;
  time: string;
  is_buyer: boolean;
  is_maker: boolean;
  quote_qty: string;
}

export interface OrderStats {
  total_orders: number;
  buy_orders: number;
  sell_orders: number;
  total_volume: number;
}

const DEFAULT_STATS: OrderStats = {
  total_orders: 0,
  buy_orders: 0,
  sell_orders: 0,
  total_volume: 0,
};

export const useBinanceOrdersStore = defineStore(
  'binance-orders',
  () => {
    // 状态
    const orders = ref<BinanceOrder[]>([]);
    const stats = ref<OrderStats>({ ...DEFAULT_STATS });
    const loading = ref(false);
    const lastFetchTime = ref<number>(0);
    const cacheTimeout = 3 * 60 * 1000; // 3分钟缓存

    // 计算属性 - 最近5条订单
    const recentOrders = computed((): BinanceOrder[] => {
      return [...orders.value]
        .sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime())
        .slice(0, 5);
    });

    // 计算属性 - 今日订单数量
    const todayOrdersCount = computed((): number => {
      const today = new Date().toISOString().split('T')[0];
      return orders.value.filter((order) => {
        const orderDate = new Date(order.time).toISOString().split('T')[0];
        return orderDate === today;
      }).length;
    });

    // 方法 - 检查是否需要刷新数据
    const needsRefresh = (): boolean => {
      return Date.now() - lastFetchTime.value > cacheTimeout || orders.value.length === 0;
    };

    // 方法 - 获取订单数据
    const fetchOrders = async (forceRefresh = false): Promise<void> => {
      if (!forceRefresh && !needsRefresh()) {
        return;
      }

      loading.value = true;
      try {
        // 仅获取近期少量订单,满足仪表板展示
        const response = await api.get('/api/v1/binance-filled-orders/', {
          params: { page: 1, limit: 50 },
        });

        if (response.data?.success && response.data?.data) {
          const incoming = response.data.data as BinanceOrder[];
          const base = forceRefresh ? [] : orders.value;
          orders.value = mergeById(base, incoming, {
            sort: (a, b) => new Date(b.time).getTime() - new Date(a.time).getTime(),
            maxItems: 200,
          });
          lastFetchTime.value = Date.now();
        } else {
          console.warn('⚠️ 获取币安成交订单数据失败:', response.data);
        }
      } catch (error) {
        console.error('❌ 获取币安成交订单数据出错:', error);
      } finally {
        loading.value = false;
      }
    };

    // 方法 - 获取统计数据
    const fetchStats = async (): Promise<void> => {
      try {
        const response = await api.get('/api/v1/binance-filled-orders/stats');

        if (response.data?.success) {
          stats.value = response.data.data || stats.value;
        } else {
          console.warn('⚠️ 获取币安订单统计失败:', response.data);
        }
      } catch (error) {
        console.error('❌ 获取币安订单统计出错:', error);
      }
    };

    // 方法 - 强制刷新数据
    const refreshData = async (): Promise<void> => {
      await Promise.all([fetchOrders(true), fetchStats()]);
    };

    return {
      // 状态
      orders,
      stats,
      loading,

      // 计算属性
      recentOrders,
      todayOrdersCount,

      // 方法
      fetchOrders,
      fetchStats,
      refreshData,
      needsRefresh,
    };
  },
  {
    persist: {
      key: 'binance-orders-store',
      storage: localStorage,
      paths: [],
      afterHydrate: (context) => {
        const store = context.store as ReturnType<typeof useBinanceOrdersStore>;

        store.orders = [];
        store.stats = { ...DEFAULT_STATS };
        store.lastFetchTime = 0;

        store.$persist();
      },
    },
  },
);
