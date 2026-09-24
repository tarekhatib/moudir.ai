export function scoreTone(score: number): 'good' | 'warning' | 'bad' {
  if (score >= 0.75) return 'good'
  if (score >= 0.5) return 'warning'
  return 'bad'
}

// Software weights are stored as levels ("high") or numbers (0.8) depending on who saved them.
export function formatWeight(value: string | number): string {
  if (typeof value === 'number') return value.toFixed(2)
  const asNumber = Number(value)
  return Number.isNaN(asNumber) ? value : asNumber.toFixed(2)
}
