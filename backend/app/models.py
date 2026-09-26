from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


def utcnow() -> datetime:
    """Naive UTC timestamp; every datetime in the database is naive UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Organization(Base):
    """A customer company. Every employee and manager belongs to exactly one."""

    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    """A manager who signs in to the dashboard."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(320), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    password_hash = Column(String(255), nullable=False)
    # "owner" can manage the organization's manager accounts; "manager" cannot.
    role = Column(String(20), nullable=False, default="manager")
    created_at = Column(DateTime, default=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="users")
    sessions = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")


class AuthSession(Base):
    """A signed-in dashboard session. Only a hash of the cookie token is stored."""

    __tablename__ = "auth_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")


class Employee(Base):
    """Employees tracked by the system."""

    __tablename__ = "employees"
    __table_args__ = (UniqueConstraint("organization_id", "email", name="uq_employee_org_email"),)

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    role = Column(String(200), nullable=True)
    email = Column(String(320), nullable=True)
    # SHA-256 of the desktop agent's token; the token itself is shown once and never stored.
    agent_token_hash = Column(String(64), nullable=True, unique=True, index=True)
    agent_token_created_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    organization = relationship("Organization", back_populates="employees")
    config = relationship("Config", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="employee", cascade="all, delete-orphan")


class Config(Base):
    """Employee configuration for scoring & tracking."""

    __tablename__ = "configs"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    job_description = Column(String(2000), nullable=True)
    role_tag = Column(String(100), nullable=True)
    software_weights = Column(JSON, default=dict)
    category_weights = Column(JSON, default=dict)
    schedule = Column(JSON, default=dict)
    min_productive_hours = Column(Float, default=6.0)
    max_idle_minutes = Column(Integer, default=60)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    employee = relationship("Employee", back_populates="config")


class ActivityLog(Base):
    """Raw activity events from the agent."""

    __tablename__ = "activity_logs"
    __table_args__ = (Index("ix_activity_logs_employee_timestamp", "employee_id", "timestamp"),)

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(32), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    detail = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)

    employee = relationship("Employee", back_populates="activity_logs")
