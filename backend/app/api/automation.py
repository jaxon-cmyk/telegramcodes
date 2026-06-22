from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import AutomationRule, ExecutedTrade, MT5Account, ParsedSignal, TradeIntent, TradeIntentStatus, User
from app.schemas.common import AutomationRuleCreate, AutomationRulePatch, AutomationRuleRead, ExecutedTradeRead, TradeIntentRead
from app.services.audit import audit
from app.services.trade_execution import evaluate_and_execute_signal

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
    intents = await evaluate_and_execute_signal(db, signal, actor_user_id=current_user.id)
    if not intents:
        raise HTTPException(status_code=400, detail="Create an enabled automation rule first")
    db.commit()
    intent = intents[0]
    db.refresh(intent)
    return intent


@router.get("/trades", response_model=list[ExecutedTradeRead])
def trades(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ExecutedTrade]:
    return list(db.scalars(select(ExecutedTrade).where(ExecutedTrade.user_id == current_user.id).order_by(ExecutedTrade.created_at.desc()).limit(200)))
