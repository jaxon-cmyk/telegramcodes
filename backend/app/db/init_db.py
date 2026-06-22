from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import Base, engine
from app.models import User, UserRole


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    with Session(engine) as db:
        existing_admin = db.scalar(select(User).where(User.email == settings.bootstrap_admin_email))
        if existing_admin:
            return
        admin = User(
            email=settings.bootstrap_admin_email,
            password_hash=hash_password(settings.bootstrap_admin_password),
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
