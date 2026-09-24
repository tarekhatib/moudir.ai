import { useEffect, useState, type FormEvent } from 'react'
import { ApiError, apiGet, apiPost, errorMessage, isAbort } from '../api/client'
import { CATEGORY_KEYS, DAY_KEYS, type DayKey, type Employee, type EmployeeConfig, type TimeRange, type WeightLevel } from '../types'
import {
  CATEGORY_LABELS,
  DAY_LABELS,
  categoryTotal,
  configToForm,
  formToPayload,
  hasErrors,
  nextRowKey,
  validateConfig,
  type ConfigErrors,
  type ConfigForm,
} from '../utils/config'

type Props = {
  employee: Employee
  onSaved: () => void
  onError: (message: string) => void
}

const WORKDAY_BLOCKS: TimeRange[] = [
  ['09:00', '13:00'],
  ['14:00', '18:00'],
]

export function ConfigPanel({ employee, onSaved, onError }: Props) {
  const [form, setForm] = useState<ConfigForm | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [errors, setErrors] = useState<ConfigErrors>({})
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)

  const employeeId = employee.id

  useEffect(() => {
    const controller = new AbortController()
    setForm(null)
    setLoadError(null)
    setErrors({})
    setDirty(false)
    apiGet<EmployeeConfig>(`/config/${employeeId}`, controller.signal)
      .then((config) => setForm(configToForm(config)))
      .catch((error: unknown) => {
        if (isAbort(error)) return
        // Employees created before configs existed have no row yet: start from defaults.
        if (error instanceof ApiError && error.status === 404) {
          setForm(configToForm(null))
        } else {
          setLoadError(errorMessage(error))
        }
      })
    return () => controller.abort()
  }, [employeeId])

  if (loadError) return <div className="error-box">Unable to load settings: {loadError}</div>
  if (!form) return <div className="loading-box">Loading settings…</div>

  const change = (updater: (current: ConfigForm) => ConfigForm) => {
    setForm((current) => (current ? updater(current) : current))
    setDirty(true)
  }

  const setDay = (day: DayKey, index: number, position: 0 | 1, value: string) =>
    change((current) => ({
      ...current,
      schedule: {
        ...current.schedule,
        [day]: current.schedule[day].map((range, i): TimeRange =>
          i === index ? (position === 0 ? [value, range[1]] : [range[0], value]) : range,
        ),
      },
    }))

  const addBlock = (day: DayKey) =>
    change((current) => {
      const last = current.schedule[day].at(-1)
      const block: TimeRange = last ? [last[1], last[1] < '23:00' ? addHour(last[1]) : '23:59'] : ['09:00', '17:00']
      return { ...current, schedule: { ...current.schedule, [day]: [...current.schedule[day], block] } }
    })

  const removeBlock = (day: DayKey, index: number) =>
    change((current) => ({
      ...current,
      schedule: { ...current.schedule, [day]: current.schedule[day].filter((_, i) => i !== index) },
    }))

  const applyStandardWeek = () =>
    change((current) => {
      const schedule = { ...current.schedule }
      for (const day of DAY_KEYS) {
        schedule[day] = day === 'sat' || day === 'sun' ? [] : WORKDAY_BLOCKS.map(([s, e]): TimeRange => [s, e])
      }
      return { ...current, schedule }
    })

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const found = validateConfig(form)
    setErrors(found)
    if (hasErrors(found)) return

    setSaving(true)
    try {
      const saved = await apiPost<EmployeeConfig>(`/config/${employeeId}`, formToPayload(form, employee))
      setForm(configToForm(saved))
      setDirty(false)
      onSaved()
    } catch (error) {
      onError(errorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const total = categoryTotal(form)

  return (
    <form className="settings" onSubmit={(event) => void handleSubmit(event)} noValidate>
      <section className="panel">
        <div className="panel-heading">
          <h2>Scoring weights</h2>
          <span className={total === 100 ? 'total-pill ok' : 'total-pill'}>Total: {total}%</span>
        </div>
        <p className="muted panel-intro">How much each category contributes to the productivity score.</p>
        <div className="weight-grid">
          {CATEGORY_KEYS.map((key) => (
            <label key={key}>
              {CATEGORY_LABELS[key]}
              <span className="input-suffix">
                <input
                  type="number"
                  min={0}
                  max={100}
                  step={5}
                  value={form.categories[key]}
                  onChange={(event) =>
                    change((current) => ({ ...current, categories: { ...current.categories, [key]: event.target.value } }))
                  }
                />
                <span>%</span>
              </span>
            </label>
          ))}
        </div>
        {errors.categories ? <p className="field-error">{errors.categories}</p> : null}
      </section>

      <section className="panel">
        <h2>Software weights</h2>
        <p className="muted panel-intro">Mark which applications count as high, medium or low value for this role.</p>
        {form.apps.length === 0 ? <p className="muted">No applications configured.</p> : null}
        <div className="app-rows">
          {form.apps.map((app) => (
            <div className="app-row" key={app.key}>
              <input
                aria-label="Application name"
                placeholder="e.g. VS Code"
                value={app.name}
                onChange={(event) =>
                  change((current) => ({
                    ...current,
                    apps: current.apps.map((row) => (row.key === app.key ? { ...row, name: event.target.value } : row)),
                  }))
                }
              />
              <select
                aria-label={`Weight for ${app.name || 'application'}`}
                value={app.level}
                onChange={(event) =>
                  change((current) => ({
                    ...current,
                    apps: current.apps.map((row) =>
                      row.key === app.key ? { ...row, level: event.target.value as WeightLevel } : row,
                    ),
                  }))
                }
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <button
                type="button"
                className="icon-button"
                aria-label={`Remove ${app.name || 'application'}`}
                onClick={() => change((current) => ({ ...current, apps: current.apps.filter((row) => row.key !== app.key) }))}
              >
                ×
              </button>
            </div>
          ))}
        </div>
        {errors.apps ? <p className="field-error">{errors.apps}</p> : null}
        <button
          type="button"
          className="secondary-button"
          onClick={() =>
            change((current) => ({ ...current, apps: [...current.apps, { key: nextRowKey(), name: '', level: 'medium' }] }))
          }
        >
          Add application
        </button>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Work schedule</h2>
          <button type="button" className="secondary-button" onClick={applyStandardWeek}>
            Use Mon–Fri 9–6
          </button>
        </div>
        <div className="schedule">
          {DAY_KEYS.map((day) => (
            <div className="schedule-day" key={day}>
              <strong>{DAY_LABELS[day]}</strong>
              <div className="schedule-blocks">
                {form.schedule[day].length === 0 ? <span className="muted">Day off</span> : null}
                {form.schedule[day].map((range, index) => (
                  <span className="time-block" key={index}>
                    <input
                      type="time"
                      aria-label={`${DAY_LABELS[day]} block ${index + 1} start`}
                      value={range[0]}
                      onChange={(event) => setDay(day, index, 0, event.target.value)}
                    />
                    –
                    <input
                      type="time"
                      aria-label={`${DAY_LABELS[day]} block ${index + 1} end`}
                      value={range[1]}
                      onChange={(event) => setDay(day, index, 1, event.target.value)}
                    />
                    <button
                      type="button"
                      className="icon-button"
                      aria-label={`Remove ${DAY_LABELS[day]} block ${index + 1}`}
                      onClick={() => removeBlock(day, index)}
                    >
                      ×
                    </button>
                  </span>
                ))}
                <button type="button" className="link-button" onClick={() => addBlock(day)}>
                  + Add block
                </button>
              </div>
              {errors.schedule?.[day] ? <span className="field-error">{errors.schedule[day]}</span> : null}
            </div>
          ))}
        </div>
      </section>

      <section className="panel">
        <h2>Targets</h2>
        <div className="form-grid">
          <label>
            Minimum productive hours per day
            <input
              type="number"
              min={0}
              max={24}
              step={0.5}
              value={form.minProductiveHours}
              onChange={(event) => change((current) => ({ ...current, minProductiveHours: event.target.value }))}
            />
            {errors.minProductiveHours ? <span className="field-error">{errors.minProductiveHours}</span> : null}
          </label>
          <label>
            Maximum idle minutes per day
            <input
              type="number"
              min={0}
              max={1440}
              step={5}
              value={form.maxIdleMinutes}
              onChange={(event) => change((current) => ({ ...current, maxIdleMinutes: event.target.value }))}
            />
            {errors.maxIdleMinutes ? <span className="field-error">{errors.maxIdleMinutes}</span> : null}
          </label>
        </div>
      </section>

      <div className="form-actions sticky-actions">
        <button type="submit" className="primary-button" disabled={saving || !dirty}>
          {saving ? 'Saving…' : 'Save settings'}
        </button>
        {dirty ? <span className="muted">You have unsaved changes</span> : null}
      </div>
    </form>
  )
}

function addHour(time: string): string {
  const [hours, minutes] = time.split(':').map(Number)
  return `${String(Math.min(hours + 1, 23)).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}
