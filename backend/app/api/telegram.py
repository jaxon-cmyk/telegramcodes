from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import decrypt_secret, encrypt_secret
from app.db.session import get_db
from app.models import ParsedSignal, SignalStatus, TelegramChannel, TelegramMessage, TelegramSession, User
from app.schemas.common import (
    ChannelEnableRequest,
    ChannelRead,
    MessageRead,
    SearchRequest,
    TelegramConnectRequest,
    TelegramDialogRead,
    TelegramVerifyRequest,
)
from app.services.audit import audit
from app.services.parser import SignalParser
from app.services.telegram_service import TelegramService

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/connect")
async def connect_telegram(
    payload: TelegramConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    service = TelegramService()
    result = await service.begin_connect(payload.api_id, payload.api_hash, payload.phone)
    session = TelegramSession(
        user_id=current_user.id,
        api_id_encrypted=encrypt_secret(payload.api_id) or "",
        api_hash_encrypted=encrypt_secret(payload.api_hash) or "",
        phone_encrypted=encrypt_secret(payload.phone) or "",
        session_encrypted=encrypt_secret(result.get("session_token")),
        status=result["status"],
    )
    db.add(session)
    db.flush()
    audit(db, action="telegram_connect_started", entity_type="telegram_session", user_id=current_user.id, actor_user_id=current_user.id, entity_id=str(session.id))
    db.commit()
    return {"session_id": session.id, "status": session.status}


@router.post("/verify")
async def verify_telegram(
    payload: TelegramVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    session = db.scalar(select(TelegramSession).where(TelegramSession.id == payload.session_id, TelegramSession.user_id == current_user.id))
    if not session:
        raise HTTPException(status_code=404, detail="Telegram session not found")
    service = TelegramService()
    result = await service.verify_code(decrypt_secret(session.session_encrypted), payload.code, payload.password)
    session.session_encrypted = encrypt_secret(result["session_string"])
    session.status = result["status"]
    audit(db, action="telegram_verified", entity_type="telegram_session", user_id=current_user.id, actor_user_id=current_user.id, entity_id=str(session.id))
    db.commit()
    return {"session_id": session.id, "status": session.status}


@router.get("/dialogs", response_model=list[TelegramDialogRead])
async def dialogs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TelegramDialogRead]:
    session = db.scalar(select(TelegramSession).where(TelegramSession.user_id == current_user.id).order_by(TelegramSession.created_at.desc()))
    if not session:
        raise HTTPException(status_code=400, detail="Connect Telegram first")
    service = TelegramService()
    remote_dialogs = await service.list_dialogs(decrypt_secret(session.session_encrypted))
    existing = {
        channel.telegram_dialog_id: channel
        for channel in db.scalars(select(TelegramChannel).where(TelegramChannel.user_id == current_user.id))
    }
    return [
        TelegramDialogRead(
            dialog_id=item.dialog_id,
            title=item.title,
            kind=item.kind,
            is_enabled=existing.get(item.dialog_id).is_enabled if item.dialog_id in existing else False,
        )
        for item in remote_dialogs
    ]


@router.post("/channels/{dialog_id}/enable", response_model=ChannelRead)
async def enable_channel(
    dialog_id: str,
    payload: ChannelEnableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TelegramChannel:
    session = db.scalar(select(TelegramSession).where(TelegramSession.user_id == current_user.id).order_by(TelegramSession.created_at.desc()))
    if not session:
        raise HTTPException(status_code=400, detail="Connect Telegram first")
    channel = db.scalar(select(TelegramChannel).where(TelegramChannel.user_id == current_user.id, TelegramChannel.telegram_dialog_id == dialog_id))
    if not channel:
        channel = TelegramChannel(
            user_id=current_user.id,
            telegram_session_id=session.id,
            telegram_dialog_id=dialog_id,
            title=dialog_id.replace("-", " ").title(),
            kind="channel",
        )
        db.add(channel)
    channel.is_enabled = payload.enabled
    channel.last_sync_at = datetime.now(timezone.utc)
    audit(db, action="telegram_channel_toggled", entity_type="telegram_channel", user_id=current_user.id, actor_user_id=current_user.id, entity_id=dialog_id, details={"enabled": payload.enabled})
    db.commit()
    db.refresh(channel)
    return channel


@router.get("/messages/{dialog_id}", response_model=list[MessageRead])
async def sync_messages(
    dialog_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TelegramMessage]:
    channel = db.scalar(select(TelegramChannel).where(TelegramChannel.user_id == current_user.id, TelegramChannel.telegram_dialog_id == dialog_id))
    if not channel:
        raise HTTPException(status_code=404, detail="Enable channel before syncing messages")
    service = TelegramService()
    parser = SignalParser()
    session = db.scalar(select(TelegramSession).where(TelegramSession.id == channel.telegram_session_id, TelegramSession.user_id == current_user.id))
    for item in await service.fetch_messages(dialog_id, decrypt_secret(session.session_encrypted) if session else None):
        existing = db.scalar(
            select(TelegramMessage).where(
                TelegramMessage.user_id == current_user.id,
                TelegramMessage.channel_id == channel.id,
                TelegramMessage.telegram_message_id == item["telegram_message_id"],
            )
        )
        if existing:
            continue
        message = TelegramMessage(
            user_id=current_user.id,
            channel_id=channel.id,
            telegram_message_id=item["telegram_message_id"],
            text=item["text"],
            sender_name=item.get("sender_name"),
            sent_at=item.get("sent_at") or datetime.now(timezone.utc),
            raw_payload=item.get("raw_payload", {}),
        )
        db.add(message)
        db.flush()

        parse_result = parser.parse(message.text)
        signal = ParsedSignal(
            user_id=current_user.id,
            message_id=message.id,
            symbol=parse_result.symbol,
            side=parse_result.side,
            entry=parse_result.entry,
            stop_loss=parse_result.stop_loss,
            take_profits=parse_result.take_profits,
            lot=parse_result.lot,
            risk_percent=parse_result.risk_percent,
            confidence=parse_result.confidence,
            parser_source=parse_result.parser_source,
            explanation=parse_result.explanation,
            status=SignalStatus.parsed if parse_result.is_valid else SignalStatus.rejected,
            rejection_reason=parse_result.rejection_reason,
        )
        db.add(signal)
        audit(
            db,
            action="telegram_message_synced",
            entity_type="telegram_message",
            user_id=current_user.id,
            actor_user_id=current_user.id,
            entity_id=str(message.id),
            details={"dialog_id": dialog_id, "signal_status": signal.status.value},
        )
    channel.last_sync_at = datetime.now(timezone.utc)
    db.commit()
    return list(db.scalars(select(TelegramMessage).where(TelegramMessage.user_id == current_user.id, TelegramMessage.channel_id == channel.id).order_by(TelegramMessage.sent_at.desc())))


@router.post("/search", response_model=list[MessageRead])
def search_messages(payload: SearchRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TelegramMessage]:
    query = select(TelegramMessage).where(TelegramMessage.user_id == current_user.id, TelegramMessage.text.ilike(f"%{payload.query}%"))
    if payload.channel_id:
        query = query.where(TelegramMessage.channel_id == payload.channel_id)
    return list(db.scalars(query.order_by(TelegramMessage.sent_at.desc())))
