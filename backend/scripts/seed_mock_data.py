"""Seed a demo organization with employees and ~5 weeks of activity.

Usage (from backend/, after `alembic upgrade head`):
    python scripts/seed_mock_data.py            # create the demo organization (skips if present)
    python scripts/seed_mock_data.py --reset    # delete it and seed again
    python scripts/seed_mock_data.py --remove   # delete it only

Sign in to the dashboard with DEMO_EMAIL and the password printed at the end
(override it with the DEMO_PASSWORD environment variable). Only the demo
organization is touched. Refuses to run when ENVIRONMENT=production.
"""

import argparse
import os
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import models  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.settings import get_settings  # noqa: E402

MOCK_EMAIL_DOMAIN = "@demo.moudir.example"
DEMO_ORGANIZATION = "Moudir Demo"
DEMO_EMAIL = "demo" + MOCK_EMAIL_DOMAIN
DEFAULT_DEMO_PASSWORD = "moudir-demo-password"
HISTORY_DAYS = 35

STANDARD_WEEK = {
    day: [["09:00", "13:00"], ["14:00", "18:00"]] for day in ("mon", "tue", "wed", "thu", "fri")
}

# Each persona drives how its generated days look.
#   apps:        (app_name, window titles, relative frequency)
#   focus:       (min, max) app_focus events on a normal workday
#   idle:        (min, max) idle_start events per workday
#   start_hour:  typical login hour (UTC), jittered
#   trend:       daily multiplier drift across the history (+ improving, - declining)
#   weekend:     probability of working on a weekend day
#   absences:    days-ago offsets with no activity (sick/leave)
PERSONAS = [
    {
        "name": "Jad Karam",
        "role": "Lead Software Engineer",
        "role_tag": "engineering",
        "job_description": "Architecture design and full-stack backend development",
        "software_weights": {"VS Code": "high", "Terminal": "high", "Chrome": "medium", "Slack": "medium", "YouTube": "low"},
        "category_weights": {"app_usage": 0.5, "browser": 0.15, "punctuality": 0.15, "idle": 0.2},
        "apps": [
            ("VS Code", ["app/main.py", "models.py", "test_api.py", "README.md"], 10),
            ("Terminal", ["zsh — pytest", "zsh — git", "uvicorn app.main:app"], 5),
            ("Chrome", ["GitHub — Pull request #42", "FastAPI docs", "Stack Overflow"], 4),
            ("Slack", ["#engineering", "#incidents", "DM — Maya"], 3),
            ("YouTube", ["Conference talk"], 1),
        ],
        "focus": (55, 75), "idle": (0, 2), "start_hour": 8.75, "trend": 0.0, "weekend": 0.15,
        "absences": [],
    },
    {
        "name": "Maya Haddad",
        "role": "Product Designer",
        "role_tag": "design",
        "job_description": "UX research, prototyping and design system maintenance",
        "software_weights": {"Figma": "high", "Notion": "medium", "Chrome": "medium", "Slack": "medium"},
        "category_weights": {"app_usage": 0.45, "browser": 0.2, "punctuality": 0.15, "idle": 0.2},
        "apps": [
            ("Figma", ["Dashboard redesign", "Design system — Components", "Onboarding flow"], 9),
            ("Notion", ["Research notes", "Sprint planning"], 3),
            ("Chrome", ["Dribbble", "Material Design guidelines", "User interview recording"], 4),
            ("Slack", ["#design", "#product"], 3),
            ("Zoom", ["Usability session"], 1),
        ],
        "focus": (40, 60), "idle": (1, 3), "start_hour": 9.5, "trend": 0.012, "weekend": 0.05,
        "absences": [12],
    },
    {
        "name": "Omar Farouk",
        "role": "Account Executive",
        "role_tag": "sales",
        "job_description": "Manages enterprise accounts across the MENA region",
        "software_weights": {"Outlook": "high", "Salesforce": "high", "Zoom": "high", "Excel": "medium", "LinkedIn": "medium"},
        "category_weights": {"app_usage": 0.35, "browser": 0.25, "punctuality": 0.2, "idle": 0.2},
        "apps": [
            ("Outlook", ["Inbox", "RE: Renewal proposal", "Calendar"], 8),
            ("Chrome", ["Salesforce — Opportunities", "LinkedIn Sales Navigator", "Company news"], 6),
            ("Zoom", ["Client call — Acme", "Pipeline review"], 4),
            ("Excel", ["Q3 forecast.xlsx"], 2),
            ("Microsoft Teams", ["Sales team"], 2),
        ],
        "focus": (35, 55), "idle": (1, 4), "start_hour": 9.0, "trend": 0.0, "weekend": 0.0,
        "absences": [5, 6],
    },
    {
        "name": "Lina Sabbagh",
        "role": "Data Analyst",
        "role_tag": "analytics",
        "job_description": "Builds KPI reports and ad-hoc analysis for leadership",
        "software_weights": {"Excel": "high", "Power BI": "high", "PyCharm": "high", "Chrome": "medium", "Slack": "medium"},
        "category_weights": {"app_usage": 0.45, "browser": 0.15, "punctuality": 0.2, "idle": 0.2},
        "apps": [
            ("Power BI", ["Revenue dashboard", "Churn model"], 6),
            ("Excel", ["Monthly KPIs.xlsx", "Raw export.csv"], 6),
            ("PyCharm", ["cohort_analysis.py", "etl.py"], 5),
            ("Chrome", ["pandas documentation", "BigQuery console"], 3),
            ("Slack", ["#data", "#leadership"], 2),
        ],
        "focus": (30, 50), "idle": (1, 3), "start_hour": 9.25, "trend": 0.02, "weekend": 0.0,
        "absences": [],
    },
    {
        "name": "Karim Nassar",
        "role": "Customer Support Specialist",
        "role_tag": "support",
        "job_description": "Handles tier-1 tickets and customer escalations",
        "software_weights": {"Zendesk": "high", "Outlook": "medium", "Microsoft Teams": "medium", "Facebook": "low"},
        "category_weights": {"app_usage": 0.4, "browser": 0.2, "punctuality": 0.2, "idle": 0.2},
        "apps": [
            ("Chrome", ["Zendesk — Ticket #8812", "Zendesk — Views", "Help center"], 8),
            ("Outlook", ["Inbox", "Escalations"], 4),
            ("Microsoft Teams", ["Support shift", "DM — Team lead"], 3),
            ("Chrome", ["Facebook", "News"], 2),
        ],
        "focus": (14, 28), "idle": (4, 7), "start_hour": 9.4, "trend": 0.0, "weekend": 0.1,
        "absences": [20],
    },
    {
        "name": "Sara Mansour",
        "role": "HR Coordinator",
        "role_tag": "hr",
        "job_description": "Onboarding, payroll coordination and employee relations",
        "software_weights": {"Outlook": "high", "Workday": "high", "Word": "medium", "Microsoft Teams": "medium"},
        "category_weights": {"app_usage": 0.4, "browser": 0.2, "punctuality": 0.2, "idle": 0.2},
        "apps": [
            ("Outlook", ["Inbox", "New hire paperwork", "Calendar"], 7),
            ("Chrome", ["Workday — Payroll", "Workday — Onboarding"], 5),
            ("Word", ["Offer letter template.docx", "Policy update.docx"], 3),
            ("Microsoft Teams", ["HR team", "1:1 — Manager"], 3),
        ],
        "focus": (40, 55), "idle": (2, 4), "start_hour": 8.9, "trend": -0.018, "weekend": 0.0,
        "absences": [],
    },
]


