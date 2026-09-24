export function scoreTone(score: number): 'good' | 'warning' | 'bad' {
  if (score >= 0.75) return 'good'
  if (score >= 0.5) return 'warning'
  return 'bad'
}

