# Moudir.ai Scoring Heuristics & Algorithm

This document details the productivity scoring algorithm and metrics computation implemented in [`backend/app/scoring.py`](../backend/app/scoring.py).

---

## Important Notice: Pilot Heuristics

> [!IMPORTANT]
> **Productive hours** and **productivity scores** computed by Moudir.ai are **rule-based pilot heuristics** derived from endpoint activity-event frequency. They do **not** represent verified timesheet hours, payroll records, or exhaustive employee output measurements.

The system measures digital presence and active application context switches, designed to give managers directional signals rather than legal or compensation-grade accounting.

---

## Time Windows & Aggregation

When querying `GET /reports/{employee_id}?period=<period>`, the reporting engine queries raw activity events within a dynamic timeframe calculated from UTC:

| Period | Start Time | End Time |
| :--- | :--- | :--- |
| **`daily`** | Midnight (`00:00:00 UTC`) of the current day | Midnight of the following day (+24h) |
| **`weekly`** | Midnight (`00:00:00 UTC`) of the current week's Monday | Start of next Monday (+7 days) |
| **`monthly`** | Midnight (`00:00:00 UTC`) of the 1st day of the current month | Start of the 1st day of next month |

---

## Scoring Model Breakdown

Scores are computed **per UTC day**. Each day with at least one event gets a score in `[0.0, 1.0]`:

$$\text{Day Score} = \min\left(1.0, \max\left(0.0, \sum w_i \cdot s_i\right)\right)$$

A period's `average_score` (daily, weekly or monthly) is the **mean of the day scores on days with
activity**. Days without any events are left out rather than counted as zero, and `days_active`
says how many days were averaged. If the period has no activity at all, `average_score` is
`null` and the dashboard shows "No data" instead of a score.

Scoring per day keeps the thresholds below meaningful at every period length: 20 focus events is
a full day of app usage, not a full month of it, and two short idle periods a day don't add up to
a zero idle score over a month.

### 1. Sub-Score Formulas

1. **App Usage Score (`app_usage_score`)**:
   $$\text{app\_usage\_score} = \min\left(1.0, \frac{\text{count}(\text{app\_focus})}{20}\right)$$
   - *Rationale*: Measures active engagement with desktop productivity applications. Reaches maximum (1.0) at 20 or more focus events in the day.

2. **Browser Score (`browser_score`)**:
   $$\text{browser\_score} = \min\left(1.0, \frac{\text{count}(\text{browser\_tab})}{15}\right)$$
   - *Rationale*: Measures research and web-based tool engagement. Reaches maximum (1.0) at 15 or more recorded tab context switches in the day.

3. **Punctuality Score (`punctuality_score`)**:
   $$\text{punctuality\_score} = \begin{cases} 1.0 & \text{if } \text{count}(\text{login}) > 0 \\ 0.0 & \text{otherwise} \end{cases}$$
   - *Rationale*: Indicates whether an employee logged in and initialized an active session that day.

4. **Idle Score (`idle_score`)**:
   $$\text{idle\_score} = \max\left(0.0, 1.0 - (\text{count}(\text{idle\_start}) \times 0.15)\right)$$
   - *Rationale*: Starts at full score (1.0) and penalizes long idle periods by deducting 0.15 for every recorded idle trigger event.

---

## Default Category Weights

Unless overridden in the employee's configuration, the scoring engine applies the following baseline weights:

| Category | Default Weight | Key in Config |
| :--- | :--- | :--- |
| **App Usage** | `0.40` (40%) | `app_usage` |
| **Browser Activity** | `0.20` (20%) | `browser` |
| **Punctuality** | `0.20` (20%) | `punctuality` |
| **Idle Behavior** | `0.20` (20%) | `idle` |
| **Sum** | `1.00` (100%) | |

---

## Heuristic Metrics Computation

In addition to the composite score, the backend calculates:

- **Estimated Productive Hours**:
  $$\text{total\_productive\_hours} = \text{round}(\text{count}(\text{app\_focus}) \times 0.1, 2)$$
  *(Assumes an average productive focus block of 6 minutes per event)*

- **Estimated Idle Minutes**:
  $$\text{total\_idle\_minutes} = \text{count}(\text{idle\_start}) \times 15$$
  *(Assumes an average idle duration of 15 minutes per trigger)*

- **Event Distribution**:
  Raw event counts for `app_focus`, `browser_tab`, `idle_start`, `login`, and `outlook_activity`.

---

## Configuration & Customization

Scoring behavior can be customized per employee via `POST /config/{employee_id}`:

```json
{
  "category_weights": {
    "app_usage": 0.50,
    "browser": 0.20,
    "punctuality": 0.15,
    "idle": 0.15
  },
  "software_weights": {
    "VS Code": "high",
    "Slack": "medium",
    "YouTube": "low"
  },
  "schedule": {
    "mon": [["09:00", "13:00"], ["14:00", "18:00"]],
    "tue": [["09:00", "13:00"], ["14:00", "18:00"]]
  },
  "min_productive_hours": 6.0,
  "max_idle_minutes": 60
}
```
