export interface TimeframeConfigSummary {
  id: number;
  trading_symbol: string;
  kline_timeframe: string;
  demark_buy: number;
  demark_sell: number;
  daily_max_percentage: number;

  minimum_profit_percentage: number;
  monitor_delay: number;
  oper_mode: string;
  is_active: boolean | number;
  created_at: string;
  updated_at: string;


}

export interface TimeframeConfigUpdatePayload {
  demark_buy?: number;
  demark_sell?: number;
  daily_max_percentage?: number;

  minimum_profit_percentage?: number;
  monitor_delay?: number;
  oper_mode?: string;
  is_active?: boolean;


}

export interface TimeframeBulkUpdatePayload {
  demark_buy?: number;
  demark_sell?: number;
  minimum_profit_percentage?: number;
  monitor_delay?: number;
}
