import { authApi } from './auth';
import { configApi } from './config';
import { symbolApi } from './symbols';
import { timeframeConfigApi } from './timeframes';
import { tradingLogsApi } from './tradingLogs';
import { logsApi } from './logs';
import { dashboardApi } from './dashboard';
import { profitAnalysisApi } from './profitAnalysis';
import { binanceFilledOrdersApi } from './binanceFilledOrders';
import { api, handleApiError } from './http';

export const apiService = {
  auth: authApi,
  config: configApi,
  symbol: symbolApi,
  timeframeConfig: timeframeConfigApi,
  tradingLogs: tradingLogsApi,
  logs: logsApi,
  dashboard: dashboardApi,
  profitAnalysis: profitAnalysisApi,
  binanceFilledOrders: binanceFilledOrdersApi,
  handleError: handleApiError,
};

export {
  api,
  handleApiError,
};

export type { ApiResponse, NumberLike } from './http';
export type { SymbolSummary, SymbolUpdatePayload, SymbolSignalStrength } from './symbols';
export type {
  TimeframeConfigSummary,
  TimeframeConfigUpdatePayload,
  TimeframeBulkUpdatePayload,
} from './timeframes.types';
export type { SellOrderRecord, SellOrdersResponse } from './profitAnalysis.types';
export type {
  TradingLogsQueryParams,
  TradingLogsListResponse,
  TradingLogsStatsResponse,
  TradingLogSymbolsResponse,
  TradingLogResponse,
  LogsQueryParams,
} from './tradingLogs.types';
export type {
  LoginResponse,
  VerifyResponse,
  ChangePasswordResponse,
} from './auth';
export type { BinanceStatusData, BinanceValidationResult } from './config';
