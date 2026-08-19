import os
from fastapi import FastAPI, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from dotenv import load_dotenv
from .database import engine, Base, get_db
from . import models  # noqa — ensures models are registered before create_all

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Moudir.ai Backend")

AGENT_TOKEN = os.getenv("AGENT_TOKEN")


class ActivityEventCreate(BaseModel):
    employee_id: int
    event_type: str
    timestamp: str
    detail: dict = Field(default_factory=dict)


class IngestPayload(BaseModel):
    """Batched events from agent."""

    events: list[ActivityEventCreate]


@app.get("/health")
def health_check():
    return {"status": "ok"}


def verify_agent_token(x_agent_token: str = Header(None)):
    """Validate X-Agent-Token header."""
    if not AGENT_TOKEN or not x_agent_token or x_agent_token != AGENT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Agent-Token",
        )
    return x_agent_token


@app.post("/ingest")
def ingest_events(
    payload: IngestPayload,
    db: Session = Depends(get_db),
    token: str = Depends(verify_agent_token),
):
    """Store a batch of activity events from the agent."""
    stored_count = 0

    for event_data in payload.events:
        activity = models.ActivityLog(
            employee_id=event_data.employee_id,
            event_type=event_data.event_type,
            timestamp=datetime.fromisoformat(event_data.timestamp),
            detail=event_data.detail or {},
        )
        db.add(activity)
        stored_count += 1

    db.commit()

    return {"status": "success", "events_stored": stored_count}
