"""
Pydantic request/response models for the ingestion API.
See /docs/api-contract.md.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ActivityEvent(BaseModel):
    employee_id: int
    event_type: str  # login, logout, app_focus, idle, browser_tab, outlook
    timestamp: Optional[datetime] = None
    detail: Optional[Dict[str, Any]] = None


class IngestRequest(BaseModel):
    events: List[ActivityEvent]


class IngestResponse(BaseModel):
    ingested: int
