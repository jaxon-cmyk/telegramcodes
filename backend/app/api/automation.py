from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import AutomationRule, ExecutedTrade, MT5Account, ParsedSignal, TradeIntent, TradeIntentStatus, User
from app.schemas.common import AutomationRuleCreate, AutomationRulePatch, AutomationRuleRead, ExecutedTradeRead, TradeIntentRead
from app.services.audit import audit
from app.services.automation import AutomationEngine
from app.services.mt5_bridge import MT5Bridge

router = APIRouter(tags=["automation"])


@router.post("/automation-rules", response_model=AutomationRuleRead)
def create_rule(payload: AutomationRuleCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AutomationRule:
    account = db.scalar(select(MT5Account).where(MT5Account.id == payload.mt5_account_id, MT5Account.user_id == current_user.id))
    if not account:
        raise HTTPException(status_code=404, detail="MT5 account not found")
    rule = AutomationRule(user_id=current_user.id, **payload.model_dump())
    db.add(rule)
    db.flush()
    audit(db, action="automation_rule_created", entity_type="automation_rule", user_id=current_user.id, actor_user_id=current_user.id, entity_id=str(rule.id))
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/automation-rules", response_model=list[AutomationRuleRead])
def rules(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[AutomationRule]:
    return list(db.scalars(select(AutomationRule).where(AutomationRule.user_id == current_user.id).order_by(AutomationRule.created_at.desc())))


@router.patch("/automation-rules/{rule_id}", response_model=AutomationRuleRead)
def patch_rule(rule_id: int, payload: AutomationRulePatch, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AutomationRule:
    rule = db.scalar(select(AutomationRule).where(AutomationRule.id == rule_id, AutomationRule.user_id == current_user.id))
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    audit(db, action="automation_rule_updated", entity_type="automation_rule", user_id=current_user.id, actor_user_id=current_user.id, entity_id=str(rule.id))
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/trade-intents", response_model=list[TradeIntentRead])
def trade_intents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TradeIntent]:
    return list(db.scalars(select(TradeIntent).where(TradeIntent.user_id == current_user.id).order_by(TradeIntent.created_at.desc()).limit(200)))


@router.post("/trade-intents/{signal_id}/execute-test", response_model=TradeIntentRead)
async def execute_test(signal_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TradeIntent:
    signal = db.scalar(select(ParsedSignal).where(ParsedSignal.id == signal_id, ParsedSignal.user_id == current_user.id))
    if not signal:
        raise HTTPException(status_code=404, detail="Parsed signal not found")
    rule = db.scalar(select(AutomationRule).where(AutomationRule.user_id == current_user.id, AutomationRule.is_enabled.is_(True)).limit(1))
    if not rule:
        raise HTTPException(status_code=400, detail="Create an enabled automation rule first")
    intent = AutomationEngine().evaluate(db, signal, rule)
    db.add(intent)
    db.flush()
    if intent.status == TradeIntentStatus.pending:
        account = db.scalar(select(MT5Account).where(MT5Account.id == rule.mt5_account_id, MT5Account.user_id == current_user.id))
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
                        user_id=current_user.id,
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
    audit(db, action="trade_intent_evaluated", entity_type="trade_intent", user_id=current_user.id, actor_user_id=current_user.id, entity_id=str(intent.id), details={"status": intent.status.value, "reason": intent.block_reason})
    db.commit()
    db.refresh(intent)
    return intent


@router.get("/trades", response_model=list[ExecutedTradeRead])
def trades(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ExecutedTrade]:
    return list(db.scalars(select(ExecutedTrade).where(ExecutedTrade.user_id == current_user.id).order_by(ExecutedTrade.created_at.desc()).limit(200)))
