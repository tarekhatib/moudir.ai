from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from .database import Base


class Employee(Base):
    """Employees tracked by the system."""

    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    configs = relationship("Config", back_populates="employee")
    activity_logs = relationship("ActivityLog", back_populates="employee")
    daily_scores = relationship("DailyScore", back_populates="employee")


class Config(Base):
    """Employee configuration for scoring & tracking."""

    __tablename__ = "configs"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )

    job_description = Column(String, nullable=True)
    role_tag = Column(String, nullable=True)
    software_weights = Column(JSON, default={})
    category_weights = Column(JSON, default={})
    schedule = Column(JSON, default={})
    min_productive_hours = Column(Float, default=6.0)
    max_idle_minutes = Column(Integer, default=60)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = relationship("Employee", back_populates="configs")


class ActivityLog(Base):
    """Raw activity events from the agent."""

    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    event_type = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    detail = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="activity_logs")


class DailyScore(Base):
    """Computed daily productivity score."""

    __tablename__ = "daily_scores"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    date = Column(DateTime, nullable=False, index=True)

    score = Column(Float, nullable=False)
    category_scores = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="daily_scores")


class Report(Base):
    """Aggregated reports (weekly, monthly)."""

    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )

    period = Column(String, nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    average_score = Column(Float, nullable=False)
    total_productive_hours = Column(Float, default=0.0)
    total_idle_minutes = Column(Integer, default=0)
    event_summary = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow)
