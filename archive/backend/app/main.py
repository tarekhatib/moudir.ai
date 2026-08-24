import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Depends, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dotenv import load_dotenv

try:
    from weasyprint import HTML
except Exception:  # pragma: no cover - fallback used when system libs are unavailable
    HTML = None

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
except Exception:  # pragma: no cover - only needed if reportlab missing
    letter = None
    getSampleStyleSheet = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None

from .database import Base, engine, get_db
from . import models  # noqa — ensures models are registered before create_all

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Moudir.ai Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_TOKEN = os.getenv("AGENT_TOKEN")
REPORTS_DIR = Path(__file__).resolve().parent.parent / "docs" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class ActivityEventCreate(BaseModel):
    employee_id: int
    event_type: str
    timestamp: str
    detail: dict = Field(default_factory=dict)


class IngestPayload(BaseModel):
    """Batched events from agent."""

    events: list[ActivityEventCreate]


class EmployeeProfilePayload(BaseModel):
    name: str
    role: str | None = None
    email: str | None = None
    job_description: str | None = None
    role_tag: str | None = None


class ConfigPayload(BaseModel):
    job_description: str | None = None
    role_tag: str | None = None
    software_weights: dict = Field(default_factory=dict)
    category_weights: dict = Field(default_factory=dict)
    schedule: dict = Field(default_factory=dict)
    min_productive_hours: float = 6.0
    max_idle_minutes: int = 60


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


@app.get("/employees")
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(models.Employee).order_by(models.Employee.id.asc()).all()
    rows = []
    for employee in employees:
        config = db.query(models.Config).filter(models.Config.employee_id == employee.id).first()
        rows.append(
            {
                "id": employee.id,
                "name": employee.name,
                "role": employee.role,
                "email": employee.email,
                "job_description": config.job_description if config else None,
                "role_tag": config.role_tag if config else None,
            }
        )
    return rows


@app.post("/employees")
def create_employee(payload: EmployeeProfilePayload, db: Session = Depends(get_db)):
    employee = models.Employee(
        name=payload.name,
        role=payload.role,
        email=payload.email,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)

    config = db.query(models.Config).filter(models.Config.employee_id == employee.id).first()
    if config is None:
        config = models.Config(employee_id=employee.id)
        db.add(config)

    config.job_description = payload.job_description
    config.role_tag = payload.role_tag
    db.commit()
    db.refresh(config)

    return {
        "id": employee.id,
        "name": employee.name,
        "role": employee.role,
        "email": employee.email,
        "job_description": config.job_description,
        "role_tag": config.role_tag,
    }


