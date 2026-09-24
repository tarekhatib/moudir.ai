import { useEffect, useState, type FormEvent } from 'react'
import type { Employee, EmployeeInput } from '../types'
import { validateEmployee, type EmployeeErrors } from '../utils/validation'

type Props = {
  // null means the form is creating a new employee.
  employee: Employee | null
  saving: boolean
  onSave: (input: EmployeeInput) => void
  onCancel?: () => void
  onDelete?: () => void
  deleting?: boolean
}

const EMPTY: EmployeeInput = { name: '', role: '', email: '', job_description: '', role_tag: '' }

function toInput(employee: Employee | null): EmployeeInput {
  if (!employee) return EMPTY
  return {
    name: employee.name,
    role: employee.role ?? '',
    email: employee.email ?? '',
    job_description: employee.job_description ?? '',
    role_tag: employee.role_tag ?? '',
  }
}

export function EmployeeForm({ employee, saving, onSave, onCancel, onDelete, deleting = false }: Props) {
  const [form, setForm] = useState<EmployeeInput>(() => toInput(employee))
  const [errors, setErrors] = useState<EmployeeErrors>({})
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  // Reset the form whenever a different employee (or "new") is shown.
  useEffect(() => {
    setForm(toInput(employee))
    setErrors({})
    setConfirmingDelete(false)
  }, [employee])

  const update = (field: keyof EmployeeInput, value: string) => {
    setForm((current) => ({ ...current, [field]: value }))
    if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }))
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const found = validateEmployee(form)
    setErrors(found)
    if (Object.keys(found).length === 0) onSave(form)
  }

  const field = (name: keyof EmployeeInput, label: string, type = 'text') => (
    <label>
      {label}
      <input
        type={type}
        value={form[name]}
        aria-invalid={errors[name] ? true : undefined}
        onChange={(event) => update(name, event.target.value)}
      />
      {errors[name] ? <span className="field-error">{errors[name]}</span> : null}
    </label>
  )

  return (
    <form className="panel form-panel" onSubmit={handleSubmit} noValidate>
      <h2>{employee ? 'Employee profile' : 'New employee'}</h2>
      <div className="form-grid">
        {field('name', 'Full name *')}
        {field('role', 'Role')}
        {field('email', 'Email', 'email')}
        {field('role_tag', 'Role tag')}
        <label className="full-width">
          Job description
          <textarea value={form.job_description} onChange={(event) => update('job_description', event.target.value)} />
        </label>
      </div>
      <div className="form-actions">
        <button type="submit" className="primary-button" disabled={saving}>
          {saving ? 'Saving…' : employee ? 'Save employee' : 'Create employee'}
        </button>
        {onCancel ? (
          <button type="button" className="secondary-button" onClick={onCancel} disabled={saving}>
            Cancel
          </button>
        ) : null}
        {employee && onDelete && !confirmingDelete ? (
          <button
            type="button"
            className="danger-link"
            onClick={() => setConfirmingDelete(true)}
            disabled={saving || deleting}
          >
            Delete employee
          </button>
        ) : null}
      </div>
      {employee && onDelete && confirmingDelete ? (
        <div className="confirm-box" role="alertdialog" aria-label="Confirm delete">
          <p>
            Delete <strong>{employee.name}</strong>? This also removes their settings and all recorded activity. This
            cannot be undone.
          </p>
          <div className="form-actions">
            <button type="button" className="danger-button" onClick={onDelete} disabled={deleting}>
              {deleting ? 'Deleting…' : 'Yes, delete'}
            </button>
            <button type="button" className="secondary-button" onClick={() => setConfirmingDelete(false)} disabled={deleting}>
              Keep employee
            </button>
          </div>
        </div>
      ) : null}
    </form>
  )
}
