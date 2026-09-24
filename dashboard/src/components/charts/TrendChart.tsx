import { useState, type MouseEvent } from 'react'

export type ChartPoint = {
  label: string // short axis label, e.g. "Sep 12"
  fullLabel: string // tooltip / table label, e.g. "Fri, Sep 12"
  value: number | null // null = no data for that day (gap in a line)
}

type Props = {
  title: string
  points: ChartPoint[]
  kind: 'line' | 'column'
  format: (value: number) => string
  valueLabel: string
  // Fixed y max (e.g. 100 for percentages); otherwise derived from the data.
  max?: number
}

const WIDTH = 640
const HEIGHT = 220
const MARGIN = { top: 14, right: 16, bottom: 28, left: 44 }
const PLOT_W = WIDTH - MARGIN.left - MARGIN.right
const PLOT_H = HEIGHT - MARGIN.top - MARGIN.bottom

function niceMax(value: number): number {
  if (value <= 0) return 1
  const magnitude = 10 ** Math.floor(Math.log10(value))
  const step = [1, 2, 2.5, 5, 10].find((candidate) => candidate * magnitude >= value) ?? 10
  return step * magnitude
}

// Column with a 4px rounded data end and a square baseline.
function columnPath(x: number, y: number, w: number, h: number): string {
  const r = Math.min(4, h, w / 2)
  return `M${x},${y + h} V${y + r} Q${x},${y} ${x + r},${y} H${x + w - r} Q${x + w},${y} ${x + w},${y + r} V${y + h} Z`
}

export function TrendChart({ title, points, kind, format, valueLabel, max }: Props) {
  const [hover, setHover] = useState<number | null>(null)

  const n = points.length
  const values = points.map((point) => point.value ?? 0)
  const yMax = max ?? niceMax(Math.max(...values, 0))
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((fraction) => fraction * yMax)
  const band = PLOT_W / Math.max(n, 1)
  const x = (index: number) => MARGIN.left + band * (index + 0.5)
  const y = (value: number) => MARGIN.top + PLOT_H * (1 - Math.min(value, yMax) / yMax)
  const labelEvery = Math.ceil(n / 7)

  // Split the line where days have no data, so gaps are not drawn as real values.
  const segments: string[] = []
  let current: string[] = []
  points.forEach((point, index) => {
    if (point.value === null) {
      if (current.length) segments.push(current.join(' '))
      current = []
    } else {
      current.push(`${current.length ? 'L' : 'M'}${x(index)},${y(point.value)}`)
    }
  })
  if (current.length) segments.push(current.join(' '))

  const lastIndex = points.map((point) => point.value !== null).lastIndexOf(true)

  const handleMove = (event: MouseEvent<SVGRectElement>) => {
    const box = event.currentTarget.getBoundingClientRect()
    const relative = (event.clientX - box.left) / box.width
    setHover(Math.max(0, Math.min(n - 1, Math.floor(relative * n))))
  }

  const hovered = hover !== null ? points[hover] : null
  const columnWidth = Math.min(24, band * 0.6)

  return (
    <figure className="chart">
      <figcaption className="chart-title">{title}</figcaption>
      <div className="chart-frame">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={`${title}, ${n} days`}>
          {ticks.map((tick) => (
            <g key={tick}>
              <line className="chart-gridline" x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={y(tick)} y2={y(tick)} />
              <text className="chart-axis" x={MARGIN.left - 8} y={y(tick)} textAnchor="end" dominantBaseline="middle">
                {format(tick)}
              </text>
            </g>
          ))}

          {points.map((point, index) =>
            index % labelEvery === 0 || index === n - 1 ? (
              <text key={point.fullLabel} className="chart-axis" x={x(index)} y={HEIGHT - 8} textAnchor="middle">
                {point.label}
              </text>
            ) : null,
          )}

          {hover !== null ? (
            <line className="chart-crosshair" x1={x(hover)} x2={x(hover)} y1={MARGIN.top} y2={MARGIN.top + PLOT_H} />
          ) : null}

          {kind === 'column'
            ? points.map((point, index) =>
                point.value ? (
                  <path
                    key={point.fullLabel}
                    className={hover === index ? 'chart-column active' : 'chart-column'}
                    d={columnPath(x(index) - columnWidth / 2, y(point.value), columnWidth, MARGIN.top + PLOT_H - y(point.value))}
                  />
                ) : null,
              )
            : null}

          {kind === 'line' ? (
            <>
              {segments.map((d) => (
                <path key={d} className="chart-line" d={d} />
              ))}
              {points.map((point, index) =>
                point.value !== null && (index === hover || index === lastIndex) ? (
                  <circle key={point.fullLabel} className="chart-dot" cx={x(index)} cy={y(point.value)} r={4} />
                ) : null,
              )}
              {lastIndex >= 0 && hover === null ? (
                <text
                  className="chart-end-label"
                  x={x(lastIndex)}
                  y={y(values[lastIndex]) - 12}
                  textAnchor={lastIndex > n - 3 ? 'end' : 'middle'}
                >
                  {format(values[lastIndex])}
                </text>
              ) : null}
            </>
          ) : null}

          <rect
            className="chart-hit"
            x={MARGIN.left}
            y={MARGIN.top}
            width={PLOT_W}
            height={PLOT_H}
            onMouseMove={handleMove}
            onMouseLeave={() => setHover(null)}
          />
        </svg>

        {hovered && hover !== null ? (
          <div
            className="chart-tooltip"
            style={{
              left: `${(x(hover) / WIDTH) * 100}%`,
              transform: `translateX(${hover > n / 2 ? 'calc(-100% - 12px)' : '12px'})`,
            }}
          >
            <span className="chart-tooltip-label">{hovered.fullLabel}</span>
            <strong>{hovered.value === null ? 'No activity' : format(hovered.value)}</strong>
          </div>
        ) : null}
      </div>

      <details className="chart-table">
        <summary>Show data table</summary>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th className="numeric">{valueLabel}</th>
            </tr>
          </thead>
          <tbody>
            {points.map((point) => (
              <tr key={point.fullLabel}>
                <td>{point.fullLabel}</td>
                <td className="numeric">{point.value === null ? '—' : format(point.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  )
}
