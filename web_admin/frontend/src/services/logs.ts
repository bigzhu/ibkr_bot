import { api } from './http';
import type { LogsQueryParams, TradingLogResponse, LogsApiResponse } from './tradingLogs.types';

export const logsApi = {
  getLogs: async (params?: LogsQueryParams): Promise<LogsApiResponse> => {
    const response = await api.get('/api/v1/logs', { params });
    return response.data;
  },

  getLogStats: async (params?: {
    date_from?: string;
    date_to?: string;
  }): Promise<
    {
      success: boolean;
      message?: string;
      data?: {
        total_logs: number;
        success_count: number;
        error_count: number;
        success_rate: number;
      };
    }
  > => {
    const response = await api.get('/api/v1/logs/stats', { params });
    return response.data;
  },

  exportLogs: async (params?: {
    format?: 'csv' | 'xlsx';
    date_from?: string;
    date_to?: string;
    symbol?: string;
  }): Promise<Blob> => {
    const response = await api.get('/api/v1/logs/export', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },

  clearLogs: async (params?: {
    date_before?: string;
    keep_recent_days?: number;
  }): Promise<{
    success: boolean;
    message?: string;
    data?: { deleted_count: number };
  }> => {
    const response = await api.post('/api/v1/logs/clear', params);
    return response.data;
  },
};

export const isTradingLogResponse = (log: unknown): log is TradingLogResponse => {
  if (!log || typeof log !== 'object') {
    return false;
  }
  const candidate = log as Record<string, unknown>;
  return (
    typeof candidate.id === 'number' &&
    typeof candidate.created_at === 'string' &&
    typeof candidate.symbol === 'string'
  );
};
