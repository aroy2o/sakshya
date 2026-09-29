import { PROVENANCE_COLORS, PROVENANCE_LABELS, type ProvenanceKind } from '@/utils/provenance'

/**
 * `REAL · <source>` / `SYNTHETIC · demo` / `PLACEHOLDER` chip —
 * REAL_DATA_PLAN.md §7: "a credibility feature, not clutter." Hard rule #1
 * (Reality Pass R6): callers derive `kind` from a real `placeholder`/
 * `is_synthetic` field, never hardcode it — see `utils/provenance.ts`.
 */
export function ProvenanceChip({
  kind,
  detail,
  className,
}: {
  kind: ProvenanceKind
  detail?: string
  className?: string
}) {
  const color = PROVENANCE_COLORS[kind]
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-semibold tracking-wide ${className ?? ''}`}
      style={{ borderColor: color, color, backgroundColor: `${color}1a` }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} aria-hidden="true" />
      {PROVENANCE_LABELS[kind]}
      {detail && <span className="font-normal opacity-80">· {detail}</span>}
    </span>
  )
}