@app.get("/employees/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    config = db.query(models.Config).filter(models.Config.employee_id == employee_id).first()
    return {
        "id": employee.id,
        "name": employee.name,
        "role": employee.role,
        "email": employee.email,
        "job_description": config.job_description if config else None,
        "role_tag": config.role_tag if config else None,
    }


@app.put("/employees/{employee_id}")
def update_employee(employee_id: int, payload: EmployeeProfilePayload, db: Session = Depends(get_db)):
    employee = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.name = payload.name
    employee.role = payload.role
    employee.email = payload.email

    config = db.query(models.Config).filter(models.Config.employee_id == employee_id).first()
    if config is None:
        config = models.Config(employee_id=employee_id)
        db.add(config)

    config.job_description = payload.job_description
    config.role_tag = payload.role_tag

    db.commit()
    db.refresh(employee)
    db.refresh(config)

    return {
        "id": employee.id,
        "name": employee.name,
        "role": employee.role,
        "email": employee.email,
        "job_description": config.job_description,
        "role_tag": config.role_tag,
    }


@app.get("/config/{employee_id}")
def get_config(employee_id: int, db: Session = Depends(get_db)):
    config = db.query(models.Config).filter(models.Config.employee_id == employee_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    return {
        "employee_id": config.employee_id,
        "job_description": config.job_description,
        "role_tag": config.role_tag,
        "software_weights": config.software_weights or {},
        "category_weights": config.category_weights or {},
        "schedule": config.schedule or {},
        "min_productive_hours": config.min_productive_hours,
        "max_idle_minutes": config.max_idle_minutes,
    }


@app.post("/config/{employee_id}")
def save_config(
    employee_id: int,
    payload: ConfigPayload,
    db: Session = Depends(get_db),
):
    config = db.query(models.Config).filter(models.Config.employee_id == employee_id).first()
    if not config:
        config = models.Config(employee_id=employee_id)
        db.add(config)

    config.job_description = payload.job_description
    config.role_tag = payload.role_tag
    config.software_weights = payload.software_weights or {}
    config.category_weights = payload.category_weights or {}
    config.schedule = payload.schedule or {}
    config.min_productive_hours = payload.min_productive_hours
    config.max_idle_minutes = payload.max_idle_minutes

    db.commit()
    db.refresh(config)

    return {
        "employee_id": config.employee_id,
        "job_description": config.job_description,
        "role_tag": config.role_tag,
        "software_weights": config.software_weights or {},
        "category_weights": config.category_weights or {},
        "schedule": config.schedule or {},
        "min_productive_hours": config.min_productive_hours,
        "max_idle_minutes": config.max_idle_minutes,
    }


def _score_logs_for_period(employee_id: int, db: Session, period: str):
    today = datetime.utcnow().date()
    if period == "daily":
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)
    elif period == "weekly":
        start = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
        end = start + timedelta(days=7)
    elif period == "monthly":
        start = datetime(today.year, today.month, 1)
        if start.month == 12:
            end = datetime(start.year + 1, 1, 1)
        else:
            end = datetime(start.year, start.month + 1, 1)
    else:
        raise HTTPException(status_code=400, detail="period must be daily, weekly, or monthly")

    logs = (
        db.query(models.ActivityLog)
        .filter(
            models.ActivityLog.employee_id == employee_id,
            models.ActivityLog.timestamp >= start,
            models.ActivityLog.timestamp < end,
        )
        .all()
    )

    config = db.query(models.Config).filter(models.Config.employee_id == employee_id).first()
    category_weights = (config.category_weights or {}) if config else {}
    app_weights = (config.software_weights or {}) if config else {}

    app_focus_count = sum(1 for log in logs if log.event_type == "app_focus")
    browser_count = sum(1 for log in logs if log.event_type == "browser_tab")
    idle_events = sum(1 for log in logs if log.event_type == "idle_start")
    login_count = sum(1 for log in logs if log.event_type == "login")

    app_usage_score = min(1.0, app_focus_count / 20.0)
    browser_score = min(1.0, browser_count / 15.0)
    punctuality_score = 1.0 if login_count else 0.0
    idle_score = max(0.0, 1.0 - (idle_events * 0.15))

    weighted_total = (
        app_usage_score * float(category_weights.get("app_usage", 0.4))
        + browser_score * float(category_weights.get("browser", 0.2))
        + punctuality_score * float(category_weights.get("punctuality", 0.2))
        + idle_score * float(category_weights.get("idle", 0.2))
    )
    weighted_total = max(0.0, min(1.0, weighted_total))

    event_summary = {
        "app_focus": app_focus_count,
        "browser_tab": browser_count,
        "idle_start": idle_events,
        "login": login_count,
        "outlook_activity": sum(1 for log in logs if log.event_type == "outlook_activity"),
    }

    return {
        "employee_id": employee_id,
        "period": period,
        "average_score": weighted_total,
        "total_productive_hours": round(app_focus_count * 0.1, 2),
        "total_idle_minutes": idle_events * 15,
        "event_summary": event_summary,
        "app_weights": app_weights,
    }


@app.get("/reports/{employee_id}")
def get_reports(
    employee_id: int,
    period: str = Query("daily", regex="daily|weekly|monthly"),
    db: Session = Depends(get_db),
):
    return _score_logs_for_period(employee_id, db, period)


@app.get("/reports/{employee_id}/pdf")
def export_report_pdf(
    employee_id: int,
    period: str = Query("daily", regex="daily|weekly|monthly"),
    db: Session = Depends(get_db),
):
    summary = _score_logs_for_period(employee_id, db, period)
    safe_name = f"report_{employee_id}_{period}.pdf"
    output_path = REPORTS_DIR / safe_name

    if HTML is not None:
        html = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; margin: 30px; color: #111; }}
              h1 {{ font-size: 32px; margin-bottom: 8px; }}
              h2 {{ font-size: 20px; margin-top: 24px; }}
              .row {{ margin: 10px 0; }}
              .label {{ font-weight: bold; display: inline-block; width: 220px; }}
            </style>
          </head>
          <body>
            <h1>Moudir.ai Report</h1>
            <div class='row'><span class='label'>Employee ID:</span> {employee_id}</div>
            <div class='row'><span class='label'>Period:</span> {period}</div>
            <div class='row'><span class='label'>Average score:</span> {summary['average_score']:.2f}</div>
            <div class='row'><span class='label'>Productive hours:</span> {summary['total_productive_hours']}</div>
            <div class='row'><span class='label'>Idle minutes:</span> {summary['total_idle_minutes']}</div>
            <h2>Event Summary</h2>
            <div class='row'><span class='label'>App focus:</span> {summary['event_summary']['app_focus']}</div>
            <div class='row'><span class='label'>Browser tabs:</span> {summary['event_summary']['browser_tab']}</div>
            <div class='row'><span class='label'>Idle starts:</span> {summary['event_summary']['idle_start']}</div>
            <div class='row'><span class='label'>Logins:</span> {summary['event_summary']['login']}</div>
          </body>
        </html>
        """
        try:
            HTML(string=html).write_pdf(str(output_path))
            return FileResponse(output_path, media_type="application/pdf", filename=safe_name)
        except Exception:
            pass

    if letter is None or getSampleStyleSheet is None or SimpleDocTemplate is None:
        raise HTTPException(status_code=500, detail="PDF export is unavailable because no PDF generator is configured.")

    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("Moudir.ai Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Employee ID: {employee_id}"))
    story.append(Paragraph(f"Period: {period}"))
    story.append(Paragraph(f"Average score: {summary['average_score']:.2f}"))
    story.append(Paragraph(f"Productive hours: {summary['total_productive_hours']}"))
    story.append(Paragraph(f"Idle minutes: {summary['total_idle_minutes']}"))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Event Summary"))
    story.append(Paragraph(f"App focus: {summary['event_summary']['app_focus']}"))
    story.append(Paragraph(f"Browser tabs: {summary['event_summary']['browser_tab']}"))
    story.append(Paragraph(f"Idle starts: {summary['event_summary']['idle_start']}"))
    story.append(Paragraph(f"Logins: {summary['event_summary']['login']}"))

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    doc.build(story)
    return FileResponse(output_path, media_type="application/pdf", filename=safe_name)
