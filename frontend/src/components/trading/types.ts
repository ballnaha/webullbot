export interface SignalData {
  symbol: string;
  price: number;
  rsi: number;
  sma_fast: number;
  sma_slow: number;
  sma_signal: string;
  rsi_signal: string;
  hybrid_signal: string;
  volume_ema_signal?: string;
}

export interface Trade {
  time: string;
  symbol: string;
  action: string;
  qty: number;
  price: number;
  status: string;
  timestamp?: string;
  total?: number;
  avgBuyPrice?: number;
  realizedPnL?: number;
  pnlPct?: number;
}

export interface Position {
  symbol: string;
  qty: number;
  avg_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct?: number;
}
