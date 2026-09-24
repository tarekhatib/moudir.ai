import type { Period } from '../types'

// Mirrors the backend's UTC bucketing in _score_logs_for_period (see docs/SCORING.md).
export function periodRange(period: Period, now = new Date()): { start: Date; end: Date } {
  const today = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()))
  if (period === 'daily') {
    return { start: today, end: addDays(today, 1) }
  }
  if (period === 'weekly') {
    const mondayOffset = (today.getUTCDay() + 6) % 7
    const start = addDays(today, -mondayOffset)
    return { start, end: addDays(start, 7) }
  }
  const start = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1))
  const end = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + 1, 1))
  return { start, end }
}

export function describePeriod(period: Period, now = new Date()): string {
  const { start, end } = periodRange(period, now)
  const format = (date: Date) =>
    date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
  if (period === 'daily') return format(start)
  return `${format(start)} – ${format(addDays(end, -1))}`
}

function addDays(date: Date, days: number): Date {
  const copy = new Date(date)
  copy.setUTCDate(copy.getUTCDate() + days)
  return copy
}
