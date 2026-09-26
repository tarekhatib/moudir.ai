"""Productivity scoring. See docs/SCORING.md for the formulas."""

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from . import models

PERIODS = ("daily", "weekly", "monthly")
EVENT_TYPES = ("app_focus", "browser_tab", "idle_start", "login", "outlook_activity")
DEFAULT_CATEGORY_WEIGHTS = {"app_usage": 0.4, "browser": 0.2, "punctuality": 0.2, "idle": 0.2}


def period_bounds(period: str, today: date | None = None) -> tuple[datetime, datetime]:
    today = today or models.utcnow().date()
    if period == "daily":
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)
    elif period == "weekly":
        start = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
        end = start + timedelta(days=7)
    elif period == "monthly":
        start = datetime(today.year, today.month, 1)
        end = datetime(start.year + 1, 1, 1) if start.month == 12 else datetime(start.year, start.month + 1, 1)
    else:
        raise ValueError(f"unknown period: {period}")
    return start, end


def query_logs(db: Session, employee_id: int, start: datetime, end: datetime) -> list[models.ActivityLog]:
    return (
        db.query(models.ActivityLog)
        .filter(
            models.ActivityLog.employee_id == employee_id,
            models.ActivityLog.timestamp >= start,
            models.ActivityLog.timestamp < end,
        )
        .all()
    )


def category_weights_for(employee: models.Employee) -> dict:
    return (employee.config.category_weights if employee.config else None) or {}


def _event_summary(logs) -> dict:
    summary = dict.fromkeys(EVENT_TYPES, 0)
    for log in logs:
        if log.event_type in summary:
            summary[log.event_type] += 1
    return summary


def score_day(logs, category_weights: dict) -> float | None:
    """Score one day's events in [0, 1]; None when there was no activity to score."""
    if not logs:
        return None
    counts = _event_summary(logs)
    weights = {**DEFAULT_CATEGORY_WEIGHTS, **(category_weights or {})}

    app_usage_score = min(1.0, counts["app_focus"] / 20.0)
    browser_score = min(1.0, counts["browser_tab"] / 15.0)
    punctuality_score = 1.0 if counts["login"] else 0.0
    idle_score = max(0.0, 1.0 - counts["idle_start"] * 0.15)

    total = (
        app_usage_score * float(weights["app_usage"])
        + browser_score * float(weights["browser"])
        + punctuality_score * float(weights["punctuality"])
        + idle_score * float(weights["idle"])
    )
    return max(0.0, min(1.0, total))


def summarize(logs, category_weights: dict) -> dict:
    """Score a span of events: the average of its daily scores over days with activity."""
    by_day: dict[date, list] = {}
    for log in logs:
        by_day.setdefault(log.timestamp.date(), []).append(log)
    day_scores = [score_day(day_logs, category_weights) for day_logs in by_day.values()]
    counts = _event_summary(logs)

    return {
        "average_score": sum(day_scores) / len(day_scores) if day_scores else None,
        "days_active": len(day_scores),
        "total_productive_hours": round(counts["app_focus"] * 0.1, 2),
        "total_idle_minutes": counts["idle_start"] * 15,
        "event_summary": counts,
    }


def top_apps(logs, limit: int = 8) -> list[dict]:
    counts: dict[str, int] = {}
    for log in logs:
        if log.event_type != "app_focus":
            continue
        name = ((log.detail or {}).get("app_name") or "").strip() or "Unknown"
        counts[name] = counts.get(name, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))
    return [{"app_name": name, "focus_events": count} for name, count in ranked[:limit]]


def period_report(db: Session, employee: models.Employee, period: str) -> dict:
    start, end = period_bounds(period)
    logs = query_logs(db, employee.id, start, end)
    return {
        "employee_id": employee.id,
        "period": period,
        "period_start": start.date().isoformat(),
        "period_end": (end - timedelta(days=1)).date().isoformat(),
        **summarize(logs, category_weights_for(employee)),
        "app_weights": (employee.config.software_weights if employee.config else None) or {},
        "top_apps": top_apps(logs),
    }


def daily_trend(db: Session, employee: models.Employee, days: int) -> list[dict]:
    today = datetime.combine(models.utcnow().date(), datetime.min.time())
    start = today - timedelta(days=days - 1)
    logs = query_logs(db, employee.id, start, today + timedelta(days=1))
    weights = category_weights_for(employee)

    by_day: dict[date, list] = {}
    for log in logs:
        by_day.setdefault(log.timestamp.date(), []).append(log)

    points = []
    for offset in range(days):
        day = (start + timedelta(days=offset)).date()
        day_logs = by_day.get(day, [])
        summary = summarize(day_logs, weights)
        del summary["days_active"]
        points.append({"date": day.isoformat(), "has_activity": bool(day_logs), **summary})
    return points
