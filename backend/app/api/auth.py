from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Invite, User
from app.schemas.common import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.services.audit import audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    invite = db.scalar(select(Invite).where(Invite.code == payload.invite_code))
    if not invite or invite.used_at:
        raise HTTPException(status_code=400, detail="Invalid or used invite code")
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite code expired")
    if invite.email and invite.email.lower() != payload.email.lower():
        raise HTTPException(status_code=400, detail="Invite email does not match")
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    invite.used_by_user_id = user.id
    invite.used_at = datetime.now(timezone.utc)
    audit(db, action="registered", entity_type="user", user_id=user.id, actor_user_id=user.id, entity_id=str(user.id))
    db.commit()
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    audit(db, action="login", entity_type="user", user_id=user.id, actor_user_id=user.id, entity_id=str(user.id))
    db.commit()
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)) -> dict:
    return {"ok": True, "user_id": current_user.id}


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
