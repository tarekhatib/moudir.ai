import { useEffect, useMemo, useState } from 'react'
import './App.css'

type Period = 'daily' | 'weekly' | 'monthly'

type Employee = {
  id: number
  name: string
  role: string | null
  email: string | null
  job_description: string | null
  role_tag: string | null
}

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
  const [employees, setEmployees] = useState<Employee[]>([])
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({
    name: '',
    role: '',
    email: '',
    job_description: '',
    role_tag: '',
  })

  useEffect(() => {
    let isMounted = true

    async function load() {
      try {
        const healthResponse = await fetchJSON<{ status: string }>(`${API_URL}/health`)
        if (!isMounted) return
        setHealth(healthResponse.status)

        const employeeList = await fetchJSON<Employee[]>(`${API_URL}/employees`)
        if (!isMounted) return
        setEmployees(employeeList)

        if (employeeList.length > 0) {
          const activeId = selectedEmployeeId ?? employeeList[0].id
          setSelectedEmployeeId(activeId)
          const report = await fetchJSON<Summary>(`${API_URL}/reports/${activeId}?period=${period}`)
          if (!isMounted) return
          setSummary(report)
        } else {
          setSummary(null)
        }
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

  useEffect(() => {
    if (!selectedEmployeeId) return

    const employee = employees.find((item) => item.id === selectedEmployeeId)
    if (!employee) return

    setForm({
      name: employee.name,
      role: employee.role ?? '',
      email: employee.email ?? '',
      job_description: employee.job_description ?? '',
      role_tag: employee.role_tag ?? '',
    })
  }, [employees, selectedEmployeeId])

  useEffect(() => {
    if (!selectedEmployeeId) return

    let isMounted = true

    async function loadSummary() {
      try {
        const report = await fetchJSON<Summary>(`${API_URL}/reports/${selectedEmployeeId}?period=${period}`)
        if (!isMounted) return
        setSummary(report)
      } catch {
        if (!isMounted) return
        setError('Unable to load employee report')
      }
    }

    void loadSummary()
    return () => {
      isMounted = false
    }
  }, [selectedEmployeeId, period])

  const scoreTone = useMemo(() => {
    if (!summary) return 'neutral'
    if (summary.average_score >= 0.75) return 'good'
    if (summary.average_score >= 0.5) return 'warning'
    return 'bad'
  }, [summary])

  const handleDownload = async () => {
    if (!selectedEmployeeId) return

    const response = await fetch(`${API_URL}/reports/${selectedEmployeeId}/pdf?period=${period}`)
    if (!response.ok) {
      throw new Error(`PDF request failed: ${response.status}`)
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report-${selectedEmployeeId}-${period}.pdf`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleFormChange = (field: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const handleSaveEmployee = async () => {
    if (!selectedEmployeeId) return

    const payload = {
      name: form.name,
      role: form.role,
      email: form.email,
      job_description: form.job_description,
      role_tag: form.role_tag,
    }

    const response = await fetch(`${API_URL}/employees/${selectedEmployeeId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      throw new Error(`Save failed: ${response.status}`)
    }

    const updated = await response.json()
    setEmployees((current) =>
      current.map((employee) =>
        employee.id === updated.id
          ? { ...employee, ...updated }
          : employee,
      ),
    )
  }

  const handleCreateEmployee = async () => {
    const payload = {
      name: form.name || 'New Employee',
      role: form.role,
      email: form.email,
      job_description: form.job_description,
      role_tag: form.role_tag,
    }

    const response = await fetch(`${API_URL}/employees`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      throw new Error(`Create failed: ${response.status}`)
    }

    const created = await response.json()
    setEmployees((current) => [...current, created])
    setSelectedEmployeeId(created.id)
  }

  return (
    <div className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Moudir.ai</p>
          <h1>Admin dashboard</h1>
        </div>
        <div className="topbar-actions">
          <div className={`status-pill ${health === 'ok' ? 'online' : ''}`}>
            Backend: {health}
          </div>
          {selectedEmployeeId ? (
            <button type="button" className="primary-button" onClick={() => void handleDownload()}>
              Download PDF
            </button>
          ) : null}
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

      <section className="employee-manager">
        <div className="panel">
          <h2>Employees</h2>
          <div className="employee-list">
            {employees.map((employee) => (
              <button
                key={employee.id}
                type="button"
                className={selectedEmployeeId === employee.id ? 'employee-item selected' : 'employee-item'}
                onClick={() => setSelectedEmployeeId(employee.id)}
              >
                <span>{employee.name}</span>
                <small>#{employee.id}</small>
              </button>
            ))}
          </div>
          <button type="button" className="secondary-button" onClick={() => void handleCreateEmployee()}>
            Add employee
          </button>
        </div>

        <div className="panel form-panel">
          <h2>Employee profile</h2>
          <div className="form-grid">
            <label>
              Full name
              <input value={form.name} onChange={(event) => handleFormChange('name', event.target.value)} />
            </label>
            <label>
              Role
              <input value={form.role} onChange={(event) => handleFormChange('role', event.target.value)} />
            </label>
            <label>
              Email
              <input value={form.email} onChange={(event) => handleFormChange('email', event.target.value)} />
            </label>
            <label>
              Role tag
              <input value={form.role_tag} onChange={(event) => handleFormChange('role_tag', event.target.value)} />
            </label>
            <label className="full-width">
              Job description
              <textarea value={form.job_description} onChange={(event) => handleFormChange('job_description', event.target.value)} />
            </label>
          </div>
          <button type="button" className="primary-button" onClick={() => void handleSaveEmployee()}>
            Save employee
          </button>
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
