from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import AuditLog, ParsedSignal, SignalStatus, TelegramMessage, User
from app.schemas.common import AuditLogRead, MessageRead, ParsedSignalRead
from app.services.audit import audit
from app.services.parser import SignalParser

router = APIRouter(tags=["messages"])


@router.get("/messages", response_model=list[MessageRead])
def messages(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TelegramMessage]:
    return list(db.scalars(select(TelegramMessage).where(TelegramMessage.user_id == current_user.id).order_by(TelegramMessage.sent_at.desc()).limit(200)))


@router.get("/signals", response_model=list[ParsedSignalRead])
def signals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ParsedSignal]:
    return list(db.scalars(select(ParsedSignal).where(ParsedSignal.user_id == current_user.id).order_by(ParsedSignal.created_at.desc()).limit(200)))


@router.post("/signals/{message_id}/reparse", response_model=ParsedSignalRead)
def reparse_signal(message_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ParsedSignal:
    message = db.scalar(select(TelegramMessage).where(TelegramMessage.id == message_id, TelegramMessage.user_id == current_user.id))
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    result = SignalParser().parse(message.text)
    signal = ParsedSignal(
        user_id=current_user.id,
        message_id=message.id,
        symbol=result.symbol,
        side=result.side,
        entry=result.entry,
        stop_loss=result.stop_loss,
        take_profits=result.take_profits,
        lot=result.lot,
        risk_percent=result.risk_percent,
        confidence=result.confidence,
        parser_source=result.parser_source,
        explanation=result.explanation,
        status=SignalStatus.parsed if result.is_valid else SignalStatus.rejected,
        rejection_reason=result.rejection_reason,
    )
    db.add(signal)
    db.flush()
    audit(db, action="signal_reparsed", entity_type="parsed_signal", user_id=current_user.id, actor_user_id=current_user.id, entity_id=str(signal.id), details={"status": signal.status.value})
    db.commit()
    db.refresh(signal)
    return signal


@router.get("/audit-logs", response_model=list[AuditLogRead])
def audit_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[AuditLog]:
    return list(
        db.scalars(
            select(AuditLog)
            .where(AuditLog.user_id == current_user.id)
            .order_by(AuditLog.created_at.desc())
            .limit(200)
        )
    )
