from datetime import datetime, timezone
from fastapi import HTTPException

CLOSED_STATUSES = ("done", "cancelled")

# Из какого статуса в какие можно перейти (README, раздел 5, пункт 3)
ALLOWED_TRANSITIONS = {
    "new": ("in_progress", "cancelled"),
    "in_progress": ("done", "cancelled", "new"),
    "done": ("in_progress",),
    "cancelled": ("new",),
}

def apply_status(obj, new_status: str):
    """Меняет статус цели или задачи. Ставит completed_at при переходе в done и очищает при переоткрытии."""
    if new_status not in ALLOWED_TRANSITIONS[obj.status]:
        raise HTTPException(status_code=409, detail=f"Недопустимый переход статуса: {obj.status} -> {new_status}.")
    obj.status = new_status
    obj.completed_at = datetime.now(timezone.utc) if new_status == "done" else None
