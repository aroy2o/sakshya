import { ErrorState } from '@/components/layout/ErrorState'
import { SkeletonBlock } from '@/components/shared/Skeleton'
import { ProvenanceChip } from '@/components/shared/ProvenanceChip'
import { useMws } from '@/hooks/useMws'
import { useProgrammeMarigaon } from '@/hooks/useProgrammeMarigaon'
import { useProvenance } from '@/hooks/useProvenance'
import { useWatershedImpact } from '@/hooks/useWatershedImpact'
import { provenanceFromPlaceholderFlag } from '@/utils/provenance'

const REALITY_TIERS = [
  {
    tier: '1 — Real, automated',
    detail: 'MWS boundary, satellite series, programme stats, work-code registry aggregates, WRIS water layers.',
  },
  {
    tier: '2 — Real, semi-manual',
    detail: 'A human-curated sample of real geotagged assets with photos, from the public Bhuvan MGNREGA viewer (none loaded yet — optional R7).',
  },
  {
    tier: '3 — Synthetic, on purpose',
    detail: 'Planted bad records (duplicate photo, out-of-boundary, mismatch) and AI-generated demo photos — always is_synthetic=true, never a real work code.',
  },
]

/**
 * Beat 7 — a printable summary of what this session showed (`window.print()`,
 * no backend report endpoint exists yet) plus a "Methods & limits" panel
 * built entirely from real `GET /provenance` + `watershed-impact` caveats +
 * the reality-ladder tiers (REAL_DATA_PLAN.md §3) — no number here that
 * an API didn't actually return.
 */
export function ReportAndMethods({ mwsId }: { mwsId: string }) {
  const mwsQuery = useMws(mwsId)
  const programmeQuery = useProgrammeMarigaon()
  const impactQuery = useWatershedImpact(mwsId)
  const provenanceQuery = useProvenance()

  return (
    <div className="mx-auto max-w-3xl p-4 sm:p-6">
      <div className="no-print mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-(--text)">Report & methods</h2>
        <button
          type="button"
          onClick={() => window.print()}
          className="rounded-md bg-(--accent) px-3 py-1.5 text-xs font-semibold text-(--bg) hover:brightness-110"
        >
          Export report (print / save as PDF)
        </button>
      </div>

      <section id="printable-report" className="rounded-lg border border-(--border) bg-(--surface) p-4">
        <h3 className="mb-2 text-sm font-semibold text-(--text)">Watershed report summary</h3>
        {mwsQuery.isLoading && <SkeletonBlock lines={3} />}
        {mwsQuery.data && (
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-(--text-muted)">
            <dt>Watershed</dt>
            <dd className="text-right text-(--text)">{mwsQuery.data.name}</dd>
            <dt>District</dt>
            <dd className="text-right text-(--text)">{mwsQuery.data.district}, {mwsQuery.data.state}</dd>
            <dt>Boundary</dt>
            <dd className="text-right">
              <ProvenanceChip kind={mwsQuery.data.is_synthetic_boundary ? 'synthetic' : 'real'} />
            </dd>
            {programmeQuery.data && (
              <>
                <dt>Focus project</dt>
                <dd className="text-right text-(--text)">{programmeQuery.data.focus_project.project_name}</dd>
                <dt>Pre-implementation backlog</dt>
                <dd className="text-right text-(--text)">
                  {programmeQuery.data.moderation_backlog.pre.yet_to_moderate_pct_of_geotagged}% yet to moderate
                </dd>
              </>
            )}
            {impactQuery.data && (
              <>
                <dt>NDVI effect (treated − control)</dt>
                <dd className="text-right text-(--text)">
                  {impactQuery.data.summary.NDVI.effect >= 0 ? '+' : ''}
                  {impactQuery.data.summary.NDVI.effect.toFixed(3)}{' '}
                  <ProvenanceChip kind={provenanceFromPlaceholderFlag(impactQuery.data.summary.placeholder)} />
                </dd>
              </>
            )}
          </dl>
        )}
      </section>

      <section className="mt-4 rounded-lg border border-(--border) bg-(--surface) p-4">
        <h3 className="mb-2 text-sm font-semibold text-(--text)">Reality ladder</h3>
        <ul className="space-y-2 text-xs text-(--text-muted)">
          {REALITY_TIERS.map((t) => (
            <li key={t.tier}>
              <span className="font-medium text-(--text)">{t.tier}</span> — {t.detail}
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-4 rounded-lg border border-(--border) bg-(--surface) p-4">
        <h3 className="mb-2 text-sm font-semibold text-(--text)">Data sources ({provenanceQuery.data?.length ?? 0})</h3>
        {provenanceQuery.isLoading && <SkeletonBlock lines={4} />}
        {provenanceQuery.isError && (
          <ErrorState message={(provenanceQuery.error as Error).message} onRetry={() => provenanceQuery.refetch()} />
        )}
        <ul className="max-h-72 space-y-3 overflow-y-auto text-xs">
          {provenanceQuery.data?.map((p) => (
            <li key={p.name} className="border-b border-(--border) pb-2 last:border-0">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="font-medium text-(--text)">{p.name}</span>
                <ProvenanceChip kind={p.is_synthetic ? 'synthetic' : 'real'} />
              </div>
              <p className="mt-0.5 text-(--text-faint)">{p.licence}</p>
              {p.source_url && (
                <a href={p.source_url} target="_blank" rel="noreferrer" className="text-(--accent) underline">
                  {p.source_url}
                </a>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
