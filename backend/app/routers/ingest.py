import logging
from datetime import timedelta

from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import ActivityEvent
from ..security import hash_token
from ..settings import get_settings

logger = logging.getLogger("moudir.ingest")
router = APIRouter()

_event_adapter = TypeAdapter(ActivityEvent)
MAX_CLOCK_SKEW = timedelta(hours=1)


def get_agent_employee(
    x_agent_token: str | None = Header(None),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> models.Employee:
    token = x_agent_token
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if token:
        employee = db.query(models.Employee).filter(models.Employee.agent_token_hash == hash_token(token)).first()
        if employee is not None:
            return employee
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing agent token")


@router.post("/ingest")
def ingest_events(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    employee: models.Employee = Depends(get_agent_employee),
):
    """Store a batch of activity events for the employee the agent token belongs to.

    Invalid events are skipped and counted rather than failing the batch, so one bad
    event can't block an agent's queue forever.
    """
    events = payload.get("events")
    if not isinstance(events, list):
        raise HTTPException(status_code=422, detail="events must be a list")
    if len(events) > get_settings().max_ingest_events:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Send at most {get_settings().max_ingest_events} events per request",
        )

    latest_allowed = models.utcnow() + MAX_CLOCK_SKEW
    stored = 0
    rejected = 0
    for raw in events:
        try:
            event = _event_adapter.validate_python(raw)
        except ValidationError:
            rejected += 1
            continue
        if (event.employee_id is not None and event.employee_id != employee.id) or event.timestamp > latest_allowed:
            rejected += 1
            continue
        db.add(
            models.ActivityLog(
                employee_id=employee.id,
                event_type=event.event_type,
                timestamp=event.timestamp,
                detail=event.detail,
            )
        )
        stored += 1

    db.commit()
    if rejected:
        logger.warning("employee %s: rejected %s of %s events", employee.id, rejected, len(events))
    return {"status": "success", "events_stored": stored, "events_rejected": rejected}
