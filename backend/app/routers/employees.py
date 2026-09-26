from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import get_current_user, get_org_employee
from ..schemas import ConfigPayload, EmployeeProfilePayload
from ..security import hash_token, new_token

router = APIRouter()

AGENT_TOKEN_PREFIX = "mdr_"


def employee_out(employee: models.Employee) -> dict:
    config = employee.config
    return {
        "id": employee.id,
        "name": employee.name,
        "role": employee.role,
        "email": employee.email,
        "job_description": config.job_description if config else None,
        "role_tag": config.role_tag if config else None,
        "agent_token_created_at": (
            employee.agent_token_created_at.isoformat() + "Z" if employee.agent_token_created_at else None
        ),
    }


def config_out(employee: models.Employee) -> dict:
    config = employee.config
    return {
        "employee_id": employee.id,
        "job_description": config.job_description,
        "role_tag": config.role_tag,
        "software_weights": config.software_weights or {},
        "category_weights": config.category_weights or {},
        "schedule": config.schedule or {},
        "min_productive_hours": config.min_productive_hours,
        "max_idle_minutes": config.max_idle_minutes,
    }


def _ensure_email_free(db: Session, organization_id: int, email: str | None, exclude_id: int | None = None):
    if not email:
        return
    query = db.query(models.Employee).filter(
        models.Employee.organization_id == organization_id, models.Employee.email == email
    )
    if exclude_id is not None:
        query = query.filter(models.Employee.id != exclude_id)
    if query.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An employee with this email already exists")


@router.get("/employees")
def list_employees(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    employees = (
        db.query(models.Employee)
        .filter(models.Employee.organization_id == user.organization_id)
        .order_by(models.Employee.id.asc())
        .all()
    )
    return [employee_out(employee) for employee in employees]


@router.post("/employees", status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeProfilePayload,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _ensure_email_free(db, user.organization_id, payload.email)
    employee = models.Employee(
        organization_id=user.organization_id,
        name=payload.name,
        role=payload.role,
        email=payload.email,
        config=models.Config(job_description=payload.job_description, role_tag=payload.role_tag),
    )
    db.add(employee)
    db.commit()
    return employee_out(employee)


@router.get("/employees/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return employee_out(get_org_employee(employee_id, db, user))


@router.put("/employees/{employee_id}")
def update_employee(
    employee_id: int,
    payload: EmployeeProfilePayload,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    employee = get_org_employee(employee_id, db, user)
    _ensure_email_free(db, user.organization_id, payload.email, exclude_id=employee_id)

    employee.name = payload.name
    employee.role = payload.role
    employee.email = payload.email
    if employee.config is None:
        employee.config = models.Config()
    employee.config.job_description = payload.job_description
    employee.config.role_tag = payload.role_tag
    db.commit()
    return employee_out(employee)


@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Delete an employee together with their config and activity logs."""
    employee = get_org_employee(employee_id, db, user)
    db.query(models.ActivityLog).filter(models.ActivityLog.employee_id == employee_id).delete(
        synchronize_session=False
    )
    db.delete(employee)
    db.commit()


@router.post("/employees/{employee_id}/agent-token")
def rotate_agent_token(
    employee_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Issue a new desktop-agent token for this employee. Any previous token stops working.

    The token is returned once and only its hash is stored.
    """
    employee = get_org_employee(employee_id, db, user)
    token = new_token(AGENT_TOKEN_PREFIX)
    employee.agent_token_hash = hash_token(token)
    employee.agent_token_created_at = models.utcnow()
    db.commit()
    return {"employee_id": employee.id, "agent_token": token, "created_at": employee.agent_token_created_at.isoformat() + "Z"}


@router.delete("/employees/{employee_id}/agent-token", status_code=status.HTTP_204_NO_CONTENT)
def revoke_agent_token(
    employee_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    employee = get_org_employee(employee_id, db, user)
    employee.agent_token_hash = None
    employee.agent_token_created_at = None
    db.commit()


@router.get("/config/{employee_id}")
def get_config(employee_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    employee = get_org_employee(employee_id, db, user)
    if employee.config is None:
        raise HTTPException(status_code=404, detail="Config not found")
    return config_out(employee)


@router.post("/config/{employee_id}")
def save_config(
    employee_id: int,
    payload: ConfigPayload,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    employee = get_org_employee(employee_id, db, user)
    if employee.config is None:
        employee.config = models.Config()
    config = employee.config
    config.job_description = payload.job_description
    config.role_tag = payload.role_tag
    config.software_weights = payload.software_weights
    config.category_weights = payload.category_weights
    config.schedule = payload.schedule
    config.min_productive_hours = payload.min_productive_hours
    config.max_idle_minutes = payload.max_idle_minutes
    db.commit()
    return config_out(employee)
