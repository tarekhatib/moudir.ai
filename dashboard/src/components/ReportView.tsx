import type { Summary } from '../types'
import { scoreTone } from '../utils/format'
import { TopAppsChart } from './charts/TopAppsChart'

type Props = {
  summary: Summary
}

export function ReportView({ summary }: Props) {
  const percent = Math.round(summary.average_score * 100)

  return (
    <>
      <section className="stats-grid">
        <article className="stat-card">
          <span className="label">Productivity score</span>
          <strong className={`score ${scoreTone(summary.average_score)}`}>{percent}%</strong>
          <span className="stat-hint">Estimate based on activity, not a timesheet</span>
        </article>
        <article className="stat-card">
          <span className="label">Productive hours</span>
          <strong>{summary.total_productive_hours}</strong>
        </article>
        <article className="stat-card">
          <span className="label">Idle minutes</span>
          <strong>{summary.total_idle_minutes}</strong>
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
          <TopAppsChart apps={summary.top_apps ?? []} weights={summary.app_weights ?? {}} />
        </article>
      </section>
    </>
  )
}
