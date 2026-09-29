import { useQueries } from '@tanstack/react-query'
import { api } from '@/api'
import { ErrorState } from '@/components/layout/ErrorState'
import { SkeletonBlock } from '@/components/shared/Skeleton'
import { ProvenanceChip } from '@/components/shared/ProvenanceChip'
import { useMwsAssets } from '@/hooks/useMwsAssets'
import { useProgrammeMarigaon } from '@/hooks/useProgrammeMarigaon'
import type { ProgrammeMarigaon } from '@/types/domain'

type ModerationStage = ProgrammeMarigaon['moderation_backlog']['pre']

const STAGE_LABELS: Record<'pre' | 'mid' | 'post', string> = {
  pre: 'Pre-implementation',
  mid: 'Mid-implementation',
  post: 'Post-implementation',
}

function StageBar({ stage }: { stage: ModerationStage }) {
  const total = stage.accepted + stage.yet_to_moderate + stage.rejected + stage.not_submitted + stage.mixed + stage.other
  const seg = (n: number) => (total > 0 ? (n / total) * 100 : 0)
  return (
    <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-(--surface-3)">
      <div className="bg-(--verified)" style={{ width: `${seg(stage.accepted)}%` }} title={`Accepted: ${stage.accepted}`} />
      <div className="bg-(--placeholder)" style={{ width: `${seg(stage.yet_to_moderate)}%` }} title={`Yet to moderate: ${stage.yet_to_moderate}`} />
      <div className="bg-(--flag)" style={{ width: `${seg(stage.rejected)}%` }} title={`Rejected: ${stage.rejected}`} />
      <div className="bg-(--unscored)" style={{ width: `${seg(stage.not_submitted)}%` }} title={`Not submitted: ${stage.not_submitted}`} />
      <div className="bg-(--synthetic)" style={{ width: `${seg(stage.mixed + stage.other)}%` }} title={`Mixed/other: ${stage.mixed + stage.other}`} />
    </div>
  )
}

/**
 * Beat 6 — real moderation backlog (`GET /programme/marigaon`, hard rule
 * #4) plus a demo-scale preview of what a ranked review queue looks like
 * over the 17 seeded assets. `POST /assets/{id}/review` doesn't exist yet
 * (Phase 6 backend, not built) — this section is display-only, labelled as
 * such, not wired to fake actions.
 */
export function ModerationQueue({ mwsId }: { mwsId: string }) {
  const { data: programme, isLoading, isError, error, refetch } = useProgrammeMarigaon()
  const assetsQuery = useMwsAssets(mwsId)

  const assetIds = assetsQuery.data?.features.map((f) => f.properties.id) ?? []
  const detailQueries = useQueries({
    queries: assetIds.map((id) => ({
      queryKey: ['asset-detail', id],
      queryFn: () => api.getAssetDetail(id),
    })),
  })
  const loadedAssets = detailQueries.map((q) => q.data).filter((a): a is NonNullable<typeof a> => a !== undefined)
  const ranked = [...loadedAssets].sort((a, b) => {
    const aFlag = a.ai_result?.needs_review ? 0 : 1
    const bFlag = b.ai_result?.needs_review ? 0 : 1
    if (aFlag !== bFlag) return aFlag - bFlag
    return (a.geo_score ?? 30) - (b.geo_score ?? 30)
  })

  return (
    <div className="mx-auto max-w-4xl p-4 sm:p-6">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <h2 className="text-lg font-semibold text-(--text)">Moderation queue</h2>
        <ProvenanceChip kind="real" detail="WDC-PMKSY MIS, live" />
      </div>

      {isLoading && <SkeletonBlock lines={5} />}
      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {programme && (
        <>
          <div className="mb-4 rounded-lg border border-(--border) bg-(--surface) p-4">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold tabular-nums text-(--placeholder)">
                {programme.moderation_backlog.pre.yet_to_moderate_pct_of_geotagged}%
              </span>
              <span className="text-sm text-(--text-muted)">
                of {programme.moderation_backlog_denominator} geotagged works are pre-implementation
                &quot;Yet to Moderate&quot; ({programme.moderation_backlog.pre.yet_to_moderate}/
                {programme.moderation_backlog_denominator})
              </span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-(--text-faint)">{programme.moderation_backlog_note}</p>
          </div>

          <div className="mb-4 space-y-3 rounded-lg border border-(--border) bg-(--surface) p-4">
            {(['pre', 'mid', 'post'] as const).map((key) => {
              const stage = programme.moderation_backlog[key]
              return (
                <div key={key}>
                  <div className="mb-1 flex items-baseline justify-between text-xs">
                    <span className="font-medium text-(--text)">{STAGE_LABELS[key]}</span>
                    <span className="text-(--text-muted)">
                      {stage.accepted} accepted · {stage.yet_to_moderate} yet to moderate · {stage.rejected} rejected ·{' '}
                      {stage.not_submitted} not submitted
                      {stage.mixed + stage.other > 0 ? ` · ${stage.mixed + stage.other} mixed/other` : ''}
                    </span>
                  </div>
                  <StageBar stage={stage} />
                </div>
              )
            })}
            <p className="pt-1 text-[11px] text-(--text-faint)">
              Source: {programme.source_report}, {programme.focus_project.project_name}.
            </p>
          </div>
        </>
      )}

      <div className="rounded-lg border border-(--border) bg-(--surface) p-4">
        <div className="mb-2 flex items-center gap-2">
          <h3 className="text-sm font-semibold text-(--text)">Demo queue preview</h3>
          <ProvenanceChip kind="synthetic" detail="demo assets" />
        </div>
        <p className="mb-2 text-[11px] text-(--text-faint)">
          Ranked: needs-review flags first, then geo-integrity score ascending. Review actions
          (Confirm/Reject) aren&apos;t wired to a backend endpoint yet — preview only.
        </p>
        {assetsQuery.isLoading && <SkeletonBlock lines={4} />}
        {ranked.length > 0 && (
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-(--border) text-(--text-faint)">
                <th className="py-1 pr-2">Work</th>
                <th className="py-1 pr-2">Category</th>
                <th className="py-1 pr-2">Geo score</th>
                <th className="py-1">AI flag</th>
              </tr>
            </thead>
            <tbody>
              {ranked.map((a) => (
                <tr key={a.id} className="border-b border-(--border)">
                  <td className="py-1 pr-2 text-(--text)">{a.work_code ?? `#${a.id}`}</td>
                  <td className="py-1 pr-2 text-(--text-muted)">{a.category}</td>
                  <td className="py-1 pr-2 font-mono text-(--text-muted)">{a.geo_score ?? '—'}/30</td>
                  <td className="py-1">
                    {a.ai_result?.needs_review ? (
                      <span className="text-amber-300">needs review</span>
                    ) : (
                      <span className="text-(--text-faint)">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
