import { PERIODS, type Period } from '../types'

type Props = {
  value: Period
  onChange: (period: Period) => void
}

export function PeriodSelector({ value, onChange }: Props) {
  return (
    <div className="segmented-control" role="group" aria-label="Select report period">
      {PERIODS.map((item) => (
        <button
          key={item}
          type="button"
          aria-pressed={value === item}
          className={value === item ? 'active' : ''}
          onClick={() => onChange(item)}
        >
          {item}
        </button>
      ))}
    </div>
  )
}
