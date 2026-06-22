from sqlalchemy.orm import Session

from app.models import AuditLog


def audit(
    db: Session,
    *,
    action: str,
    entity_type: str,
    user_id: int | None = None,
    actor_user_id: int | None = None,
    entity_id: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    item = AuditLog(
        action=action,
        entity_type=entity_type,
        user_id=user_id,
        actor_user_id=actor_user_id,
        entity_id=entity_id,
        details=details or {},
    )
    db.add(item)
    db.flush()
    return item
