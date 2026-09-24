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
