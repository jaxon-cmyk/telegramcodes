from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(ORMModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime


class UserAdminUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8)


class UserAdminCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "user"
    is_active: bool = True


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    invite_code: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class InviteCreate(BaseModel):
    email: EmailStr | None = None
    expires_at: datetime | None = None


class InviteRead(ORMModel):
    id: int
    code: str
    email: EmailStr | None
    used_by_user_id: int | None
    expires_at: datetime | None
    used_at: datetime | None
    created_at: datetime


class TelegramConnectRequest(BaseModel):
    api_id: str
    api_hash: str
    phone: str


class TelegramVerifyRequest(BaseModel):
    session_id: int
    code: str
    password: str | None = None


class TelegramDialogRead(BaseModel):
    dialog_id: str
    title: str
    kind: str
    is_enabled: bool = False


class ChannelEnableRequest(BaseModel):
    enabled: bool = True


class ChannelRead(ORMModel):
    id: int
    telegram_dialog_id: str
    title: str
    kind: str
    is_enabled: bool
    last_message_at: datetime | None
    last_sync_at: datetime | None


class MessageRead(ORMModel):
    id: int
    channel_id: int
    telegram_message_id: str
    text: str
    sender_name: str | None
    sent_at: datetime


class SearchRequest(BaseModel):
    query: str
    channel_id: int | None = None


class ParsedSignalRead(ORMModel):
    id: int
    message_id: int
    symbol: str | None
    side: str | None
    entry: float | None
    stop_loss: float | None
    take_profits: list[Any]
    lot: float | None
    risk_percent: float | None
    confidence: float
    parser_source: str
    explanation: str
    status: str
    rejection_reason: str | None
    created_at: datetime


class MT5AccountConnect(BaseModel):
    name: str
    provider: str = "cloud_bridge"
    provider_account_id: str
    credentials: dict[str, Any]


class MT5AccountRead(ORMModel):
    id: int
    name: str
    provider: str
    provider_account_id: str
    status: str
    balance: float | None
    equity: float | None
    last_health_check_at: datetime | None
    created_at: datetime


class AutomationRuleCreate(BaseModel):
    name: str
    channel_id: int
    mt5_account_id: int
    is_enabled: bool = True
    allowed_symbols: list[str] = Field(default_factory=list)
    max_lot: float = 0.1
    max_risk_percent: float = 1.0
    max_trades_per_day: int = 3
    require_stop_loss: bool = True
    duplicate_window_minutes: int = 60


class AutomationRulePatch(BaseModel):
    name: str | None = None
    is_enabled: bool | None = None
    allowed_symbols: list[str] | None = None
    max_lot: float | None = None
    max_risk_percent: float | None = None
    max_trades_per_day: int | None = None
    require_stop_loss: bool | None = None
    duplicate_window_minutes: int | None = None


class AutomationRuleRead(ORMModel):
    id: int
    name: str
    channel_id: int
    mt5_account_id: int
    is_enabled: bool
    allowed_symbols: list[str]
    max_lot: float
    max_risk_percent: float
    max_trades_per_day: int
    require_stop_loss: bool
    duplicate_window_minutes: int


class TradeIntentRead(ORMModel):
    id: int
    parsed_signal_id: int
    automation_rule_id: int | None
    mt5_account_id: int | None
    status: str
    payload: dict[str, Any]
    block_reason: str | None
    provider_response: dict[str, Any]
    created_at: datetime


class ExecutedTradeRead(ORMModel):
    id: int
    trade_intent_id: int
    mt5_account_id: int
    provider_order_id: str | None
    symbol: str
    side: str
    volume: float | None
    entry: float | None
    stop_loss: float | None
    take_profits: list[Any]
    status: str
    created_at: datetime


class AuditLogRead(ORMModel):
    id: int
    user_id: int | None
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: str | None
    details: dict[str, Any]
    created_at: datetime
