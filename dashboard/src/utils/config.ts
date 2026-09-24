import {
  CATEGORY_KEYS,
  DAY_KEYS,
  type CategoryKey,
  type DayKey,
  type EmployeeConfig,
  type TimeRange,
  type WeightLevel,
} from '../types'

// Backend defaults, see _score_logs_for_period and docs/SCORING.md.
export const DEFAULT_CATEGORY_WEIGHTS: Record<CategoryKey, number> = {
  app_usage: 0.4,
  browser: 0.2,
  punctuality: 0.2,
  idle: 0.2,
}

export const CATEGORY_LABELS: Record<CategoryKey, string> = {
  app_usage: 'App usage',
  browser: 'Browser activity',
  punctuality: 'Punctuality',
  idle: 'Idle behaviour',
}

export const DAY_LABELS: Record<DayKey, string> = {
  mon: 'Monday',
  tue: 'Tuesday',
  wed: 'Wednesday',
  thu: 'Thursday',
  fri: 'Friday',
  sat: 'Saturday',
  sun: 'Sunday',
}

export type AppWeightRow = { key: number; name: string; level: WeightLevel }

// Form-friendly shape: percentages as whole numbers, numeric fields as strings while editing.
export type ConfigForm = {
  apps: AppWeightRow[]
  categories: Record<CategoryKey, string>
  schedule: Record<DayKey, TimeRange[]>
  minProductiveHours: string
  maxIdleMinutes: string
}

let rowKey = 0
export const nextRowKey = () => ++rowKey

const LEVELS: WeightLevel[] = ['high', 'medium', 'low']

function toLevel(value: unknown): WeightLevel {
  return LEVELS.includes(value as WeightLevel) ? (value as WeightLevel) : 'medium'
}

export function configToForm(config: EmployeeConfig | null): ConfigForm {
  const categories = {} as Record<CategoryKey, string>
  for (const key of CATEGORY_KEYS) {
    const weight = config?.category_weights?.[key] ?? DEFAULT_CATEGORY_WEIGHTS[key]
    categories[key] = String(Math.round(Number(weight) * 100))
  }

  const schedule = {} as Record<DayKey, TimeRange[]>
  for (const day of DAY_KEYS) {
    schedule[day] = (config?.schedule?.[day] ?? []).map(([start, end]) => [start, end] as TimeRange)
  }

  return {
    apps: Object.entries(config?.software_weights ?? {}).map(([name, level]) => ({
      key: nextRowKey(),
      name,
      level: toLevel(level),
    })),
    categories,
    schedule,
    minProductiveHours: String(config?.min_productive_hours ?? 6),
    maxIdleMinutes: String(config?.max_idle_minutes ?? 60),
  }
}

export type ConfigErrors = {
  apps?: string
  categories?: string
  schedule?: Partial<Record<DayKey, string>>
  minProductiveHours?: string
  maxIdleMinutes?: string
}

export function categoryTotal(form: ConfigForm): number {
  return CATEGORY_KEYS.reduce((sum, key) => sum + (Number(form.categories[key]) || 0), 0)
}

export function validateConfig(form: ConfigForm): ConfigErrors {
  const errors: ConfigErrors = {}

  const names = form.apps.map((app) => app.name.trim().toLowerCase())
  if (names.some((name) => !name)) {
    errors.apps = 'Every app needs a name'
  } else if (new Set(names).size !== names.length) {
    errors.apps = 'Each app can only be listed once'
  }

  const values = CATEGORY_KEYS.map((key) => Number(form.categories[key]))
  if (values.some((value) => !Number.isFinite(value) || value < 0 || value > 100)) {
    errors.categories = 'Each weight must be between 0 and 100'
  } else if (categoryTotal(form) !== 100) {
    errors.categories = `Weights must add up to 100% (currently ${categoryTotal(form)}%)`
  }

  const scheduleErrors: Partial<Record<DayKey, string>> = {}
  for (const day of DAY_KEYS) {
    const ranges = [...form.schedule[day]].sort((a, b) => a[0].localeCompare(b[0]))
    if (ranges.some(([start, end]) => !start || !end)) {
      scheduleErrors[day] = 'Fill in both start and end times'
    } else if (ranges.some(([start, end]) => start >= end)) {
      scheduleErrors[day] = 'End time must be after start time'
    } else if (ranges.some((range, index) => index > 0 && range[0] < ranges[index - 1][1])) {
      scheduleErrors[day] = 'Time blocks overlap'
    }
  }
  if (Object.keys(scheduleErrors).length > 0) errors.schedule = scheduleErrors

  const hours = Number(form.minProductiveHours)
  if (form.minProductiveHours.trim() === '' || !Number.isFinite(hours) || hours < 0 || hours > 24) {
    errors.minProductiveHours = 'Enter a number of hours between 0 and 24'
  }

  const idle = Number(form.maxIdleMinutes)
  if (form.maxIdleMinutes.trim() === '' || !Number.isInteger(idle) || idle < 0 || idle > 1440) {
    errors.maxIdleMinutes = 'Enter whole minutes between 0 and 1440'
  }

  return errors
}

export function hasErrors(errors: ConfigErrors): boolean {
  return Object.keys(errors).length > 0
}

// Builds the POST /config body. job_description and role_tag live on the same backend row,
// so they are passed through from the employee profile to avoid wiping them.
export function formToPayload(
  form: ConfigForm,
  profile: { job_description: string | null; role_tag: string | null },
) {
  const software_weights: Record<string, WeightLevel> = {}
  for (const app of form.apps) software_weights[app.name.trim()] = app.level

  const category_weights = {} as Record<CategoryKey, number>
  for (const key of CATEGORY_KEYS) category_weights[key] = Number(form.categories[key]) / 100

  const schedule: Partial<Record<DayKey, TimeRange[]>> = {}
  for (const day of DAY_KEYS) {
    if (form.schedule[day].length > 0) {
      schedule[day] = [...form.schedule[day]].sort((a, b) => a[0].localeCompare(b[0]))
    }
  }

  return {
    job_description: profile.job_description,
    role_tag: profile.role_tag,
    software_weights,
    category_weights,
    schedule,
    min_productive_hours: Number(form.minProductiveHours),
    max_idle_minutes: Number(form.maxIdleMinutes),
  }
}
