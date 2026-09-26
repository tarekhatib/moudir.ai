import { useEffect, useMemo, useState } from 'react'
import { apiGet, errorMessage, isAbort } from '../api/client'
import type { Period, TeamRow } from '../types'
import { formatScore, scoreTone, TONE_LABELS } from '../utils/format'
import { describePeriod } from '../utils/period'
import { PeriodSelector } from './PeriodSelector'

type Props = {
  period: Period
  onPeriodChange: (period: Period) => void
  onOpenEmployee: (id: number) => void
  onAddEmployee: () => void
}

type SortKey = 'name' | 'average_score' | 'total_productive_hours' | 'total_idle_minutes' | 'logins'

const COLUMNS: { key: SortKey; label: string; numeric: boolean }[] = [
  { key: 'name', label: 'Employee', numeric: false },
  { key: 'average_score', label: 'Score', numeric: true },
  { key: 'total_productive_hours', label: 'Productive hours', numeric: true },
  { key: 'total_idle_minutes', label: 'Idle minutes', numeric: true },
  { key: 'logins', label: 'Logins', numeric: true },
]

// Below this score an employee is flagged in the overview.
const ATTENTION_THRESHOLD = 0.5

function sortValue(row: TeamRow, key: SortKey): string | number | null {
  if (key === 'name') return row.name.toLowerCase()
  if (key === 'logins') return row.event_summary.login
  return row[key]
}

export function TeamOverview({ period, onPeriodChange, onOpenEmployee, onAddEmployee }: Props) {
  const [rows, setRows] = useState<TeamRow[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sort, setSort] = useState<{ key: SortKey; descending: boolean }>({ key: 'average_score', descending: true })

  useEffect(() => {
    const controller = new AbortController()
    setRows(null)
    setError(null)
    apiGet<TeamRow[]>(`/team/summary?period=${period}`, controller.signal)
      .then(setRows)
      .catch((loadError: unknown) => {
        if (!isAbort(loadError)) setError(errorMessage(loadError))
      })
    return () => controller.abort()
  }, [period])

  const sorted = useMemo(() => {
    if (!rows) return []
    return [...rows].sort((a, b) => {
      const left = sortValue(a, sort.key)
      const right = sortValue(b, sort.key)
      // Employees with no data always sort last, whichever direction.
      if (left === null || right === null) return left === right ? 0 : left === null ? 1 : -1
      const order = left < right ? -1 : left > right ? 1 : 0
      return sort.descending ? -order : order
    })
  }, [rows, sort])

  const stats = useMemo(() => {
    if (!rows || rows.length === 0) return null
    const scores = rows.flatMap((row) => (row.average_score === null ? [] : [row.average_score]))
    const average = scores.length ? scores.reduce((sum, score) => sum + score, 0) / scores.length : null
    const hours = rows.reduce((sum, row) => sum + row.total_productive_hours, 0)
    const attention = scores.filter((score) => score < ATTENTION_THRESHOLD).length
    return { average, hours, attention, noData: rows.length - scores.length }
  }, [rows])

  const toggleSort = (key: SortKey) =>
    setSort((current) =>
      current.key === key ? { key, descending: !current.descending } : { key, descending: key !== 'name' },
    )

  return (
    <>
      <section className="toolbar">
        <PeriodSelector value={period} onChange={onPeriodChange} />
        <span className="muted period-range">{describePeriod(period)} (UTC)</span>
      </section>

      {error ? <div className="error-box">Unable to load team overview: {error}</div> : null}
      {!rows && !error ? <div className="loading-box">Loading team overview…</div> : null}

      {rows && rows.length === 0 ? (
        <div className="panel empty-state">
          <h2>No employees yet</h2>
          <p className="muted">Add employees to see how the team is doing.</p>
          <div>
            <button type="button" className="primary-button" onClick={onAddEmployee}>
              Add employee
            </button>
          </div>
        </div>
      ) : null}

      {stats ? (
        <section className="stats-grid">
          <article className="stat-card">
            <span className="label">Employees</span>
            <strong>{rows?.length}</strong>
          </article>
          <article className="stat-card">
            <span className="label">Team average score</span>
            <strong className={`score ${scoreTone(stats.average)}`}>{formatScore(stats.average)}</strong>
            <span className={`tone-badge ${scoreTone(stats.average)}`}>
              {TONE_LABELS[scoreTone(stats.average)]}
            </span>
          </article>
          <article className="stat-card">
            <span className="label">Total productive hours</span>
            <strong>
              {stats.hours.toFixed(1)}
              <span className="stat-unit">h</span>
            </strong>
          </article>
          <article className="stat-card">
            <span className="label">Need attention</span>
            <strong className={stats.attention > 0 ? 'score bad' : 'score good'}>{stats.attention}</strong>
            <span className="stat-hint">
              Score below {ATTENTION_THRESHOLD * 100}% this period
              {stats.noData > 0 ? ` · ${stats.noData} with no activity` : ''}
            </span>
          </article>
        </section>
      ) : null}

      {sorted.length > 0 ? (
        <section className="panel table-panel">
          <div className="table-scroll">
            <table className="team-table">
              <thead>
                <tr>
                  {COLUMNS.map((column) => (
                    <th
                      key={column.key}
                      className={column.numeric ? 'numeric' : undefined}
                      aria-sort={sort.key === column.key ? (sort.descending ? 'descending' : 'ascending') : 'none'}
                    >
                      <button type="button" className="sort-button" onClick={() => toggleSort(column.key)}>
                        {column.label}
                        <span aria-hidden="true" className="sort-indicator">
                          {sort.key === column.key ? (sort.descending ? '▼' : '▲') : ''}
                        </span>
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sorted.map((row) => {
                  const percent = Math.round((row.average_score ?? 0) * 100)
                  return (
                    <tr key={row.id}>
                      <td>
                        <button type="button" className="row-link" onClick={() => onOpenEmployee(row.id)}>
                          {row.name}
                        </button>
                        {row.role ? <small className="employee-role">{row.role}</small> : null}
                      </td>
                      <td className="numeric">
                        <span className="score-cell">
                          <span className="score-bar" aria-hidden="true">
                            <span className={`score-fill ${scoreTone(row.average_score)}`} style={{ width: `${percent}%` }} />
                          </span>
                          <span className={`score ${scoreTone(row.average_score)}`}>{formatScore(row.average_score)}</span>
                          <span className={`tone-badge ${scoreTone(row.average_score)}`}>{TONE_LABELS[scoreTone(row.average_score)]}</span>
                        </span>
                      </td>
                      <td className="numeric">{row.total_productive_hours}</td>
                      <td className="numeric">{row.total_idle_minutes}</td>
                      <td className="numeric">{row.event_summary.login}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </>
  )
}
