import type { Summary } from '../types'
import { formatScore, scoreTone, TONE_LABELS } from '../utils/format'
import { TopAppsChart } from './charts/TopAppsChart'

type Props = {
  summary: Summary
}

export function ReportView({ summary }: Props) {
  return (
    <>
      <section className="stats-grid">
        <article className="stat-card">
          <span className="label">Productivity score</span>
          <strong className={`score ${scoreTone(summary.average_score)}`}>{formatScore(summary.average_score)}</strong>
          <span className={`tone-badge ${scoreTone(summary.average_score)}`}>
            {TONE_LABELS[scoreTone(summary.average_score)]}
          </span>
          <span className="stat-hint">
            {summary.average_score === null
              ? 'No activity recorded this period'
              : `Average of ${summary.days_active} active ${summary.days_active === 1 ? 'day' : 'days'} · an estimate, not a timesheet`}
          </span>
        </article>
        <article className="stat-card">
          <span className="label">Productive hours</span>
          <strong>
            {summary.total_productive_hours}
            <span className="stat-unit">h</span>
          </strong>
        </article>
        <article className="stat-card">
          <span className="label">Idle minutes</span>
          <strong>
            {summary.total_idle_minutes}
            <span className="stat-unit">min</span>
          </strong>
        </article>
        <article className="stat-card">
          <span className="label">Logins</span>
          <strong>{summary.event_summary.login}</strong>
        </article>
      </section>

      <section className="content-grid">
        <article className="panel">
          <h2>Event summary</h2>
          <ul className="metric-list">
            <li><span>App focus</span><strong>{summary.event_summary.app_focus}</strong></li>
            <li><span>Browser tabs</span><strong>{summary.event_summary.browser_tab}</strong></li>
            <li><span>Idle starts</span><strong>{summary.event_summary.idle_start}</strong></li>
            <li><span>Outlook activity</span><strong>{summary.event_summary.outlook_activity}</strong></li>
          </ul>
        </article>

        <article className="panel">
          <h2>Most used applications</h2>
          <TopAppsChart apps={summary.top_apps} weights={summary.app_weights ?? {}} />
        </article>
      </section>
    </>
  )
}
