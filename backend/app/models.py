"""
Draft schema — finalize together on Day 2, adjust field names/types as
the real config JSON shape and agent payload get nailed down.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String)
    job_description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    config = relationship("EmployeeConfig", back_populates="employee", uselist=False)
    activity_logs = relationship("ActivityLog", back_populates="employee")
    daily_scores = relationship("DailyScore", back_populates="employee")


class EmployeeConfig(Base):
    __tablename__ = "configs"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True)

    software_weights = Column(JSON)       # {"vscode": "high", "facebook.com": "low", ...}
    category_weights = Column(JSON)       # {"app_usage": 0.4, "browser": 0.2, ...}
    schedule = Column(JSON)               # {"mon": ["09:00", "17:00"], ...}
    min_productive_hours = Column(Float)
    max_idle_minutes = Column(Float)

    employee = relationship("Employee", back_populates="config")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String)   # login, logout, app_focus, idle, browser_tab, outlook
    detail = Column(JSON)         # flexible payload per event_type

    employee = relationship("Employee", back_populates="activity_logs")


class DailyScore(Base):
    __tablename__ = "daily_scores"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(DateTime)
    category_scores = Column(JSON)   # per-category breakdown
    total_score = Column(Float)

    employee = relationship("Employee", back_populates="daily_scores")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    period_type = Column(String)   # daily, weekly, monthly
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    summary = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)
