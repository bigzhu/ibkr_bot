import type { ApiResponse, NumberLike } from './http';

export interface SellOrderRecord extends Record<string, unknown> {
  id?: number;
  order_no?: string;
  pair?: string;
  side?: string;
  time?: string | null;
  profit?: NumberLike;
  net_profit?: NumberLike;
  commission?: NumberLike;
}

export type SellOrdersResponse = ApiResponse<SellOrderRecord[]> & {
  total?: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
};

