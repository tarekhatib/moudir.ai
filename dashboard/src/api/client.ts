// Central place for backend API calls. Base URL configurable via .env (VITE_API_URL).
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// FastAPI returns errors as {detail: string} or {detail: [{msg: ...}]} for validation errors.
async function toApiError(res: Response, fallback: string): Promise<ApiError> {
  let message = fallback
  try {
    const body = await res.json()
    if (typeof body?.detail === 'string') {
      message = body.detail
    } else if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
      message = body.detail.map((item: { msg: string }) => item.msg).join(', ')
    }
  } catch {
    // Body was not JSON; keep the fallback message.
  }
  return new ApiError(message, res.status)
}

async function request<T>(method: string, path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError('Cannot reach the backend. Is it running?', 0)
  }
  if (!res.ok) throw await toApiError(res, `${method} ${path} failed (${res.status})`)
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const apiGet = <T>(path: string, signal?: AbortSignal) => request<T>('GET', path, undefined, signal)
export const apiPost = <T>(path: string, body: unknown) => request<T>('POST', path, body)
export const apiPut = <T>(path: string, body: unknown) => request<T>('PUT', path, body)
export const apiDelete = (path: string) => request<void>('DELETE', path)

export async function apiDownload(path: string, filename: string): Promise<void> {
  let res: Response
  try {
    res = await fetch(`${API_URL}${path}`)
  } catch {
    throw new ApiError('Cannot reach the backend. Is it running?', 0)
  }
  if (!res.ok) throw await toApiError(res, `Download failed (${res.status})`)

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unknown error'
}

export function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}
