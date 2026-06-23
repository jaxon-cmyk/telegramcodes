from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AutomationRule, ParsedSignal, TradeIntent, TradeIntentStatus
from app.models.entities import now_utc


class AutomationEngine:
    def evaluate(self, db: Session, signal: ParsedSignal, rule: AutomationRule) -> TradeIntent:
        reasons = []
        symbol = (signal.symbol or "").upper()
        allowed = [item.upper() for item in (rule.allowed_symbols or [])]

        if signal.status.value != "parsed":
            reasons.append("Signal did not pass parser validation")
        if not signal.symbol or not signal.side:
            reasons.append("Signal is missing symbol or side")
        if not rule.is_enabled:
            reasons.append("Automation rule is disabled")
        if allowed and symbol not in allowed:
            reasons.append(f"{symbol} is not in the allowed symbol list")
        if rule.require_stop_loss and not signal.stop_loss:
            reasons.append("Stop loss is required")
        if not signal.lot:
            reasons.append("Signal lot is required")
        if signal.lot and signal.lot > rule.max_lot:
            reasons.append("Signal lot exceeds max lot")
        if signal.risk_percent and signal.risk_percent > rule.max_risk_percent:
            reasons.append("Signal risk exceeds max risk percent")

        start_of_day = now_utc().replace(hour=0, minute=0, second=0, microsecond=0)
        trades_today = db.scalar(
            select(func.count(TradeIntent.id)).where(
                TradeIntent.user_id == signal.user_id,
                TradeIntent.automation_rule_id == rule.id,
                TradeIntent.created_at >= start_of_day,
                TradeIntent.status.in_([TradeIntentStatus.executed, TradeIntentStatus.pending]),
            )
        )
        if trades_today >= rule.max_trades_per_day:
            reasons.append("Max trades per day reached")

        duplicate_since = now_utc() - timedelta(minutes=rule.duplicate_window_minutes)
        duplicate = db.scalar(
            select(TradeIntent).where(
                TradeIntent.user_id == signal.user_id,
                TradeIntent.automation_rule_id == rule.id,
                TradeIntent.created_at >= duplicate_since,
                TradeIntent.payload["symbol"].as_string() == symbol,
                TradeIntent.payload["side"].as_string() == (signal.side or ""),
            )
        )
        if duplicate:
            reasons.append("Duplicate signal within prevention window")

        payload = {
            "symbol": symbol,
            "side": signal.side,
            "entry": signal.entry,
            "stop_loss": signal.stop_loss,
            "take_profits": signal.take_profits,
            "volume": signal.lot,
            "risk_percent": signal.risk_percent,
        }
        return TradeIntent(
            user_id=signal.user_id,
            parsed_signal_id=signal.id,
            automation_rule_id=rule.id,
            mt5_account_id=rule.mt5_account_id,
            status=TradeIntentStatus.blocked if reasons else TradeIntentStatus.pending,
            payload=payload,
            block_reason="; ".join(reasons) if reasons else None,
        )
