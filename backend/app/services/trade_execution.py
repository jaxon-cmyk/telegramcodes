from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AutomationRule, ExecutedTrade, MT5Account, ParsedSignal, TelegramMessage, TradeIntent, TradeIntentStatus
from app.services.audit import audit
from app.services.automation import AutomationEngine
from app.services.mt5_bridge import MT5Bridge


async def evaluate_and_execute_signal(
    db: Session,
    signal: ParsedSignal,
    *,
    actor_user_id: int | None = None,
    channel_id: int | None = None,
) -> list[TradeIntent]:
    if channel_id is None:
        message = db.scalar(select(TelegramMessage).where(TelegramMessage.id == signal.message_id, TelegramMessage.user_id == signal.user_id))
        channel_id = message.channel_id if message else None

    if channel_id is None:
        audit(
            db,
            action="auto_trade_skipped",
            entity_type="parsed_signal",
            user_id=signal.user_id,
            actor_user_id=actor_user_id,
            entity_id=str(signal.id),
            details={"reason": "Could not determine source channel"},
        )
        return []

    rules = list(
        db.scalars(
            select(AutomationRule).where(
                AutomationRule.user_id == signal.user_id,
                AutomationRule.channel_id == channel_id,
                AutomationRule.is_enabled.is_(True),
            )
        )
    )
    intents: list[TradeIntent] = []
    if not rules:
        audit(
            db,
            action="auto_trade_skipped",
            entity_type="parsed_signal",
            user_id=signal.user_id,
            actor_user_id=actor_user_id,
            entity_id=str(signal.id),
            details={"reason": "No enabled automation rules"},
        )
        return intents

    for rule in rules:
        intent = AutomationEngine().evaluate(db, signal, rule)
        db.add(intent)
        db.flush()
        intents.append(intent)

        if intent.status == TradeIntentStatus.pending:
            account = db.scalar(select(MT5Account).where(MT5Account.id == rule.mt5_account_id, MT5Account.user_id == signal.user_id))
            if not account:
                intent.status = TradeIntentStatus.failed
                intent.block_reason = "MT5 account missing"
            else:
                try:
                    check = await MT5Bridge().order_check(account.provider_account_id, intent.payload)
                    response = await MT5Bridge().order_send(account.provider_account_id, intent.payload)
                    intent.provider_response = {"check": check, "send": response}
                    intent.status = TradeIntentStatus.executed
                    db.add(
                        ExecutedTrade(
                            user_id=signal.user_id,
                            trade_intent_id=intent.id,
                            mt5_account_id=account.id,
                            provider_order_id=response.get("order_id"),
                            symbol=intent.payload["symbol"],
                            side=intent.payload["side"],
                            volume=intent.payload.get("volume"),
                            entry=intent.payload.get("entry"),
                            stop_loss=intent.payload.get("stop_loss"),
                            take_profits=intent.payload.get("take_profits", []),
                            status="submitted",
                        )
                    )
                except Exception as exc:
                    intent.status = TradeIntentStatus.failed
                    intent.block_reason = str(exc)

        audit(
            db,
            action="auto_trade_evaluated",
            entity_type="trade_intent",
            user_id=signal.user_id,
            actor_user_id=actor_user_id,
            entity_id=str(intent.id),
            details={
                "automation_rule_id": rule.id,
                "status": intent.status.value,
                "reason": intent.block_reason,
            },
        )

    return intents
