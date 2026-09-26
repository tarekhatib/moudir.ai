from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .security import hash_token

SESSION_COOKIE = "moudir_session"


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        session = (
            db.query(models.AuthSession)
            .filter(models.AuthSession.token_hash == hash_token(token))
            .first()
        )
        if session is not None and session.expires_at > models.utcnow():
            return session.user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not signed in")


def require_owner(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the account owner can do this")
    return user


def get_org_employee(employee_id: int, db: Session, user: models.User) -> models.Employee:
    """Look up an employee in the caller's organization; other organizations' employees are a 404."""
    employee = (
        db.query(models.Employee)
        .filter(models.Employee.id == employee_id, models.Employee.organization_id == user.organization_id)
        .first()
    )
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee
