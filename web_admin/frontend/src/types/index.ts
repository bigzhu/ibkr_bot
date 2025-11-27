// 基础类型定义
export interface LogEntry {
  id: number;
  symbol: string;
  action_type: string;
  result: string;
  created_at: string;
  quantity?: number;
  price?: number;
  signal_value?: number;
  error_message?: string | null;
}

export interface SymbolConfig {
  id: number;
  symbol: string;
  timeframe: string;
  signal_value: number;
  is_active: boolean;
  last_trade?: {
    timestamp: string;
    side: string;
  } | null;
  isToggling?: boolean;
}

export type TableFieldResolver<Row extends Record<string, unknown>, Value = unknown> =
  | keyof Row
  | ((row: Row) => Value);

export interface TableColumn<
  Row extends Record<string, unknown> = Record<string, unknown>,
  Value = unknown,
> {
  name: string;
  label: string;
  field: TableFieldResolver<Row, Value>;
  align?: 'left' | 'right' | 'center';
  sortable?: boolean;
  required?: boolean;
  sort?: (a: Value, b: Value, rowA: Row, rowB: Row) => number;
  sortOrder?: 'ad' | 'da';
  format?: (val: Value, row: Row) => string | number | boolean | null | undefined;
  style?: string | ((row: Row) => string);
  classes?: string | ((row: Row) => string);
  headerStyle?: string;
  headerClasses?: string;
}

export interface FilterFunction {
  (val: string, update: (fn: () => void) => void): void;
}
