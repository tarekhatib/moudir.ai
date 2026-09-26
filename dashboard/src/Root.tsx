import { useCallback, useEffect, useState } from 'react'
import { apiGet, apiPost, ApiError, errorMessage, setUnauthorizedHandler } from './api/client'
import App from './App'
import { AuthScreen } from './components/AuthScreen'
import type { Me } from './types'

type AuthState = { status: 'loading' } | { status: 'signed-out' } | { status: 'signed-in'; me: Me } | { status: 'error'; message: string }

// Decides between the sign-in screen and the app, and returns to sign-in when a session expires.
export default function Root() {
  const [auth, setAuth] = useState<AuthState>({ status: 'loading' })

  const checkSession = useCallback(async () => {
    setAuth({ status: 'loading' })
    try {
      setAuth({ status: 'signed-in', me: await apiGet<Me>('/auth/me') })
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) setAuth({ status: 'signed-out' })
      else setAuth({ status: 'error', message: errorMessage(error) })
    }
  }, [])

  useEffect(() => {
    void checkSession()
    setUnauthorizedHandler(() => setAuth({ status: 'signed-out' }))
    return () => setUnauthorizedHandler(null)
  }, [checkSession])

  const signOut = useCallback(async () => {
    try {
      await apiPost('/auth/logout', {})
    } finally {
      setAuth({ status: 'signed-out' })
    }
  }, [])

  if (auth.status === 'loading') {
    return <div className="auth-shell"><p className="muted">Loading…</p></div>
  }
  if (auth.status === 'error') {
    return (
      <div className="auth-shell">
        <div className="error-box" role="alert">
          {auth.message}{' '}
          <button type="button" className="link-button" onClick={() => void checkSession()}>
            Try again
          </button>
        </div>
      </div>
    )
  }
  if (auth.status === 'signed-out') {
    return <AuthScreen onSignedIn={(me) => setAuth({ status: 'signed-in', me })} />
  }
  return <App key={auth.me.user.id} me={auth.me} onSignOut={() => void signOut()} />
}
