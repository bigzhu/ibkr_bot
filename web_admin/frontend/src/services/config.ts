import { api } from './http';
import type { ApiResponse } from './http';

export interface BinanceStatusData {
  has_api_key: boolean;
  has_secret_key: boolean;
  is_configured: boolean;
  api_key: string;
  secret_key: string;
  environment_name: string;
}

export type BinanceValidationResult = Record<string, unknown>;

export const configApi = {
  getBinanceStatus: async (): Promise<{
    success: boolean;
    data: BinanceStatusData;
  }> => {
    const response = await api.get('/api/v1/config/binance/status');
    return response.data;
  },

  validateBinanceApi: async (config: {
    api_key: string;
    secret_key: string;
  }): Promise<{
    success: boolean;
    message: string;
    data?: BinanceValidationResult;
    error_code?: string;
    error_details?: string;
  }> => {
    const response = await api.post('/api/v1/config/binance/validate', config);
    return response.data;
  },

  saveBinanceConfig: async (config: {
    api_key: string;
    secret_key: string;
  }): Promise<{
    success: boolean;
    message: string;
    validation_result?: BinanceValidationResult;
  }> => {
    const response = await api.post('/api/v1/config/binance/save', config);
    return response.data;
  },

  getLogLevel: async (): Promise<{
    success: boolean;
    message: string;
    log_level: string;
  }> => {
    const response = await api.get('/api/v1/config/log-level');
    return response.data;
  },

  updateLogLevel: async (
    log_level: string,
  ): Promise<{
    success: boolean;
    message: string;
    log_level: string;
  }> => {
    const response = await api.put('/api/v1/config/log-level', { log_level });
    return response.data;
  },

  clearCache: async (): Promise<ApiResponse> => {
    const response = await api.post('/api/v1/config/cache/clear');
    return response.data;
  },
};
