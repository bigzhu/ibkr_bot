import { api } from './http';
import type { ApiResponse } from './http';
import type { SellOrdersResponse } from './profitAnalysis.types';
import { toNumber } from './utils';

const normalizeQuoteAsset = (quoteAsset?: string): string | undefined => {
  if (!quoteAsset) {
    return undefined;
  }
  return quoteAsset.toUpperCase();
};

export const profitAnalysisApi = {
  getSellOrders: async (params?: {
    start_date?: string;
    end_date?: string;
    symbol?: string;
    order_no?: string;
    quote_asset?: string;
    page?: number;
    limit?: number;
  }): Promise<SellOrdersResponse> => {
    const normalizedParams = params ? { ...params } : {};
    if (normalizedParams.quote_asset) {
      normalizedParams.quote_asset = normalizeQuoteAsset(normalizedParams.quote_asset);
    }
    const response = await api.get('/api/profit-analysis/sell-orders', {
      params: normalizedParams,
    });
    return response.data;
  },

  getDailyProfits: async (params?: {
    start_date?: string;
    end_date?: string;
    symbol?: string;
    quote_asset?: string;
  }): Promise<
    ApiResponse<
      Array<{
        date: string;
        order_count: number;
        total_profit: number;
        total_commission: number;
        net_profit: number;
      }>
    >
  > => {
    const normalizedParams = params ? { ...params } : {};
    if (normalizedParams.quote_asset) {
      normalizedParams.quote_asset = normalizeQuoteAsset(normalizedParams.quote_asset);
    }
    const response = await api.get('/api/profit-analysis/daily-profits', {
      params: normalizedParams,
    });
    return response.data;
  },

  getMonthlyProfits: async (params?: {
    start_date?: string;
    end_date?: string;
    symbol?: string;
    quote_asset?: string;
  }): Promise<
    ApiResponse<
      Array<{
        month: string;
        order_count: number;
        total_profit: number;
        total_commission: number;
        net_profit: number;
      }>
    >
  > => {
    const normalizedParams = params ? { ...params } : {};
    if (normalizedParams.quote_asset) {
      normalizedParams.quote_asset = normalizeQuoteAsset(normalizedParams.quote_asset);
    }
    const response = await api.get('/api/profit-analysis/monthly-profits', {
      params: normalizedParams,
    });
    return response.data;
  },

  getSymbolProfits: async (params?: {
    start_date?: string;
    end_date?: string;
    quote_asset?: string;
  }): Promise<
    ApiResponse<
      Array<{
        symbol: string;
        order_count: number;
        total_profit: number;
        total_commission: number;
        net_profit: number;
      }>
    >
  > => {
    const normalizedParams = params ? { ...params } : {};
    if (normalizedParams.quote_asset) {
      normalizedParams.quote_asset = normalizeQuoteAsset(normalizedParams.quote_asset);
    }
    const response = await api.get('/api/profit-analysis/symbol-profits', {
      params: normalizedParams,
    });
    return response.data;
  },

  getSymbolDailyProfits: async (params?: {
    start_date?: string;
    end_date?: string;
    symbol?: string;
    quote_asset?: string;
  }): Promise<
    ApiResponse<
      Array<{
        symbol: string;
        date: string;
        order_count: number;
        total_profit: number;
        total_commission: number;
        net_profit: number;
      }>
    >
  > => {
    const normalizedParams = params ? { ...params } : {};
    if (normalizedParams.quote_asset) {
      normalizedParams.quote_asset = normalizeQuoteAsset(normalizedParams.quote_asset);
    }
    const response = await api.get('/api/profit-analysis/symbol-daily-profits', {
      params: normalizedParams,
    });
    return response.data;
  },

  // helper reused by dashboard
  toNumber,
};
