import type { ReactNode } from 'react'

/** Big KPI numeral per REAL_DATA_PLAN.md §7's design brief ("big KPI numerals"). */
export function KpiNumeral({
  value,
  label,
  sublabel,
  chip,
}: {
  value: string
  label: string
  sublabel?: string
  chip?: ReactNode
}) {
  return (
    <div className="min-w-[9rem]">
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold tabular-nums text-[var(--text)] sm:text-4xl">{value}</span>
        {chip}
      </div>
      <p className="mt-0.5 text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">{label}</p>
      {sublabel && <p className="text-[11px] text-[var(--text-faint)]">{sublabel}</p>}
    </div>
  )
}
