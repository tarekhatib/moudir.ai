import { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'
import { apiDelete, apiDownload, apiGet, apiPost, apiPut, errorMessage, isAbort } from './api/client'
import { AccountView } from './components/AccountView'
import { AgentPanel } from './components/AgentPanel'
import { ConfigPanel } from './components/ConfigPanel'
import { EmployeeForm } from './components/EmployeeForm'
import { EmployeeList } from './components/EmployeeList'
import { AccountIcon, DownloadIcon, PeopleIcon, PlusIcon, SignOutIcon, TeamIcon } from './components/Icons'
import { Notice, type NoticeMessage } from './components/Notice'
import { PeriodSelector } from './components/PeriodSelector'
import { ReportView } from './components/ReportView'
import { TeamOverview } from './components/TeamOverview'
import { TrendPanel } from './components/TrendPanel'
import type { Employee, EmployeeInput, Me, Period, Summary } from './types'
import { describePeriod } from './utils/period'

type Status = 'loading' | 'ready' | 'error'
type Tab = 'report' | 'settings' | 'agent'
type View = 'team' | 'employees' | 'account'

const TAB_LABELS: Record<Tab, string> = { report: 'Report', settings: 'Settings', agent: 'Desktop agent' }
const VIEW_LABELS: Record<View, string> = { team: 'Team overview', employees: 'Employees', account: 'Account' }

type Props = {
  me: Me
  onSignOut: () => void
}

function App({ me, onSignOut }: Props) {
  const [period, setPeriod] = useState<Period>('daily')
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

  // `quiet` refreshes the list in place without swapping it for a loading state.
  const loadEmployees = useCallback(async (signal?: AbortSignal, quiet = false) => {
    if (!quiet) setEmployeesStatus('loading')
    try {
      const list = await apiGet<Employee[]>('/employees', signal)
      setEmployees(list)
      setSelectedId((current) => (current !== null && list.some((e) => e.id === current) ? current : list[0]?.id ?? null))
      setEmployeesStatus('ready')
    } catch (error) {
      if (isAbort(error)) return
      setEmployeesStatus('error')
      setNotice({ kind: 'error', text: errorMessage(error) })
    }
  }, [])

  // Load on sign-in, then refresh quietly each time the Employees page is opened, so employees
  // added or moved elsewhere (another manager, a script) show up without reloading the page.
  const employeesLoaded = useRef(false)
  useEffect(() => {
    if (employeesLoaded.current && view !== 'employees') return
    const controller = new AbortController()
    void loadEmployees(controller.signal, employeesLoaded.current)
    employeesLoaded.current = true
    return () => controller.abort()
  }, [loadEmployees, view])

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

  const pageTitle =
    view === 'employees' ? (creating ? 'New employee' : selectedEmployee?.name ?? 'Employees') : VIEW_LABELS[view]
  const pageCrumb =
    view === 'employees' && selectedEmployee && !creating ? selectedEmployee.role || 'Employee' : me.organization.name

  const setAgentTokenDate = (id: number, agentTokenCreatedAt: string | null) =>
    setEmployees((current) =>
      current.map((employee) => (employee.id === id ? { ...employee, agent_token_created_at: agentTokenCreatedAt } : employee)),
    )

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img className="brand-mark" src="/favicon.svg" alt="" width={28} height={28} />
          <span className="brand-name">Moudir</span>
        </div>

        <nav className="side-nav" aria-label="Main">
          <span className="nav-label">Workspace</span>
          {(['team', 'employees', 'account'] as View[]).map((item) => (
            <button
              key={item}
              type="button"
              className={view === item ? 'nav-item active' : 'nav-item'}
              aria-current={view === item ? 'page' : undefined}
              aria-label={VIEW_LABELS[item]}
              onClick={() => setView(item)}
            >
              {item === 'team' ? <TeamIcon /> : item === 'employees' ? <PeopleIcon /> : <AccountIcon />}
              <span>{VIEW_LABELS[item]}</span>
              {item === 'employees' && employeesStatus === 'ready' ? (
                <span className="nav-count">{employees.length}</span>
              ) : null}
            </button>
          ))}
        </nav>

        <div className="sidebar-foot">
          <span className="sidebar-user">
            <strong>{me.organization.name}</strong>
            <small>{me.user.name}</small>
          </span>
          <button type="button" className="icon-button" onClick={onSignOut} aria-label="Sign out" title="Sign out">
            <SignOutIcon />
          </button>
        </div>
      </aside>

      <main className="main">
        <div className="dashboard-shell">
          <header className="page-header">
            <div>
              <p className="crumb">{pageCrumb}</p>
              <h1>{pageTitle}</h1>
            </div>
            <div className="page-actions">
              {view === 'team' ? (
                <button type="button" className="secondary-button" onClick={startCreating}>
                  <PlusIcon />
                  Add employee
                </button>
              ) : null}
              {view === 'employees' && selectedId !== null && !creating ? (
                <button type="button" className="primary-button" onClick={() => void handleDownload()} disabled={downloading}>
                  <DownloadIcon />
                  {downloading ? 'Preparing…' : 'Download PDF'}
                </button>
              ) : null}
            </div>
          </header>

          <Notice notice={notice} onDismiss={dismissNotice} />

          {employeesStatus === 'error' && view !== 'account' ? (
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

          {view === 'account' ? <AccountView me={me} onNotice={setNotice} /> : null}

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
                  {(['report', 'settings', 'agent'] as Tab[]).map((item) => (
                    <button
                      key={item}
                      type="button"
                      className={tab === item ? 'tab active' : 'tab'}
                      aria-current={tab === item ? 'page' : undefined}
                      onClick={() => setTab(item)}
                    >
                      {TAB_LABELS[item]}
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

              {selectedEmployee && !creating && tab === 'agent' ? (
                <AgentPanel
                  key={selectedEmployee.id}
                  employee={selectedEmployee}
                  onChanged={(createdAt) => setAgentTokenDate(selectedEmployee.id, createdAt)}
                  onError={(message) => setNotice({ kind: 'error', text: message })}
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

                  <TrendPanel employeeId={selectedId} refreshKey={reportVersion} />
                </>
              ) : null}
            </>
          ) : null}
        </div>
      </main>
    </div>
  )
}

export default App
