import { api } from './http';
import type {
  TradingLogsQueryParams,
  TradingLogsListResponse,
  TradingLogsStatsResponse,
  TradingLogSymbolsResponse,
} from './tradingLogs.types';

export const tradingLogsApi = {
  list: async <T = Record<string, unknown>>(
    params: TradingLogsQueryParams = {},
  ): Promise<TradingLogsListResponse<T>> => {
    const response = await api.get('/api/v1/trading-logs/logs', { params });
    return response.data;
  },

  stats: async (
    params: Pick<TradingLogsQueryParams, 'symbol' | 'timeframe'> = {},
  ): Promise<TradingLogsStatsResponse> => {
    const response = await api.get('/api/v1/trading-logs/stats', { params });
    return response.data;
  },

  symbols: async (): Promise<TradingLogSymbolsResponse> => {
    const response = await api.get('/api/v1/trading-logs/symbols');
    return response.data;
  },
};
