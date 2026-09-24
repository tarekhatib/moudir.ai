import type { TopApp } from '../../types'

type Props = {
  apps: TopApp[]
  weights: Record<string, string | number>
}

// Horizontal bars: app names are long, so they read better on the left than under columns.
export function TopAppsChart({ apps, weights }: Props) {
  if (apps.length === 0) {
    return <p className="muted">No application activity recorded in this period.</p>
  }

  const max = Math.max(...apps.map((app) => app.focus_events))
  // Software weights are keyed by whatever the manager typed, so match case-insensitively.
  const weightFor = (name: string) =>
    Object.entries(weights).find(([key]) => key.toLowerCase() === name.toLowerCase())?.[1]

  return (
    <ul className="hbar-list" aria-label="Most used applications by focus events">
      {apps.map((app) => {
        const weight = weightFor(app.app_name)
        return (
          <li key={app.app_name} className="hbar-row" title={`${app.app_name}: ${app.focus_events} focus events`}>
            <span className="hbar-name">
              {app.app_name}
              {weight !== undefined ? <span className={`weight-tag ${String(weight)}`}>{String(weight)}</span> : null}
            </span>
            <span className="hbar-track">
              <span className="hbar-fill" style={{ width: `${(app.focus_events / max) * 100}%` }} />
            </span>
            <span className="hbar-value">{app.focus_events}</span>
          </li>
        )
      })}
    </ul>
  )
}
