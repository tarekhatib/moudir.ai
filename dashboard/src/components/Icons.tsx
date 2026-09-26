// 16px line icons, 1.5px stroke, drawn on a 16 grid. They inherit currentColor.
type IconProps = { className?: string }

const base = {
  width: 16,
  height: 16,
  viewBox: '0 0 16 16',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  'aria-hidden': true,
}

export function TeamIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <rect x="2" y="2" width="5" height="5" rx="1" />
      <rect x="9" y="2" width="5" height="5" rx="1" />
      <rect x="2" y="9" width="5" height="5" rx="1" />
      <rect x="9" y="9" width="5" height="5" rx="1" />
    </svg>
  )
}

export function PeopleIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <circle cx="6" cy="5.5" r="2.5" />
      <path d="M1.75 13.5c.5-2.3 2.2-3.5 4.25-3.5s3.75 1.2 4.25 3.5" />
      <path d="M10.5 3.2a2.5 2.5 0 0 1 0 4.6M12.2 10.3c1.1.5 1.8 1.6 2.05 3.2" />
    </svg>
  )
}

export function DownloadIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M8 2.5v8M4.75 7.25 8 10.5l3.25-3.25M2.5 13.5h11" />
    </svg>
  )
}

export function PlusIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M8 3v10M3 8h10" />
    </svg>
  )
}

export function AccountIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <circle cx="8" cy="8" r="6" />
      <circle cx="8" cy="6.5" r="2" />
      <path d="M4.2 12.5c.8-1.5 2.1-2.25 3.8-2.25s3 .75 3.8 2.25" />
    </svg>
  )
}

export function SignOutIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M6.5 2.5h-3a1 1 0 0 0-1 1v9a1 1 0 0 0 1 1h3M10.5 11 13.5 8l-3-3M13.5 8H6" />
    </svg>
  )
}
