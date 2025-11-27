import { symbolApi } from './symbols';
import { timeframeConfigApi } from './timeframes';
import { profitAnalysisApi } from './profitAnalysis';
import type { SellOrderRecord } from './profitAnalysis.types';
import { toNumber } from './utils';

export const dashboardApi = {
  getStats: async (): Promise<{
    success: boolean;
    data: {
      active_configs: number;
      total_symbols: number;
      today_trades: number;
      total_profit: number;
    };
  }> => {
    try {
      const [symbolsResponse, configsResponse] = await Promise.all([
        symbolApi.getSymbols(),
        timeframeConfigApi.getAllConfigs(),
      ]);

      const activeConfigs = configsResponse.success
        ? configsResponse.configs.filter((c) => c.is_active === 1 || c.is_active === true).length
        : 0;
      const totalSymbols = symbolsResponse.success ? symbolsResponse.symbols.length : 0;

      return {
        success: true,
        data: {
          active_configs: activeConfigs,
          total_symbols: totalSymbols,
          today_trades: 0,
          total_profit: 0,
        },
      };
    } catch {
      return {
        success: false,
        data: {
          active_configs: 0,
          total_symbols: 0,
          today_trades: 0,
          total_profit: 0,
        },
      };
    }
  },

  getProfitStats: async (): Promise<{
    success: boolean;
    data: {
      totalOrders: number;
      profitOrders: number;
      totalProfit: number;
      todayProfit: number;
    };
  }> => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      const startDate = thirtyDaysAgo.toISOString().split('T')[0];

      const sellOrdersResponse = await profitAnalysisApi.getSellOrders({
        start_date: startDate,
        limit: 1000,
      });

      if (!sellOrdersResponse.success) {
        return {
          success: false,
          data: {
            totalOrders: 0,
            profitOrders: 0,
            totalProfit: 0,
            todayProfit: 0,
          },
        };
      }

      const orders: SellOrderRecord[] = Array.isArray(sellOrdersResponse.data)
        ? sellOrdersResponse.data
        : [];

      if (orders.length === 0) {
        return {
          success: false,
          data: {
            totalOrders: 0,
            profitOrders: 0,
            totalProfit: 0,
            todayProfit: 0,
          },
        };
      }

      const todayOrders = orders.filter(
        (order) => typeof order.time === 'string' && order.time.startsWith(today),
      );

      const profitOrders = orders.filter((order) => toNumber(order.profit) > 0);
      const totalProfit = orders.reduce((sum, order) => sum + toNumber(order.net_profit), 0);
      const todayProfit = todayOrders.reduce((sum, order) => sum + toNumber(order.net_profit), 0);

      return {
        success: true,
        data: {
          totalOrders: orders.length,
          profitOrders: profitOrders.length,
          totalProfit,
          todayProfit,
        },
      };
    } catch (error) {
      console.error('获取盈利统计失败:', error);
      return {
        success: false,
        data: {
          totalOrders: 0,
          profitOrders: 0,
          totalProfit: 0,
          todayProfit: 0,
        },
      };
    }
  },
};