# The original pilot employees, re-created in the demo organization.
PERSONAS += [
    {
        "name": "Carla Jaffal",
        "role": "AI Developer",
        "role_tag": "engineering",
        "job_description": "Builds and evaluates the ML models behind Moudir",
        "software_weights": {"PyCharm": "high", "Jupyter": "high", "Chrome": "medium", "Slack": "medium"},
        "category_weights": {"app_usage": 0.4, "browser": 0.2, "punctuality": 0.2, "idle": 0.2},
        "apps": [
            ("PyCharm", ["train.py", "agent/main.py", "embeddings.py"], 8),
            ("Jupyter", ["eval_notebook.ipynb", "data_exploration.ipynb"], 5),
            ("Chrome", ["Hugging Face — Models", "arXiv — Attention paper", "Claude API docs"], 5),
            ("Slack", ["#ai-team", "#engineering"], 3),
            ("Terminal", ["python train.py", "nvidia-smi"], 2),
        ],
        "focus": (50, 70), "idle": (0, 2), "start_hour": 8.8, "trend": 0.005, "weekend": 0.1,
        "absences": [],
    },
    {
        "name": "Tarek Al Khatib",
        "role": "Senior Engineer",
        "role_tag": "engineering",
        "job_description": "Dashboard and backend development",
        "software_weights": {"VS Code": "high", "Terminal": "high", "Chrome": "medium", "Slack": "medium", "Figma": "medium"},
        "category_weights": {"app_usage": 0.4, "browser": 0.2, "punctuality": 0.2, "idle": 0.2},
        "apps": [
            ("VS Code", ["dashboard/src/App.tsx", "backend/app/main.py", "TeamOverview.tsx"], 10),
            ("Terminal", ["npm run dev", "pytest", "git"], 5),
            ("Chrome", ["localhost:5173 — Moudir.ai", "React docs", "GitHub — Pull requests"], 5),
            ("Figma", ["Moudir dashboard"], 2),
            ("Slack", ["#engineering", "DM — Carla"], 3),
        ],
        "focus": (60, 80), "idle": (0, 1), "start_hour": 8.5, "trend": 0.0, "weekend": 0.25,
        "absences": [],
    },
    {
        "name": "Alex Rivers",
        "role": "Lead Engineer",
        "role_tag": "engineering",
        "job_description": "Architecture design and full-stack backend development",
        "software_weights": {"VS Code": "high", "Terminal": "high", "Chrome": "medium", "Slack": "medium", "Jira": "medium"},
        "category_weights": {"app_usage": 0.4, "browser": 0.2, "punctuality": 0.2, "idle": 0.2},
        "apps": [
            ("VS Code", ["app/main.py", "models.py", "test_api.py"], 9),
            ("Terminal", ["zsh — pytest", "uvicorn app.main:app"], 4),
            ("Chrome", ["Jira — Sprint board", "FastAPI docs", "GitHub — Code review"], 5),
            ("Slack", ["#engineering", "#standup"], 3),
            ("Zoom", ["Architecture review"], 1),
        ],
        "focus": (50, 68), "idle": (0, 2), "start_hour": 9.0, "trend": 0.0, "weekend": 0.05,
        "absences": [15],
    },
]


