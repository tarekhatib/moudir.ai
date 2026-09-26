from datetime import date, datetime

from app import scoring


class Log:
    def __init__(self, event_type: str, when: datetime, app_name: str | None = None):
        self.event_type = event_type
        self.timestamp = when
        self.detail = {"app_name": app_name} if app_name else {}


def _busy_day(day: int, focus: int, idle: int = 0) -> list[Log]:
    when = datetime(2026, 9, day, 10)
    return (
        [Log("login", when)]
        + [Log("app_focus", when, "Code") for _ in range(focus)]
        + [Log("browser_tab", when) for _ in range(15)]
        + [Log("idle_start", when) for _ in range(idle)]
    )


def test_no_activity_has_no_score():
    summary = scoring.summarize([], {})
    assert summary["average_score"] is None
    assert summary["days_active"] == 0
    assert scoring.score_day([], {}) is None


def test_period_score_is_average_of_active_days():
    perfect = _busy_day(1, focus=20)          # 1.0
    half_focus = _busy_day(2, focus=10)       # 0.4 * 0.5 + 0.6 = 0.8
    summary = scoring.summarize(perfect + half_focus, {})
    assert summary["days_active"] == 2
    assert abs(summary["average_score"] - 0.9) < 1e-9
    # Totals still add up across the whole period.
    assert summary["event_summary"]["app_focus"] == 30
    assert summary["total_productive_hours"] == 3.0


def test_many_active_days_do_not_saturate_idle_penalty():
    # Two idle events per day is a small daily penalty; it must not add up to zero over a month.
    logs = [log for day in range(1, 21) for log in _busy_day(day, focus=20, idle=2)]
    assert abs(scoring.summarize(logs, {})["average_score"] - (0.8 + 0.2 * 0.7)) < 1e-9


def test_custom_category_weights_apply():
    logs = _busy_day(1, focus=0)
    only_app_usage = {"app_usage": 1.0, "browser": 0.0, "punctuality": 0.0, "idle": 0.0}
    assert scoring.score_day(logs, only_app_usage) == 0.0


def test_period_bounds():
    wednesday = date(2026, 9, 23)
    assert scoring.period_bounds("daily", wednesday) == (datetime(2026, 9, 23), datetime(2026, 9, 24))
    assert scoring.period_bounds("weekly", wednesday) == (datetime(2026, 9, 21), datetime(2026, 9, 28))
    assert scoring.period_bounds("monthly", date(2026, 12, 5)) == (datetime(2026, 12, 1), datetime(2027, 1, 1))
