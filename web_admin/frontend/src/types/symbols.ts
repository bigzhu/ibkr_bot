

export interface SymbolCacheEntry {
  id: number;
  symbol: string;
  signal_value: number | null;
  is_active: boolean;
  base_asset: string;
  quote_asset: string;
  current_price?: number | null;
  price_change_24h?: number | null;


  active_config_count?: number;
  inactive_config_count?: number;
  total_config_count?: number;
}

export interface ManagedSymbol extends SymbolCacheEntry {
  active_config_count: number;
  inactive_config_count: number;
  total_config_count: number;
  isToggling: boolean;

  isDeleting?: boolean;
}

export interface SymbolConfigStatsEntry {
  active: number;
  inactive: number;
  total: number;
}
