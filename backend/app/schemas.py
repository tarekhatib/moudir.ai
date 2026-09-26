"""Request bodies. Validation mirrors dashboard/src/utils/{validation,config}.ts."""

import re
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
CATEGORY_KEYS = {"app_usage", "browser", "punctuality", "idle"}
DAY_KEYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_PATTERN.match(value):
        raise ValueError("enter a valid email address")
    return value


# --- Auth -------------------------------------------------------------------


class _AccountPayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(max_length=320)
    password: str = Field(min_length=10, max_length=200)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _email(value)


class SignupPayload(_AccountPayload):
    organization_name: str = Field(min_length=1, max_length=200)

    @field_validator("organization_name")
    @classmethod
    def strip_organization_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("organization name must not be empty")
        return value


class ManagerCreatePayload(_AccountPayload):
    pass


class LoginPayload(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class PasswordChangePayload(BaseModel):
    current_password: str = Field(max_length=200)
    new_password: str = Field(min_length=10, max_length=200)


# --- Employees & config -----------------------------------------------------


class EmployeeProfilePayload(BaseModel):
    name: str = Field(max_length=200)
    role: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    job_description: str | None = Field(default=None, max_length=2000)
    role_tag: str | None = Field(default=None, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty")
        return value

    @field_validator("role", "email", "job_description", "role_tag", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        return _optional_text(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return None if value is None else _email(value)


class ConfigPayload(BaseModel):
    job_description: str | None = Field(default=None, max_length=2000)
    role_tag: str | None = Field(default=None, max_length=100)
    software_weights: dict[str, Literal["high", "medium", "low"]] = Field(default_factory=dict, max_length=200)
    category_weights: dict[str, float] = Field(default_factory=dict)
    schedule: dict[str, list[tuple[str, str]]] = Field(default_factory=dict)
    min_productive_hours: float = Field(default=6.0, ge=0, le=24)
    max_idle_minutes: int = Field(default=60, ge=0, le=1440)

    @field_validator("job_description", "role_tag", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: str | None) -> str | None:
        return _optional_text(value)

    @field_validator("software_weights")
    @classmethod
    def validate_software_weights(cls, value: dict) -> dict:
        cleaned = {}
        for name, level in value.items():
            name = name.strip()
            if not name or len(name) > 200:
                raise ValueError("app names must be 1-200 characters")
            if name.lower() in {existing.lower() for existing in cleaned}:
                raise ValueError("each app can only be listed once")
            cleaned[name] = level
        return cleaned

    @field_validator("category_weights")
    @classmethod
    def validate_category_weights(cls, value: dict) -> dict:
        if not value:
            return value
        if set(value) - CATEGORY_KEYS:
            raise ValueError(f"category weights must use keys {sorted(CATEGORY_KEYS)}")
        if any(weight < 0 or weight > 1 for weight in value.values()):
            raise ValueError("each category weight must be between 0 and 1")
        if abs(sum(value.values()) - 1.0) > 0.01:
            raise ValueError("category weights must add up to 1")
        return value

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, value: dict) -> dict:
        if set(value) - DAY_KEYS:
            raise ValueError(f"schedule days must be one of {sorted(DAY_KEYS)}")
        for day, ranges in value.items():
            ordered = sorted(ranges)
            for start, end in ordered:
                if not TIME_PATTERN.match(start) or not TIME_PATTERN.match(end):
                    raise ValueError(f"{day}: times must be HH:MM")
                if start >= end:
                    raise ValueError(f"{day}: end time must be after start time")
            if any(ordered[i][0] < ordered[i - 1][1] for i in range(1, len(ordered))):
                raise ValueError(f"{day}: time blocks overlap")
            value[day] = [list(r) for r in ordered]
        return value


# --- Agent ingestion --------------------------------------------------------

EventType = Literal["login", "logout", "app_focus", "idle_start", "idle_end", "browser_tab", "outlook_activity"]


class ActivityEvent(BaseModel):
    # Optional and ignored beyond a consistency check: the agent token identifies the employee.
    employee_id: int | None = None
    event_type: EventType
    timestamp: datetime
    detail: dict = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def to_naive_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    @model_validator(mode="after")
    def limit_detail(self):
        # Keep only short string/number fields; drop anything else the agent might send.
        self.detail = {
            str(k)[:64]: (v[:500] if isinstance(v, str) else v)
            for k, v in list(self.detail.items())[:10]
            if isinstance(v, (str, int, float, bool))
        }
        return self
