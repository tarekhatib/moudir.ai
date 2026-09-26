from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import models

EVENT_LABELS = {
    "app_focus": "App focus",
    "browser_tab": "Browser tabs",
    "idle_start": "Idle starts",
    "login": "Logins",
    "outlook_activity": "Outlook activity",
}


def _table(rows: list[list[str]]) -> Table:
    table = Table(rows, colWidths=[70 * mm, 90 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#444444")),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def render_report_pdf(employee: models.Employee, report: dict) -> bytes:
    styles = getSampleStyleSheet()
    score = report["average_score"]
    period = report["period"]

    story = [
        Paragraph("Moudir.ai productivity report", styles["Title"]),
        Paragraph(escape(employee.organization.name), styles["Normal"]),
        Spacer(1, 8 * mm),
        _table(
            [
                ["Employee", escape(employee.name)],
                ["Role", escape(employee.role or "—")],
                ["Period", f"{period.capitalize()} ({report['period_start']} to {report['period_end']}, UTC)"],
                ["Average score", "No activity recorded" if score is None else f"{score * 100:.0f}%"],
                ["Days with activity", str(report["days_active"])],
                ["Productive hours (est.)", f"{report['total_productive_hours']:g}"],
                ["Idle minutes (est.)", str(report["total_idle_minutes"])],
            ]
        ),
        Spacer(1, 6 * mm),
        Paragraph("Activity", styles["Heading2"]),
        _table([[label, str(report["event_summary"].get(key, 0))] for key, label in EVENT_LABELS.items()]),
    ]

    if report["top_apps"]:
        story += [
            Spacer(1, 6 * mm),
            Paragraph("Most-used applications", styles["Heading2"]),
            _table([[escape(app["app_name"]), f"{app['focus_events']} focus events"] for app in report["top_apps"]]),
        ]

    story += [
        Spacer(1, 8 * mm),
        Paragraph(
            "Scores and hours are heuristic estimates from activity events, not timesheets.",
            styles["Italic"],
        ),
    ]

    buffer = BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, title=f"{employee.name} — {period} report").build(story)
    return buffer.getvalue()
