import { useEffect, useMemo, useState } from 'react'
import './App.css'

type Period = 'daily' | 'weekly' | 'monthly'

type Summary = {
  employee_id: number
  period: Period
  average_score: number
  total_productive_hours: number
  total_idle_minutes: number
  event_summary: {
    app_focus: number
    browser_tab: number
    idle_start: number
    login: number
    outlook_activity: number
  }
  app_weights: Record<string, number>
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function fetchJSON<T>(input: string): Promise<T> {
  const response = await fetch(input)
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

function App() {
  const [period, setPeriod] = useState<Period>('daily')
  const [health, setHealth] = useState('Checking...')
  const [summary, setSummary] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    async function load() {
      try {
        const healthResponse = await fetchJSON<{ status: string }>(`${API_URL}/health`)
        if (!isMounted) return
        setHealth(healthResponse.status)

        const report = await fetchJSON<Summary>(`${API_URL}/reports/1?period=${period}`)
        if (!isMounted) return
        setSummary(report)
        setError(null)
      } catch (loadError) {
        if (!isMounted) return
        setError(loadError instanceof Error ? loadError.message : 'Unknown error')
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    setLoading(true)
    void load()

    return () => {
      isMounted = false
    }
  }, [period])

  const scoreTone = useMemo(() => {
    if (!summary) return 'neutral'
    if (summary.average_score >= 0.75) return 'good'
    if (summary.average_score >= 0.5) return 'warning'
    return 'bad'
  }, [summary])

  const handleDownload = async () => {
    const response = await fetch(`${API_URL}/reports/1/pdf?period=${period}`)
    if (!response.ok) {
      throw new Error(`PDF request failed: ${response.status}`)
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report-${period}.pdf`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Moudir.ai</p>
          <h1>Employee dashboard</h1>
        </div>
        <div className="topbar-actions">
          <div className={`status-pill ${health === 'ok' ? 'online' : ''}`}>
            Backend: {health}
          </div>
          <button type="button" className="primary-button" onClick={() => void handleDownload()}>
            Download PDF
          </button>
        </div>
      </header>

      <section className="toolbar">
        <div className="segmented-control" aria-label="Select report period">
          {(['daily', 'weekly', 'monthly'] as Period[]).map((item) => (
            <button
              key={item}
              type="button"
              className={period === item ? 'active' : ''}
              onClick={() => setPeriod(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </section>

      {error ? (
        <div className="error-box">Unable to load report: {error}</div>
      ) : null}

      {loading || !summary ? (
        <div className="loading-box">Loading report...</div>
      ) : (
        <>
          <section className="stats-grid">
            <article className="stat-card">
              <span className="label">Average score</span>
              <strong className={`score ${scoreTone}`}>{summary.average_score.toFixed(2)}</strong>
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
              <h2>App weighting</h2>
              {Object.keys(summary.app_weights).length === 0 ? (
                <p className="muted">No app weights configured yet.</p>
              ) : (
                <ul className="metric-list">
                  {Object.entries(summary.app_weights).map(([name, value]) => (
                    <li key={name}>
                      <span>{name}</span>
                      <strong>{Number(value).toFixed(2)}</strong>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </section>
        </>
      )}
    </div>
  )
}

export default App
