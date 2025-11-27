import { api } from './http';
import type { ApiResponse, NumberLike } from './http';

export interface SymbolSummary {
  id: number;
  symbol: string;
  base_asset: string;
  quote_asset: string;
  is_active: boolean | number;
  description: string;
  current_price?: number | null;
  volume_24h?: number | null;
  price_change_24h?: number | null;


  signal_value?: NumberLike;
  signal_timestamp?: NumberLike;
  active_config_count?: number | null;
  inactive_config_count?: number | null;
  total_config_count?: number | null;
  created_at: string;
  updated_at: string;
}

export interface SymbolUpdatePayload {
  signal_threshold?: number;
  is_active?: boolean;
  operation_mode?: string;

  description?: string;
  max_fund?: number;

}

export interface SymbolSignalStrength {
  symbol: string;
  signal_value: number | null;
  timeframe: string;
  timestamp: string | null;
}

export const symbolApi = {
  getSymbols: async (): Promise<{
    success: boolean;
    message: string;
    symbols: SymbolSummary[];
  }> => {
    const response = await api.get('/api/v1/symbols/list');
    return response.data;
  },

  addSymbol: async (symbolConfig: {
    symbol: string;
    description?: string;
    max_fund?: number | null;
  }): Promise<ApiResponse> => {
    const response = await api.post('/api/v1/symbols/add', symbolConfig);
    return response.data;
  },

  updateSymbol: async (id: number, updates: SymbolUpdatePayload): Promise<ApiResponse> => {
    const response = await api.put(`/api/v1/symbols/${id}`, updates);
    return response.data;
  },

  deleteSymbol: async (id: number): Promise<ApiResponse> => {
    const response = await api.delete(`/api/v1/symbols/${id}`);
    return response.data;
  },

  refreshAll: async (): Promise<ApiResponse> => {
    const response = await api.post('/api/v1/symbols/refresh-all');
    return response.data;
  },

  getSignalStrength: async (
    symbol: string,
  ): Promise<{
    success: boolean;
    message: string;
    data: SymbolSignalStrength | null;
  }> => {
    const response = await api.get(`/api/v1/symbols/${symbol}/signal-strength`);
    return response.data;
  },
};
