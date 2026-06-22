import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import Invite, MT5Account, TelegramMessage, TradeIntent, TradeIntentStatus, User, UserRole
from app.schemas.common import InviteCreate, InviteRead, UserAdminUpdate, UserRead
from app.services.audit import audit

router = APIRouter(tags=["admin"])


@router.post("/invites", response_model=InviteRead)
def create_invite(payload: InviteCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> Invite:
    invite = Invite(
        code=secrets.token_urlsafe(24),
        email=payload.email.lower() if payload.email else None,
        expires_at=payload.expires_at,
        created_by_user_id=admin.id,
    )
    db.add(invite)
    db.flush()
    audit(db, action="invite_created", entity_type="invite", actor_user_id=admin.id, entity_id=str(invite.id))
    db.commit()
    db.refresh(invite)
    return invite


@router.get("/admin/users", response_model=list[UserRead])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())))


@router.patch("/admin/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    target = db.scalar(select(User).where(User.id == user_id))
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    updates: dict = {}
    if payload.role is not None:
        if payload.role not in {UserRole.admin.value, UserRole.user.value}:
            raise HTTPException(status_code=400, detail="Role must be admin or user")
        if target.id == admin.id and payload.role != UserRole.admin.value:
            raise HTTPException(status_code=400, detail="You cannot remove your own admin role")
        target.role = UserRole(payload.role)
        updates["role"] = payload.role

    if payload.is_active is not None:
        if target.id == admin.id and not payload.is_active:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
        target.is_active = payload.is_active
        updates["is_active"] = payload.is_active

    audit(
        db,
        action="admin_user_updated",
        entity_type="user",
        user_id=target.id,
        actor_user_id=admin.id,
        entity_id=str(target.id),
        details=updates,
    )
    db.commit()
    db.refresh(target)
    return target


@router.get("/admin/system-health")
def system_health(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    return {
        "users": db.scalar(select(func.count(User.id))),
        "mt5_accounts": db.scalar(select(func.count(MT5Account.id))),
        "telegram_messages": db.scalar(select(func.count(TelegramMessage.id))),
        "failed_trades": db.scalar(select(func.count(TradeIntent.id)).where(TradeIntent.status == TradeIntentStatus.failed)),
        "blocked_trades": db.scalar(select(func.count(TradeIntent.id)).where(TradeIntent.status == TradeIntentStatus.blocked)),
    }
