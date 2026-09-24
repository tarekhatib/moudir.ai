export type Period = 'daily' | 'weekly' | 'monthly'

export const PERIODS: Period[] = ['daily', 'weekly', 'monthly']

export type Employee = {
  id: number
  name: string
  role: string | null
  email: string | null
  job_description: string | null
  role_tag: string | null
}

export type EmployeeInput = {
  name: string
  role: string
  email: string
  job_description: string
  role_tag: string
}

export type EventSummary = {
  app_focus: number
  browser_tab: number
  idle_start: number
  login: number
  outlook_activity: number
}

export type Summary = {
  employee_id: number
  period: Period
  average_score: number
  total_productive_hours: number
  total_idle_minutes: number
  event_summary: EventSummary
  // Values are either a level ("high" | "medium" | "low") or a numeric weight.
  app_weights: Record<string, string | number>
}

export type WeightLevel = 'high' | 'medium' | 'low'

export const CATEGORY_KEYS = ['app_usage', 'browser', 'punctuality', 'idle'] as const
export type CategoryKey = (typeof CATEGORY_KEYS)[number]

export const DAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const
export type DayKey = (typeof DAY_KEYS)[number]

// [start, end] as "HH:MM"
export type TimeRange = [string, string]

export type EmployeeConfig = {
  employee_id: number
  job_description: string | null
  role_tag: string | null
  software_weights: Record<string, WeightLevel>
  category_weights: Partial<Record<CategoryKey, number>>
  schedule: Partial<Record<DayKey, TimeRange[]>>
  min_productive_hours: number
  max_idle_minutes: number
}