def _email_for(name: str) -> str:
    return name.lower().replace(" ", ".") + MOCK_EMAIL_DOMAIN


def _weighted_app(rng: random.Random, apps):
    return rng.choices(apps, weights=[weight for _, _, weight in apps], k=1)[0]


def _day_events(rng: random.Random, persona: dict, employee_id: int, day: date, days_ago: int, now: datetime):
    """Generate one day's events for a persona, capped at `now` for today."""
    is_today = days_ago == 0
    is_weekend = day.weekday() >= 5
    if days_ago in persona["absences"]:
        return []
    if is_weekend and not is_today and rng.random() >= persona["weekend"]:
        return []

    # Trend drifts older days away from the persona's current level.
    level = max(0.3, 1.0 - persona["trend"] * days_ago)
    level *= rng.uniform(0.8, 1.1)
    if is_weekend and not is_today:
        level *= 0.3

    day_start = datetime.combine(day, datetime.min.time())
    login = day_start + timedelta(hours=persona["start_hour"] + rng.gauss(0, 0.3))
    logout = login + timedelta(hours=rng.uniform(7.5, 9.0) if not (is_weekend and not is_today) else rng.uniform(1.5, 3))
    if is_today:
        # Keep today's data in the past so the daily view is populated whenever the seed runs.
        span = min(logout - login, now - day_start - timedelta(minutes=5))
        if span < timedelta(hours=2):
            login = max(day_start, now - timedelta(hours=6))
            span = now - login - timedelta(minutes=1)
        logout = login + span
    work_seconds = max(60.0, (logout - login).total_seconds())

    def at(fraction: float) -> datetime:
        return login + timedelta(seconds=work_seconds * fraction)

    events = [(login, "login", {})]

    focus_count = int(rng.randint(*persona["focus"]) * level)
    if is_today:
        focus_count = int(focus_count * min(1.0, work_seconds / (8 * 3600)))
    for fraction in sorted(rng.random() for _ in range(focus_count)):
        app_name, titles, _ = _weighted_app(rng, persona["apps"])
        title = rng.choice(titles)
        ts = at(fraction)
        events.append((ts, "app_focus", {"app_name": app_name, "window_title": title}))
        if app_name == "Chrome":
            events.append((ts + timedelta(seconds=1), "browser_tab", {"tab_title": title}))
        if app_name == "Outlook":
            events.append((ts + timedelta(seconds=1), "outlook_activity", {"activity_type": "window_focused"}))

    idle_count = max(0, int(round(rng.randint(*persona["idle"]) * (2 - level) ** 2)))
    for _ in range(idle_count):
        start = at(rng.uniform(0.1, 0.9))
        duration = rng.randint(3, 25) * 60
        events.append((start, "idle_start", {}))
        events.append((start + timedelta(seconds=duration), "idle_end", {"duration_seconds": duration}))

    if not is_today:
        events.append((logout, "logout", {}))

    return [
        models.ActivityLog(employee_id=employee_id, event_type=event_type, timestamp=ts, detail=detail)
        for ts, event_type, detail in events
        if ts <= now
    ]


