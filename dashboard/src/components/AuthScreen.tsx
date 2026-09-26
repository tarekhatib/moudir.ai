import { useState, type FormEvent } from 'react'
import { apiPost, errorMessage } from '../api/client'
import type { Me } from '../types'

type Mode = 'signin' | 'signup'

type Props = {
  onSignedIn: (me: Me) => void
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
export const MIN_PASSWORD_LENGTH = 10

export function AuthScreen({ onSignedIn }: Props) {
  const [mode, setMode] = useState<Mode>('signin')
  const [organization, setOrganization] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const switchMode = (next: Mode) => {
    setMode(next)
    setError(null)
  }

  const validate = (): string | null => {
    if (!EMAIL_PATTERN.test(email.trim())) return 'Enter a valid email address.'
    if (mode === 'signin') return password ? null : 'Enter your password.'
    if (!organization.trim()) return 'Enter your company name.'
    if (!name.trim()) return 'Enter your name.'
    if (password.length < MIN_PASSWORD_LENGTH) return `Use at least ${MIN_PASSWORD_LENGTH} characters for your password.`
    return null
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const problem = validate()
    setError(problem)
    if (problem) return

    setSubmitting(true)
    try {
      const me =
        mode === 'signin'
          ? await apiPost<Me>('/auth/login', { email, password })
          : await apiPost<Me>('/auth/signup', { organization_name: organization, name, email, password })
      onSignedIn(me)
    } catch (submitError) {
      setError(errorMessage(submitError))
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-shell">
      <form className="panel auth-card" onSubmit={(event) => void handleSubmit(event)} noValidate>
        <div className="brand">
          <img className="brand-mark" src="/favicon.svg" alt="" width={28} height={28} />
          <span className="brand-name">Moudir</span>
        </div>
        <div>
          <h1>{mode === 'signin' ? 'Sign in' : 'Create your company account'}</h1>
          <p className="muted">
            {mode === 'signin'
              ? 'Welcome back. Sign in to see how your team is doing.'
              : 'You’ll be the account owner and can invite other managers later.'}
          </p>
        </div>

        {error ? (
          <div className="error-box" role="alert">
            {error}
          </div>
        ) : null}

        {mode === 'signup' ? (
          <>
            <label>
              Company name
              <input value={organization} onChange={(e) => setOrganization(e.target.value)} autoComplete="organization" />
            </label>
            <label>
              Your name
              <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
            </label>
          </>
        ) : null}
        <label>
          Work email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
          />
          {mode === 'signup' ? <span className="stat-hint">At least {MIN_PASSWORD_LENGTH} characters</span> : null}
        </label>

        <button type="submit" className="primary-button" disabled={submitting}>
          {submitting ? 'Please wait…' : mode === 'signin' ? 'Sign in' : 'Create account'}
        </button>

        <p className="muted auth-switch">
          {mode === 'signin' ? 'New to Moudir? ' : 'Already have an account? '}
          <button type="button" className="link-button" onClick={() => switchMode(mode === 'signin' ? 'signup' : 'signin')}>
            {mode === 'signin' ? 'Create a company account' : 'Sign in'}
          </button>
        </p>
      </form>
    </div>
  )
}
