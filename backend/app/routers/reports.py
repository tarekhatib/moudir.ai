from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import get_current_user, get_org_employee
from ..pdf import render_report_pdf
from ..scoring import daily_trend, period_report

router = APIRouter()

PERIOD_PATTERN = "^(daily|weekly|monthly)$"


@router.get("/reports/{employee_id}")
def get_report(
    employee_id: int,
    period: str = Query("daily", pattern=PERIOD_PATTERN),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return period_report(db, get_org_employee(employee_id, db, user), period)


@router.get("/reports/{employee_id}/trend")
def get_report_trend(
    employee_id: int,
    days: int = Query(14, ge=1, le=90),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Per-day scores for the last `days` days (UTC), oldest first, including days with no activity."""
    employee = get_org_employee(employee_id, db, user)
    return {"employee_id": employee.id, "days": days, "points": daily_trend(db, employee, days)}


@router.get("/reports/{employee_id}/pdf")
def export_report_pdf(
    employee_id: int,
    period: str = Query("daily", pattern=PERIOD_PATTERN),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    employee = get_org_employee(employee_id, db, user)
    pdf = render_report_pdf(employee, period_report(db, employee, period))
    filename = f"report_{employee.id}_{period}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"},
    )


@router.get("/team/summary")
def get_team_summary(
    period: str = Query("daily", pattern=PERIOD_PATTERN),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Report summary for every employee in the organization, used by the dashboard team overview."""
    employees = (
        db.query(models.Employee)
        .filter(models.Employee.organization_id == user.organization_id)
        .order_by(models.Employee.id.asc())
        .all()
    )
    return [
        {"id": employee.id, "name": employee.name, "role": employee.role, **period_report(db, employee, period)}
        for employee in employees
    ]
