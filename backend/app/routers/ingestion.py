"""
POST /ingest — receives buffered activity events from the Windows agent.
Auth: Authorization: Bearer <AGENT_TOKEN>, matched against the backend's own
AGENT_TOKEN env var (shared secret, single-agent pilot).
"""

import os
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ActivityLog
from app.schemas import IngestRequest, IngestResponse

router = APIRouter()


def verify_agent_token(authorization: str = Header(default=None)):
    expected_token = os.getenv("AGENT_TOKEN")
    if not expected_token:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "AGENT_TOKEN not configured on backend"
        )
    if authorization != f"Bearer {expected_token}":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing agent token")


@router.post("", response_model=IngestResponse)
def ingest_events(
    payload: IngestRequest,
    db: Session = Depends(get_db),
    _token: None = Depends(verify_agent_token),
):
    logs = [
        ActivityLog(
            employee_id=event.employee_id,
            event_type=event.event_type,
            timestamp=event.timestamp or datetime.utcnow(),
            detail=event.detail or {},
        )
        for event in payload.events
    ]
    db.add_all(logs)
    db.commit()
    return IngestResponse(ingested=len(logs))
