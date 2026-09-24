import { useEffect, useState } from 'react'
import { apiGet, errorMessage, isAbort } from '../api/client'
import type { Trend } from '../types'
import { TrendChart, type ChartPoint } from './charts/TrendChart'

type Props = {
  employeeId: number
  // Changes whenever the report should re-fetch (e.g. after settings are saved).
  refreshKey: number
}

const RANGES = [7, 14, 30] as const

function pointsFor(trend: Trend, pick: (point: Trend['points'][number]) => number, gaps: boolean): ChartPoint[] {
  return trend.points.map((point) => {
    // Dates are UTC calendar days; parse at noon UTC so no timezone shifts the day.
    const date = new Date(`${point.date}T12:00:00Z`)
    return {
      label: date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', timeZone: 'UTC' }),
      fullLabel: date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', timeZone: 'UTC' }),
      value: gaps && !point.has_activity ? null : pick(point),
    }
  })
}

export function TrendPanel({ employeeId, refreshKey }: Props) {
  const [days, setDays] = useState<(typeof RANGES)[number]>(14)
  const [trend, setTrend] = useState<Trend | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setError(null)
    apiGet<Trend>(`/reports/${employeeId}/trend?days=${days}`, controller.signal)
      .then(setTrend)
      .catch((loadError: unknown) => {
        if (!isAbort(loadError)) setError(errorMessage(loadError))
      })
    return () => controller.abort()
  }, [employeeId, days, refreshKey])

  const activeDays = trend?.points.filter((point) => point.has_activity).length ?? 0

  return (
    <section className="panel trend-panel">
      <div className="panel-heading">
        <h2>Trends</h2>
        <div className="segmented-control small" role="group" aria-label="Trend range">
          {RANGES.map((range) => (
            <button
              key={range}
              type="button"
              aria-pressed={days === range}
              className={days === range ? 'active' : ''}
              onClick={() => setDays(range)}
            >
              {range} days
            </button>
          ))}
        </div>
      </div>

      {error ? <div className="error-box">Unable to load trends: {error}</div> : null}
      {!trend && !error ? <p className="muted">Loading trends…</p> : null}

      {trend ? (
        <>
          <p className="muted panel-intro">
            Activity recorded on {activeDays} of the last {trend.days} days (UTC). Days without activity are left blank.
          </p>
          <div className="charts-row">
            <TrendChart
              title="Daily productivity score"
              kind="line"
              points={pointsFor(trend, (point) => Math.round(point.average_score * 100), true)}
              max={100}
              format={(value) => `${Math.round(value)}%`}
              valueLabel="Score"
            />
            <TrendChart
              title="Productive hours per day"
              kind="column"
              points={pointsFor(trend, (point) => point.total_productive_hours, false)}
              format={(value) => (Number.isInteger(value) ? String(value) : value.toFixed(1))}
              valueLabel="Hours"
            />
          </div>
        </>
      ) : null}
    </section>
  )
}
