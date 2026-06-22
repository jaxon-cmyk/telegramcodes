from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.session import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class SignalStatus(str, Enum):
    parsed = "parsed"
    rejected = "rejected"
    needs_review = "needs_review"


class TradeIntentStatus(str, Enum):
    pending = "pending"
    blocked = "blocked"
    executed = "executed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.user)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    telegram_sessions: Mapped[list["TelegramSession"]] = relationship(back_populates="user")


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    used_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TelegramSession(Base):
    __tablename__ = "telegram_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    api_id_encrypted: Mapped[str] = mapped_column(Text)
    api_hash_encrypted: Mapped[str] = mapped_column(Text)
    phone_encrypted: Mapped[str] = mapped_column(Text)
    session_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending_verification")
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    user: Mapped[User] = relationship(back_populates="telegram_sessions")


class TelegramChannel(Base):
    __tablename__ = "telegram_channels"
    __table_args__ = (UniqueConstraint("user_id", "telegram_dialog_id", name="uq_user_dialog"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    telegram_session_id: Mapped[int] = mapped_column(ForeignKey("telegram_sessions.id"))
    telegram_dialog_id: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(50), default="channel")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class TelegramMessage(Base):
    __tablename__ = "telegram_messages"
    __table_args__ = (UniqueConstraint("user_id", "channel_id", "telegram_message_id", name="uq_user_channel_message"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("telegram_channels.id"), index=True)
    telegram_message_id: Mapped[str] = mapped_column(String(128))
    text: Mapped[str] = mapped_column(Text)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ParsedSignal(Base):
    __tablename__ = "parsed_signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("telegram_messages.id"), index=True)
    symbol: Mapped[str | None] = mapped_column(String(32), nullable=True)
    side: Mapped[str | None] = mapped_column(String(10), nullable=True)
    entry: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profits: Mapped[list] = mapped_column(JSON, default=list)
    lot: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    parser_source: Mapped[str] = mapped_column(String(50), default="rules")
    explanation: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[SignalStatus] = mapped_column(SAEnum(SignalStatus), default=SignalStatus.rejected)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class MT5Account(Base):
    __tablename__ = "mt5_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(100), default="cloud_bridge")
    provider_account_id: Mapped[str] = mapped_column(String(255))
    credentials_encrypted: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="connected")
    balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_health_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("telegram_channels.id"))
    mt5_account_id: Mapped[int] = mapped_column(ForeignKey("mt5_accounts.id"))
    name: Mapped[str] = mapped_column(String(255))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    allowed_symbols: Mapped[list] = mapped_column(JSON, default=list)
    max_lot: Mapped[float] = mapped_column(Float, default=0.1)
    max_risk_percent: Mapped[float] = mapped_column(Float, default=1.0)
    max_trades_per_day: Mapped[int] = mapped_column(Integer, default=3)
    require_stop_loss: Mapped[bool] = mapped_column(Boolean, default=True)
    duplicate_window_minutes: Mapped[int] = mapped_column(Integer, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class TradeIntent(Base):
    __tablename__ = "trade_intents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    parsed_signal_id: Mapped[int] = mapped_column(ForeignKey("parsed_signals.id"))
    automation_rule_id: Mapped[int | None] = mapped_column(ForeignKey("automation_rules.id"), nullable=True)
    mt5_account_id: Mapped[int | None] = mapped_column(ForeignKey("mt5_accounts.id"), nullable=True)
    status: Mapped[TradeIntentStatus] = mapped_column(SAEnum(TradeIntentStatus), default=TradeIntentStatus.pending)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_response: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ExecutedTrade(Base):
    __tablename__ = "executed_trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    trade_intent_id: Mapped[int] = mapped_column(ForeignKey("trade_intents.id"))
    mt5_account_id: Mapped[int] = mapped_column(ForeignKey("mt5_accounts.id"))
    provider_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    symbol: Mapped[str] = mapped_column(String(32))
    side: Mapped[str] = mapped_column(String(10))
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    entry: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profits: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="submitted")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
