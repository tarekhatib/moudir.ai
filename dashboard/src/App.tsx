import { useCallback, useEffect, useState } from 'react'
import './App.css'
import { apiDelete, apiDownload, apiGet, apiPost, apiPut, errorMessage, isAbort } from './api/client'
import { ConfigPanel } from './components/ConfigPanel'
import { EmployeeForm } from './components/EmployeeForm'
import { EmployeeList } from './components/EmployeeList'
import { Notice, type NoticeMessage } from './components/Notice'
import { PeriodSelector } from './components/PeriodSelector'
import { ReportView } from './components/ReportView'
import { TeamOverview } from './components/TeamOverview'
import type { Employee, EmployeeInput, Period, Summary } from './types'
import { describePeriod } from './utils/period'

type Status = 'loading' | 'ready' | 'error'
type Tab = 'report' | 'settings'
type View = 'team' | 'employees'

function App() {
  const [period, setPeriod] = useState<Period>('daily')
  const [health, setHealth] = useState<'checking' | 'ok' | 'offline'>('checking')
  const [employees, setEmployees] = useState<Employee[]>([])
  const [employeesStatus, setEmployeesStatus] = useState<Status>('loading')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [creating, setCreating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [summaryStatus, setSummaryStatus] = useState<Status>('loading')
  const [summaryError, setSummaryError] = useState<string | null>(null)
  const [notice, setNotice] = useState<NoticeMessage | null>(null)
  const [view, setView] = useState<View>('team')
  const [tab, setTab] = useState<Tab>('report')
  const [deleting, setDeleting] = useState(false)
  // Bumped after settings are saved so the report re-fetches with the new weights.
  const [reportVersion, setReportVersion] = useState(0)

  const dismissNotice = useCallback(() => setNotice(null), [])
  const selectedEmployee = employees.find((employee) => employee.id === selectedId) ?? null

  const loadEmployees = useCallback(async (signal?: AbortSignal) => {
    setEmployeesStatus('loading')
    try {
      const [healthResponse, list] = await Promise.all([
        apiGet<{ status: string }>('/health', signal),
        apiGet<Employee[]>('/employees', signal),
      ])
      setHealth(healthResponse.status === 'ok' ? 'ok' : 'offline')
      setEmployees(list)
      setSelectedId((current) => (current !== null && list.some((e) => e.id === current) ? current : list[0]?.id ?? null))
      setEmployeesStatus('ready')
    } catch (error) {
      if (isAbort(error)) return
      setHealth('offline')
      setEmployeesStatus('error')
      setNotice({ kind: 'error', text: errorMessage(error) })
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void loadEmployees(controller.signal)
    return () => controller.abort()
  }, [loadEmployees])

  // One place that loads the report, so changing period or employee fetches exactly once.
  useEffect(() => {
    if (view !== 'employees' || selectedId === null || creating || tab !== 'report') {
      setSummary(null)
      return
    }
    const controller = new AbortController()
    setSummaryStatus('loading')
    setSummaryError(null)
    apiGet<Summary>(`/reports/${selectedId}?period=${period}`, controller.signal)
      .then((report) => {
        setSummary(report)
        setSummaryStatus('ready')
      })
      .catch((error: unknown) => {
        if (isAbort(error)) return
        setSummary(null)
        setSummaryStatus('error')
        setSummaryError(errorMessage(error))
      })
    return () => controller.abort()
  }, [view, selectedId, period, creating, tab, reportVersion])

  const handleSelect = (id: number) => {
    setCreating(false)
    setSelectedId(id)
  }

  const handleSave = async (input: EmployeeInput) => {
    setSaving(true)
    try {
      if (creating || !selectedEmployee) {
        const created = await apiPost<Employee>('/employees', input)
        setEmployees((current) => [...current, created])
        setSelectedId(created.id)
        setCreating(false)
        setNotice({ kind: 'success', text: `${created.name} was added.` })
      } else {
        const updated = await apiPut<Employee>(`/employees/${selectedEmployee.id}`, input)
        setEmployees((current) => current.map((employee) => (employee.id === updated.id ? updated : employee)))
        setNotice({ kind: 'success', text: 'Changes saved.' })
      }
    } catch (error) {
      setNotice({ kind: 'error', text: errorMessage(error) })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedEmployee) return
    const { id, name } = selectedEmployee
    setDeleting(true)
    try {
      await apiDelete(`/employees/${id}`)
      const remaining = employees.filter((employee) => employee.id !== id)
      setEmployees(remaining)
      setSelectedId(remaining[0]?.id ?? null)
      setTab('report')
      setNotice({ kind: 'success', text: `${name} was deleted.` })
    } catch (error) {
      setNotice({ kind: 'error', text: `Could not delete ${name}: ${errorMessage(error)}` })
    } finally {
      setDeleting(false)
    }
  }

  const openEmployee = (id: number) => {
    setView('employees')
    setCreating(false)
    setSelectedId(id)
    setTab('report')
  }

  const startCreating = () => {
    setView('employees')
    setCreating(true)
  }

  const handleDownload = async () => {
    if (selectedId === null) return
    setDownloading(true)
    try {
      await apiDownload(`/reports/${selectedId}/pdf?period=${period}`, `report-${selectedId}-${period}.pdf`)
    } catch (error) {
      setNotice({ kind: 'error', text: `PDF export failed: ${errorMessage(error)}` })
    } finally {
      setDownloading(false)
    }
  }

  const showForm = creating || selectedEmployee !== null

  return (
    <div className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Moudir.ai</p>
          <h1>Admin dashboard</h1>
        </div>
        <nav className="main-nav" aria-label="Main">
          {(['team', 'employees'] as View[]).map((item) => (
            <button
              key={item}
              type="button"
              className={view === item ? 'active' : ''}
              aria-current={view === item ? 'page' : undefined}
              onClick={() => setView(item)}
            >
              {item === 'team' ? 'Team overview' : 'Employees'}
            </button>
          ))}
        </nav>
        <div className="topbar-actions">
          <div className={`status-pill ${health === 'ok' ? 'online' : ''}`}>
            Backend: {health}
          </div>
          {view === 'employees' && selectedId !== null && !creating ? (
            <button type="button" className="primary-button" onClick={() => void handleDownload()} disabled={downloading}>
              {downloading ? 'Preparing…' : 'Download PDF'}
            </button>
          ) : null}
        </div>
      </header>

      <Notice notice={notice} onDismiss={dismissNotice} />

      {employeesStatus === 'error' ? (
        <div className="error-box">
          Could not load employees.{' '}
          <button type="button" className="link-button" onClick={() => void loadEmployees()}>
            Try again
          </button>
        </div>
      ) : null}

      {view === 'team' ? (
        <TeamOverview
          period={period}
          onPeriodChange={setPeriod}
          onOpenEmployee={openEmployee}
          onAddEmployee={startCreating}
        />
      ) : null}

      {view === 'employees' ? (
        <>
          <section className="employee-manager">
            {employeesStatus === 'loading' ? (
              <div className="panel"><p className="muted">Loading employees…</p></div>
            ) : (
              <EmployeeList
                employees={employees}
                selectedId={selectedId}
                creating={creating}
                onSelect={handleSelect}
                onAdd={startCreating}
              />
            )}

            {showForm ? (
              <EmployeeForm
                employee={creating ? null : selectedEmployee}
                saving={saving}
                onSave={(input) => void handleSave(input)}
                onCancel={creating && employees.length > 0 ? () => setCreating(false) : undefined}
                onDelete={() => void handleDelete()}
                deleting={deleting}
              />
            ) : (
              <div className="panel empty-state">
                <h2>No employee selected</h2>
                <p className="muted">Add an employee to start tracking activity and generating reports.</p>
              </div>
            )}
          </section>

          {selectedEmployee && !creating ? (
            <nav className="tabs" aria-label="Employee sections">
              {(['report', 'settings'] as Tab[]).map((item) => (
                <button
                  key={item}
                  type="button"
                  className={tab === item ? 'tab active' : 'tab'}
                  aria-current={tab === item ? 'page' : undefined}
                  onClick={() => setTab(item)}
                >
                  {item === 'report' ? 'Report' : 'Settings'}
                </button>
              ))}
            </nav>
          ) : null}

          {selectedEmployee && !creating && tab === 'settings' ? (
            <ConfigPanel
              employee={selectedEmployee}
              onSaved={() => {
                setReportVersion((version) => version + 1)
                setNotice({ kind: 'success', text: 'Settings saved.' })
              }}
              onError={(message) => setNotice({ kind: 'error', text: `Could not save settings: ${message}` })}
            />
          ) : null}

          {selectedId !== null && !creating && tab === 'report' ? (
            <>
              <section className="toolbar">
                <PeriodSelector value={period} onChange={setPeriod} />
                <span className="muted period-range">{describePeriod(period)} (UTC)</span>
              </section>

              {summaryStatus === 'error' ? (
                <div className="error-box">Unable to load report: {summaryError}</div>
              ) : summaryStatus === 'loading' || !summary ? (
                <div className="loading-box">Loading report…</div>
              ) : (
                <ReportView summary={summary} />
              )}
            </>
          ) : null}
        </>
      ) : null}
    </div>
  )
}

export default App
