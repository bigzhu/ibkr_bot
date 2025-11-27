import type { NumberLike, ApiResponse } from './http';

export interface LogsQueryParams {
  page?: number;
  limit?: number;
  symbol?: string;
  action_type?: string;
  result?: string;
  date_from?: string;
  date_to?: string;
}

export interface TradingLogsQueryParams {
  page?: number;
  limit?: number;
  symbol?: string;
  timeframe?: string;
  meets_conditions?: boolean | string;
  order_side?: string;
  sort_by?: string;
  sort_desc?: boolean | string;
  _t?: number | string;
}

export interface TradingLogsListResponse<T = Record<string, unknown>> {
  success: boolean;
  data?: T[];
  logs?: T[];
  total?: number;
  page?: number;
  limit?: number;
  message?: string;
  error?: string;
}

export interface TradingLogStatsData {
  total_signals?: number;
  error_count?: number;
  conditions_met?: number;
  [key: string]: unknown;
}

export interface TradingLogsStatsResponse {
  success: boolean;
  data?: TradingLogStatsData;
  message?: string;
  error?: string;
}

export interface TradingLogSymbolsResponse {
  success: boolean;
  data?: string[];
  message?: string;
  error?: string;
}

export interface TradingLogResponse {
  id: number;
  created_at: string;
  symbol: string;
  action_type: string;
  quantity?: NumberLike;
  price?: NumberLike;
  signal_value?: NumberLike;
  result: string;
  error_message?: string | null;
  side?: string | null;
  error?: string | null;
}

export type LogsApiResponse = ApiResponse<{
  logs: TradingLogResponse[];
  total: number;
  page: number;
  limit: number;
}>;

