import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import SESSION_COOKIE, get_current_user, require_owner
from ..schemas import LoginPayload, ManagerCreatePayload, PasswordChangePayload, SignupPayload
from ..security import hash_password, hash_token, login_limiter, new_token, verify_password
from ..settings import get_settings

logger = logging.getLogger("moudir.auth")
router = APIRouter()


def user_out(user: models.User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


def me_out(user: models.User) -> dict:
    return {
        "user": user_out(user),
        "organization": {"id": user.organization.id, "name": user.organization.name},
    }


def _start_session(db: Session, response: Response, user: models.User) -> None:
    settings = get_settings()
    now = models.utcnow()
    db.query(models.AuthSession).filter(
        models.AuthSession.user_id == user.id, models.AuthSession.expires_at <= now
    ).delete(synchronize_session=False)

    token = new_token()
    db.add(
        models.AuthSession(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=now + timedelta(hours=settings.session_ttl_hours),
        )
    )
    db.commit()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )


def _email_taken(db: Session, email: str) -> bool:
    return db.query(models.User).filter(models.User.email == email).first() is not None


@router.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupPayload, response: Response, db: Session = Depends(get_db)):
    if not get_settings().allow_signup:
        raise HTTPException(status_code=403, detail="Sign-up is disabled")
    if _email_taken(db, payload.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    organization = models.Organization(name=payload.organization_name)
    user = models.User(
        organization=organization,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="owner",
    )
    db.add_all([organization, user])
    db.commit()
    logger.info("organization %s created by user %s", organization.id, user.id)
    _start_session(db, response, user)
    return me_out(user)


@router.post("/auth/login")
def login(payload: LoginPayload, request: Request, response: Response, db: Session = Depends(get_db)):
    settings = get_settings()
    window = settings.login_window_minutes * 60
    keys = [f"email:{payload.email}", f"ip:{request.client.host if request.client else 'unknown'}"]
    if any(login_limiter.is_blocked(key, settings.login_max_failures, window) for key in keys):
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Try again in a few minutes.")

    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not verify_password(payload.password, user.password_hash if user else None):
        for key in keys:
            login_limiter.record_failure(key)
        logger.info("failed sign-in for %s", payload.email)
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    login_limiter.reset(keys[0])
    _start_session(db, response, user)
    return me_out(user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        db.query(models.AuthSession).filter(models.AuthSession.token_hash == hash_token(token)).delete(
            synchronize_session=False
        )
        db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/auth/me")
def me(user: models.User = Depends(get_current_user)):
    return me_out(user)


@router.post("/auth/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChangePayload,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    # Sign out every other session; keep the one making this request.
    current_hash = hash_token(request.cookies.get(SESSION_COOKIE, ""))
    db.query(models.AuthSession).filter(
        models.AuthSession.user_id == user.id, models.AuthSession.token_hash != current_hash
    ).delete(synchronize_session=False)
    db.commit()


# --- Organization & manager accounts ---------------------------------------


@router.get("/organization/users")
def list_managers(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    users = (
        db.query(models.User)
        .filter(models.User.organization_id == user.organization_id)
        .order_by(models.User.id.asc())
        .all()
    )
    return [user_out(member) for member in users]


@router.post("/organization/users", status_code=status.HTTP_201_CREATED)
def create_manager(
    payload: ManagerCreatePayload,
    db: Session = Depends(get_db),
    owner: models.User = Depends(require_owner),
):
    if _email_taken(db, payload.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    manager = models.User(
        organization_id=owner.organization_id,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="manager",
    )
    db.add(manager)
    db.commit()
    return user_out(manager)


@router.delete("/organization/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_manager(user_id: int, db: Session = Depends(get_db), owner: models.User = Depends(require_owner)):
    if user_id == owner.id:
        raise HTTPException(status_code=400, detail="You can't remove your own account")
    member = (
        db.query(models.User)
        .filter(models.User.id == user_id, models.User.organization_id == owner.organization_id)
        .first()
    )
    if member is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(member)
    db.commit()
