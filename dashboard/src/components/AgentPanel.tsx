import { useState } from 'react'
import { apiDelete, apiPost, API_URL, errorMessage } from '../api/client'
import type { Employee } from '../types'

type Props = {
  employee: Employee
  onChanged: (agentTokenCreatedAt: string | null) => void
  onError: (message: string) => void
}

type TokenResponse = { agent_token: string; created_at: string }

// Absolute URL the agent should send events to (API_URL is usually the relative "/api").
function backendUrl(): string {
  return new URL(API_URL, window.location.origin).toString().replace(/\/$/, '')
}

export function AgentPanel({ employee, onChanged, onError }: Props) {
  // Plain-text token, only held in memory right after it's generated.
  const [token, setToken] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [confirming, setConfirming] = useState<'rotate' | 'revoke' | null>(null)
  const [copied, setCopied] = useState(false)

  const hasToken = employee.agent_token_created_at !== null

  const generate = async () => {
    setBusy(true)
    try {
      const response = await apiPost<TokenResponse>(`/employees/${employee.id}/agent-token`, {})
      setToken(response.agent_token)
      setCopied(false)
      onChanged(response.created_at)
    } catch (error) {
      onError(errorMessage(error))
    } finally {
      setBusy(false)
      setConfirming(null)
    }
  }

  const revoke = async () => {
    setBusy(true)
    try {
      await apiDelete(`/employees/${employee.id}/agent-token`)
      setToken(null)
      onChanged(null)
    } catch (error) {
      onError(errorMessage(error))
    } finally {
      setBusy(false)
      setConfirming(null)
    }
  }

  const copy = async () => {
    if (!token) return
    try {
      await navigator.clipboard.writeText(token)
      setCopied(true)
    } catch {
      onError('Could not copy automatically. Select the token and copy it manually.')
    }
  }

  return (
    <section className="panel form-panel">
      <h2>Desktop agent</h2>
      <p className="muted panel-intro">
        The Moudir agent runs on {employee.name}’s computer and sends activity to your account. Each employee has their
        own token, which tells Moudir whose activity it is.
      </p>

      <p>
        Status:{' '}
        {hasToken ? (
          <strong>Token issued {new Date(employee.agent_token_created_at!).toLocaleString()}</strong>
        ) : (
          <strong>No token yet</strong>
        )}
      </p>

      {token ? (
        <div className="token-box">
          <p>
            <strong>Copy this token now.</strong> For security it won’t be shown again. If you lose it, generate a new
            one.
          </p>
          <div className="token-row">
            <code className="token-value">{token}</code>
            <button type="button" className="secondary-button" onClick={() => void copy()}>
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <p className="muted">Put these two lines in the agent’s <code>.env</code> file:</p>
          <pre className="token-env">{`BACKEND_URL=${backendUrl()}\nAGENT_TOKEN=${token}`}</pre>
        </div>
      ) : null}

      {confirming ? (
        <div className="confirm-box" role="alertdialog" aria-label="Confirm">
          <p>
            {confirming === 'rotate'
              ? 'Generate a new token? The agent using the current token will stop sending activity until you update it.'
              : 'Revoke the token? The agent will stop sending activity until you generate a new token.'}
          </p>
          <div className="form-actions">
            <button
              type="button"
              className={confirming === 'rotate' ? 'primary-button' : 'danger-button'}
              onClick={() => void (confirming === 'rotate' ? generate() : revoke())}
              disabled={busy}
            >
              {busy ? 'Working…' : confirming === 'rotate' ? 'Yes, generate new token' : 'Yes, revoke'}
            </button>
            <button type="button" className="secondary-button" onClick={() => setConfirming(null)} disabled={busy}>
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="form-actions">
          <button
            type="button"
            className="primary-button"
            onClick={() => (hasToken ? setConfirming('rotate') : void generate())}
            disabled={busy}
          >
            {busy ? 'Working…' : hasToken ? 'Generate new token' : 'Generate token'}
          </button>
          {hasToken ? (
            <button type="button" className="danger-link" onClick={() => setConfirming('revoke')} disabled={busy}>
              Revoke token
            </button>
          ) : null}
        </div>
      )}
    </section>
  )
}
