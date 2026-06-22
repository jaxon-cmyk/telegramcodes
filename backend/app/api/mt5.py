import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import encrypt_secret
from app.db.session import get_db
from app.models import MT5Account, User
from app.schemas.common import MT5AccountConnect, MT5AccountRead
from app.services.audit import audit
from app.services.mt5_bridge import MT5Bridge

router = APIRouter(prefix="/mt5/accounts", tags=["mt5"])


@router.post("/connect", response_model=MT5AccountRead)
def connect_account(payload: MT5AccountConnect, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MT5Account:
    account = MT5Account(
        user_id=current_user.id,
        name=payload.name,
        provider=payload.provider,
        provider_account_id=payload.provider_account_id,
        credentials_encrypted=encrypt_secret(json.dumps(payload.credentials)) or "",
        status="connected",
    )
    db.add(account)
    db.flush()
    audit(db, action="mt5_account_connected", entity_type="mt5_account", user_id=current_user.id, actor_user_id=current_user.id, entity_id=str(account.id))
    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=list[MT5AccountRead])
def accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[MT5Account]:
    return list(db.scalars(select(MT5Account).where(MT5Account.user_id == current_user.id).order_by(MT5Account.created_at.desc())))


@router.get("/{account_id}/status")
async def account_status(account_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    account = db.scalar(select(MT5Account).where(MT5Account.id == account_id, MT5Account.user_id == current_user.id))
    if not account:
        raise HTTPException(status_code=404, detail="MT5 account not found")
    status = await MT5Bridge().account_status(account.provider_account_id)
    account.status = status.get("status", account.status)
    info = status.get("account_info", {})
    account.balance = info.get("balance", account.balance)
    account.equity = info.get("equity", account.equity)
    account.last_health_check_at = datetime.now(timezone.utc)
    db.commit()
    return status


@router.get("/{account_id}/positions")
async def positions(account_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    account = db.scalar(select(MT5Account).where(MT5Account.id == account_id, MT5Account.user_id == current_user.id))
    if not account:
        raise HTTPException(status_code=404, detail="MT5 account not found")
    return await MT5Bridge().positions(account.provider_account_id)


@router.get("/{account_id}/history")
async def history(account_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    account = db.scalar(select(MT5Account).where(MT5Account.id == account_id, MT5Account.user_id == current_user.id))
    if not account:
        raise HTTPException(status_code=404, detail="MT5 account not found")
    return await MT5Bridge().history(account.provider_account_id)
