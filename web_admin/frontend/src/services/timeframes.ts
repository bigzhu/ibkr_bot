import { api } from './http';
import type {
  TimeframeConfigSummary,
  TimeframeConfigUpdatePayload,
  TimeframeBulkUpdatePayload,
} from './timeframes.types';

export const timeframeConfigApi = {
  getAllConfigs: async (): Promise<{
    success: boolean;
    message: string;
    configs: TimeframeConfigSummary[];
  }> => {
    const response = await api.get('/api/v1/timeframe-configs/');
    return response.data;
  },

  getConfigsBySymbol: async (
    symbol: string,
  ): Promise<{
    success: boolean;
    message: string;
    configs: TimeframeConfigSummary[];
  }> => {
    const response = await api.get(`/api/v1/timeframe-configs/${symbol}`);
    return response.data;
  },

  updateConfig: async (
    configId: number,
    updates: TimeframeConfigUpdatePayload,
  ): Promise<{ success: boolean; message: string } & Record<string, unknown>> => {
    const response = await api.put(`/api/v1/timeframe-configs/${configId}`, updates);
    return response.data;
  },

  bulkUpdateMinimumProfit: async (
    payload: TimeframeBulkUpdatePayload,
  ): Promise<{
    success: boolean;
    message: string;
    updated_count: number;
  }> => {
    const response = await api.post(
      '/api/v1/timeframe-configs/minimum-profit/bulk-update',
      payload,
    );
    return response.data;
  },

  deleteConfig: async (configId: number): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/api/v1/timeframe-configs/${configId}`);
    return response.data;
  },
};