def remove_mock_data(db) -> bool:
    owner = db.query(models.User).filter(models.User.email == DEMO_EMAIL).first()
    if owner is None:
        return False
    organization = owner.organization
    employee_ids = [employee.id for employee in organization.employees]
    # Bulk-delete activity first; the ORM cascade would load every row.
    db.query(models.ActivityLog).filter(models.ActivityLog.employee_id.in_(employee_ids)).delete(
        synchronize_session=False
    )
    db.delete(organization)
    db.commit()
    return True


def seed(db, password: str) -> tuple[int, int] | None:
    if db.query(models.User).filter(models.User.email == DEMO_EMAIL).first():
        return None

    now = models.utcnow()
    today = now.date()
    rng = random.Random(today.toordinal())
    organization = models.Organization(name=DEMO_ORGANIZATION)
    db.add(organization)
    db.add(
        models.User(
            organization=organization,
            name="Demo Manager",
            email=DEMO_EMAIL,
            password_hash=hash_password(password),
            role="owner",
        )
    )

    event_count = 0
    for persona in PERSONAS:
        employee = models.Employee(
            organization=organization,
            name=persona["name"],
            role=persona["role"],
            email=_email_for(persona["name"]),
            config=models.Config(
                job_description=persona["job_description"],
                role_tag=persona["role_tag"],
                software_weights=persona["software_weights"],
                category_weights=persona["category_weights"],
                schedule=STANDARD_WEEK,
                min_productive_hours=6.0,
                max_idle_minutes=60,
            ),
        )
        db.add(employee)
        db.flush()

        for days_ago in range(HISTORY_DAYS - 1, -1, -1):
            day = today - timedelta(days=days_ago)
            logs = _day_events(rng, persona, employee.id, day, days_ago, now)
            db.add_all(logs)
            event_count += len(logs)

    db.commit()
    return len(PERSONAS), event_count


def main():
    parser = argparse.ArgumentParser(description="Seed Moudir.ai with a demo organization and activity.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--reset", action="store_true", help="delete the demo organization before seeding")
    group.add_argument("--remove", action="store_true", help="delete the demo organization and exit")
    args = parser.parse_args()

    if get_settings().is_production:
        sys.exit("Refusing to seed demo data with ENVIRONMENT=production.")

    password = os.getenv("DEMO_PASSWORD", DEFAULT_DEMO_PASSWORD)
    db = SessionLocal()
    try:
        if args.reset or args.remove:
            removed = remove_mock_data(db)
            print("Removed the demo organization." if removed else "No demo organization to remove.")
            if args.remove:
                return
        result = seed(db, password)
        if result is None:
            print("Demo organization already exists. Use --reset to regenerate it.")
            return
        employees, events = result
        print(f"Seeded {employees} demo employee(s) with {events} activity event(s) over {HISTORY_DAYS} days.")
        print(f"Sign in with {DEMO_EMAIL} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
