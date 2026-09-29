import { ErrorState } from '@/components/layout/ErrorState'
import { SkeletonBlock } from '@/components/shared/Skeleton'
import { ContourMotif } from '@/components/shared/ContourMotif'
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
 * Rebuilt as a full-height hero rather than top-aligned cards over empty
 * space: the coverage percentage — the one number this whole dashboard is
 * about — is the dominant headline element, with the supporting counts
 * folded into one quiet line beneath it instead of four identical boxes.
 * The background contour motif is the same visual language a watershed
 * survey actually uses (elevation contours), tying the page to its subject
 * instead of sitting on a flat void.
 *
 * The three India-wide KPIs have no backing API endpoint —
 * `GET /districts/geotag-coverage` only covers the 3 NE states this app
 * focuses on, not a national rollup — so they're cited verbatim from
 * `docs/REAL_DATA_PLAN.md` §1 (dated, sourced) and chipped distinctly as
 * "REAL · CITED" rather than a live "REAL" chip. See `data/indiaMisFigures.ts`.
 * The NE comparison bars ARE live: aggregated client-side from every row
 * `GET /districts/geotag-coverage` actually returns (51 real districts).
 */
export function CommandStrip() {
  const { data: districts, isLoading, isError, error, refetch } = useDistrictCoverage()
  const stateTotals = districts ? aggregateByState(districts) : []
  const coveragePct = (INDIA_MIS_FIGURES.geotagged / INDIA_MIS_FIGURES.work_codes) * 100

  return (
    <div className="relative flex min-h-full flex-col items-center justify-center overflow-hidden px-4 py-10 sm:px-6">
      <ContourMotif className="opacity-90" />

      <div className="relative w-full max-w-3xl">
        <div className="mb-6 text-center sm:mb-8">
          <div className="mb-2 flex items-center justify-center gap-2">
            <h2 className="text-base font-medium text-(--text-muted)">WDC-PMKSY watershed works, India</h2>
            <ProvenanceChip kind="real-cited" />
          </div>
          <p className="text-[80px] font-semibold leading-none tracking-tight text-(--text) sm:text-[112px]">
            {coveragePct.toFixed(1)}
            <span className="align-top text-[0.4em] font-medium text-(--accent)">%</span>
          </p>
          <p className="mt-1 text-sm text-(--text-muted)">of work codes geotagged</p>
          <p className="mx-auto mt-3 flex max-w-lg flex-wrap items-baseline justify-center gap-x-5 gap-y-1 text-sm text-(--text-muted)">
            <span>
              <span className="font-medium text-(--text)">{fmt(INDIA_MIS_FIGURES.geotagged)}</span> Geotagged
            </span>
            <span>
              <span className="font-medium text-(--text)">{fmt(INDIA_MIS_FIGURES.work_codes)}</span> Work codes
            </span>
            <span>
              <span className="font-medium text-(--text)">{fmt(INDIA_MIS_FIGURES.projects)}</span> Projects
            </span>
            <span>
              <span className="font-medium text-(--text)">{fmt(INDIA_MIS_FIGURES.not_geotagged)}</span> Not geotagged
            </span>
          </p>
          <p className="mt-1 text-xs text-(--text-faint)">
            {INDIA_MIS_FIGURES.as_on}{' '}
            <a href={INDIA_MIS_FIGURES.source_url} target="_blank" rel="noreferrer" className="underline hover:text-(--accent)">
              (source)
            </a>
          </p>
        </div>

        <div className="mx-auto mb-6 h-px w-24 bg-(--border-strong) sm:mb-8" />

        <div className="mb-2 flex items-center gap-2">
          <h3 className="text-sm font-medium text-(--text)">Zooming into the Northeast</h3>
          <ProvenanceChip kind="real" detail="live" />
        </div>

        {isLoading && <SkeletonBlock lines={3} />}
        {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

        {stateTotals.length > 0 && (
          <div className="space-y-3">
            {stateTotals.map((s, i) => (
              <div key={s.state}>
                <div className="mb-1 flex items-baseline justify-between text-sm">
                  <span className="text-(--text)">{s.state}</span>
                  <span className="tabular-nums text-(--text-muted)">
                    {fmt(s.geotagged_works)} / {fmt(s.total_works)} ({s.pct.toFixed(1)}%)
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-(--surface-3)">
                  <div
                    className="h-2 rounded-full bg-(--accent)"
                    style={{ width: `${Math.min(100, s.pct)}%`, opacity: 1 - i * 0.18 }}
                  />
                </div>
              </div>
            ))}
            <p className="pt-1 text-xs text-(--text-faint)">
              {districts?.length ?? 0} districts (WDC-PMKSY 2.0 MIS Report GT2){districts?.[0]?.as_of ? `, as of ${districts[0].as_of}` : ''}.
              Assam leads; the next beat drills into Marigaon district.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
