export type User = {
  id: number;
  email: string;
  role: "admin" | "user";
  is_active: boolean;
};

export type TelegramDialog = {
  dialog_id: string;
  title: string;
  kind: string;
  is_enabled: boolean;
  channel_id?: number;
};

export type Message = {
  id: number;
  channel_id: number;
  telegram_message_id: string;
  text: string;
  sender_name?: string;
  sent_at: string;
};

export type ParsedSignal = {
  id: number;
  message_id: number;
  symbol?: string;
  side?: string;
  entry?: number;
  stop_loss?: number;
  take_profits: number[];
  lot?: number;
  risk_percent?: number;
  confidence: number;
  parser_source: string;
  explanation: string;
  status: string;
  rejection_reason?: string;
};

export type MT5Account = {
  id: number;
  name: string;
  provider: string;
  provider_account_id: string;
  status: string;
  balance?: number;
  equity?: number;
};

export type AutomationRule = {
  id: number;
  name: string;
  channel_id: number;
  mt5_account_id: number;
  is_enabled: boolean;
  allowed_symbols: string[];
  max_lot: number;
  max_risk_percent: number;
  max_trades_per_day: number;
  require_stop_loss: boolean;
  duplicate_window_minutes: number;
};

export type TradeIntent = {
  id: number;
  parsed_signal_id: number;
  automation_rule_id?: number;
  mt5_account_id?: number;
  status: string;
  payload: Record<string, unknown>;
  block_reason?: string;
  provider_response: Record<string, unknown>;
  created_at: string;
};

export type ExecutedTrade = {
  id: number;
  trade_intent_id: number;
  mt5_account_id: number;
  provider_order_id?: string;
  symbol: string;
  side: string;
  volume?: number;
  status: string;
  created_at: string;
};
