import { ErrorState } from '@/components/layout/ErrorState'
import { SkeletonBlock } from '@/components/shared/Skeleton'
import { KpiNumeral } from '@/components/shared/KpiNumeral'
import { ProvenanceChip } from '@/components/shared/ProvenanceChip'
import { INDIA_MIS_FIGURES } from '@/data/indiaMisFigures'
import { useDistrictCoverage } from '@/hooks/useDistrictCoverage'
import { aggregateByState } from '@/utils/neStateTotals'

function fmt(n: number): string {
  return n.toLocaleString('en-IN')
}

/**
 * Beat 1 — India-wide MIS numbers, then how the Northeast compares.
 *
 * The three India-wide KPIs (top row) have no backing API endpoint —
 * `GET /districts/geotag-coverage` only covers the 3 NE states this app
 * focuses on, not a national rollup — so they're cited verbatim from
 * `docs/REAL_DATA_PLAN.md` §1 (dated, sourced) and chipped distinctly as
 * "REAL · CITED" rather than a live "REAL" chip, so nobody mistakes them
 * for a `GET` this app actually made. See `data/indiaMisFigures.ts`.
 *
 * The NE comparison bars below ARE live: aggregated client-side from every
 * row `GET /districts/geotag-coverage` actually returns (51 real districts).
 */
export function CommandStrip() {
  const { data: districts, isLoading, isError, error, refetch } = useDistrictCoverage()
  const stateTotals = districts ? aggregateByState(districts) : []

  return (
    <div className="mx-auto max-w-4xl p-4 sm:p-6">
      <div className="mb-4">
        <div className="mb-1 flex flex-wrap items-center gap-2">
          <h2 className="text-lg font-semibold text-(--text)">India — WDC-PMKSY geotag coverage</h2>
          <ProvenanceChip kind="real-cited" />
        </div>
        <p className="text-xs text-(--text-faint)">
          {INDIA_MIS_FIGURES.as_on} ·{' '}
          <a href={INDIA_MIS_FIGURES.source_url} target="_blank" rel="noreferrer" className="underline hover:text-(--accent)">
            source
          </a>
        </p>
      </div>

      <div className="mb-6 flex flex-wrap gap-8 rounded-lg border border-(--border) bg-(--surface) p-4">
        <KpiNumeral value={fmt(INDIA_MIS_FIGURES.projects)} label="Projects" />
        <KpiNumeral value={fmt(INDIA_MIS_FIGURES.work_codes)} label="Work codes" />
        <KpiNumeral
          value={fmt(INDIA_MIS_FIGURES.geotagged)}
          label="Geotagged"
          sublabel={`${((INDIA_MIS_FIGURES.geotagged / INDIA_MIS_FIGURES.work_codes) * 100).toFixed(1)}% of all work codes`}
        />
        <KpiNumeral value={fmt(INDIA_MIS_FIGURES.not_geotagged)} label="Not geotagged" />
      </div>

      <div className="mb-2 flex items-center gap-2">
        <h3 className="text-sm font-semibold text-(--text)">Northeast India — geotag coverage by state</h3>
        <ProvenanceChip kind="real" detail="live" />
      </div>

      {isLoading && <SkeletonBlock lines={3} />}
      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {stateTotals.length > 0 && (
        <div className="space-y-2 rounded-lg border border-(--border) bg-(--surface) p-4">
          {stateTotals.map((s) => (
            <div key={s.state}>
              <div className="mb-0.5 flex items-baseline justify-between text-xs">
                <span className="font-medium text-(--text)">{s.state}</span>
                <span className="text-(--text-muted)">
                  {fmt(s.geotagged_works)} / {fmt(s.total_works)} · {s.pct.toFixed(1)}%
                </span>
              </div>
              <div className="h-2.5 w-full rounded-full bg-(--surface-3)">
                <div
                  className="h-2.5 rounded-full bg-(--accent)"
                  style={{ width: `${Math.min(100, s.pct)}%` }}
                />
              </div>
            </div>
          ))}
          <p className="pt-1 text-[11px] text-(--text-faint)">
            {districts?.length ?? 0} districts, {districts?.[0]?.as_of ? `as of ${districts[0].as_of}` : ''} · WDC-PMKSY 2.0 MIS
            Report GT2.
          </p>
        </div>
      )}
    </div>
  )
}
