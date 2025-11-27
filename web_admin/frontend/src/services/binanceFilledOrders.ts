import { api } from './http';

export interface MarketPriceResponse {
  success: boolean;
  symbol: string;
  market_price: string | null;
  message?: string;
}

export const binanceFilledOrdersApi = {
  async getMarketPrice(symbol: string): Promise<MarketPriceResponse> {
    const response = await api.get<MarketPriceResponse>(
      '/api/v1/binance-filled-orders/market-price',
      {
        params: { symbol },
        timeout: 15000,
      },
    );

    return response.data;
  },
};
