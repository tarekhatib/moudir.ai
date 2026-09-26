import { useEffect, useState, type FormEvent } from 'react'
import { apiDelete, apiGet, apiPost, errorMessage, isAbort } from '../api/client'
import type { Me, User } from '../types'
import { MIN_PASSWORD_LENGTH } from './AuthScreen'
import type { NoticeMessage } from './Notice'

type Props = {
  me: Me
  onNotice: (notice: NoticeMessage) => void
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function PasswordForm({ onNotice }: { onNotice: Props['onNotice'] }) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (next.length < MIN_PASSWORD_LENGTH) {
      setError(`Use at least ${MIN_PASSWORD_LENGTH} characters.`)
      return
    }
    setError(null)
    setSaving(true)
    try {
      await apiPost('/auth/password', { current_password: current, new_password: next })
      setCurrent('')
      setNext('')
      onNotice({ kind: 'success', text: 'Password changed. Your other sessions were signed out.' })
    } catch (saveError) {
      setError(errorMessage(saveError))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="panel form-panel" onSubmit={(event) => void handleSubmit(event)} noValidate>
      <h2>Change password</h2>
      <div className="form-grid">
        <label>
          Current password
          <input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} autoComplete="current-password" />
        </label>
        <label>
          New password
          <input
            type="password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            autoComplete="new-password"
            aria-invalid={error ? true : undefined}
          />
          {error ? <span className="field-error">{error}</span> : <span className="stat-hint">At least {MIN_PASSWORD_LENGTH} characters</span>}
        </label>
      </div>
      <div className="form-actions">
        <button type="submit" className="primary-button" disabled={saving || !current || !next}>
          {saving ? 'Saving…' : 'Change password'}
        </button>
      </div>
    </form>
  )
}

function Managers({ me, onNotice }: Props) {
  const [users, setUsers] = useState<User[] | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [removing, setRemoving] = useState<number | null>(null)
  const isOwner = me.user.role === 'owner'

  useEffect(() => {
    const controller = new AbortController()
    apiGet<User[]>('/organization/users', controller.signal)
      .then(setUsers)
      .catch((error: unknown) => {
        if (!isAbort(error)) setLoadError(errorMessage(error))
      })
    return () => controller.abort()
  }, [])

  const addManager = async (event: FormEvent) => {
    event.preventDefault()
    if (!form.name.trim()) return setFormError('Enter their name.')
    if (!EMAIL_PATTERN.test(form.email.trim())) return setFormError('Enter a valid email address.')
    if (form.password.length < MIN_PASSWORD_LENGTH) return setFormError(`Use at least ${MIN_PASSWORD_LENGTH} characters for the password.`)
    setFormError(null)
    setSaving(true)
    try {
      const created = await apiPost<User>('/organization/users', form)
      setUsers((current) => [...(current ?? []), created])
      setForm({ name: '', email: '', password: '' })
      onNotice({ kind: 'success', text: `${created.name} can now sign in. Share the password with them securely.` })
    } catch (error) {
      setFormError(errorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  const remove = async (user: User) => {
    setRemoving(user.id)
    try {
      await apiDelete(`/organization/users/${user.id}`)
      setUsers((current) => (current ?? []).filter((member) => member.id !== user.id))
      onNotice({ kind: 'success', text: `${user.name} no longer has access.` })
    } catch (error) {
      onNotice({ kind: 'error', text: `Could not remove ${user.name}: ${errorMessage(error)}` })
    } finally {
      setRemoving(null)
    }
  }

  return (
    <section className="panel form-panel">
      <h2>Managers</h2>
      <p className="muted panel-intro">Everyone listed here can sign in and see all employees in {me.organization.name}.</p>
      {loadError ? <div className="error-box">Unable to load managers: {loadError}</div> : null}
      {!users && !loadError ? <p className="muted">Loading…</p> : null}
      {users ? (
        <ul className="metric-list">
          {users.map((user) => (
            <li key={user.id}>
              <span>
                {user.name} <small className="employee-role">{user.email}</small>
              </span>
              <span className="manager-actions">
                <span className="tone-badge none">{user.role === 'owner' ? 'Owner' : 'Manager'}</span>
                {isOwner && user.id !== me.user.id ? (
                  <button type="button" className="danger-link" onClick={() => void remove(user)} disabled={removing === user.id}>
                    {removing === user.id ? 'Removing…' : 'Remove'}
                  </button>
                ) : null}
              </span>
            </li>
          ))}
        </ul>
      ) : null}

      {isOwner ? (
        <form onSubmit={(event) => void addManager(event)} noValidate>
          <h3>Add a manager</h3>
          <div className="form-grid">
            <label>
              Name
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </label>
            <label>
              Email
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </label>
            <label>
              Temporary password
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                autoComplete="new-password"
              />
              <span className="stat-hint">They can change it after signing in</span>
            </label>
          </div>
          {formError ? <div className="error-box" role="alert">{formError}</div> : null}
          <div className="form-actions">
            <button type="submit" className="primary-button" disabled={saving}>
              {saving ? 'Adding…' : 'Add manager'}
            </button>
          </div>
        </form>
      ) : (
        <p className="muted">Only the account owner can add or remove managers.</p>
      )}
    </section>
  )
}

export function AccountView({ me, onNotice }: Props) {
  return (
    <div className="stack">
      <section className="panel form-panel">
        <h2>{me.organization.name}</h2>
        <ul className="metric-list">
          <li><span>Signed in as</span><strong>{me.user.name}</strong></li>
          <li><span>Email</span><strong>{me.user.email}</strong></li>
          <li><span>Role</span><strong>{me.user.role === 'owner' ? 'Owner' : 'Manager'}</strong></li>
        </ul>
      </section>
      <Managers me={me} onNotice={onNotice} />
      <PasswordForm onNotice={onNotice} />
    </div>
  )
}
