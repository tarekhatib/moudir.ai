export type ScoreTone = 'good' | 'warning' | 'bad' | 'none'

export function scoreTone(score: number | null): ScoreTone {
  if (score === null) return 'none'
  if (score >= 0.75) return 'good'
  if (score >= 0.5) return 'warning'
  return 'bad'
}

export function formatScore(score: number | null): string {
  return score === null ? '—' : `${Math.round(score * 100)}%`
}

// Status is never colour alone: every tone also has a word.
export const TONE_LABELS: Record<ScoreTone, string> = {
  good: 'On track',
  warning: 'Watch',
  bad: 'At risk',
  none: 'No data',
}
