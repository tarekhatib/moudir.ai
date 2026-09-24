import { useEffect } from 'react'

export type NoticeMessage = { kind: 'success' | 'error'; text: string }

type Props = {
  notice: NoticeMessage | null
  onDismiss: () => void
}

// Success messages auto-dismiss; errors stay until closed or replaced.
export function Notice({ notice, onDismiss }: Props) {
  useEffect(() => {
    if (notice?.kind !== 'success') return
    const timer = window.setTimeout(onDismiss, 3000)
    return () => window.clearTimeout(timer)
  }, [notice, onDismiss])

  if (!notice) return null

  return (
    <div className={notice.kind === 'error' ? 'error-box notice' : 'success-box notice'} role={notice.kind === 'error' ? 'alert' : 'status'}>
      <span>{notice.text}</span>
      <button type="button" className="notice-close" aria-label="Dismiss" onClick={onDismiss}>
        ×
      </button>
    </div>
  )
}
