import { useEffect, useState } from 'react'
import { EvidenceContent } from '@/components/drawer/EvidenceContent'
import { ErrorState } from '@/components/layout/ErrorState'
import { SkeletonBlock } from '@/components/shared/Skeleton'
import { useAssetDetail } from '@/hooks/useAssetDetail'
import { useMwsAssets } from '@/hooks/useMwsAssets'

/**
 * Beat 5 — one work, end to end, as a standalone page (not the map-pin
 * slide-over). Shares `EvidenceContent` with `AssetDrawer.tsx` so the two
 * never drift; this beat adds only the asset picker on top.
 */
export function EvidenceBeat({ mwsId }: { mwsId: string }) {
  const assetsQuery = useMwsAssets(mwsId)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  useEffect(() => {
    const firstFeature = assetsQuery.data?.features[0]
    if (selectedId === null && firstFeature) {
      setSelectedId(firstFeature.properties.id)
    }
  }, [assetsQuery.data, selectedId])

  const assetQuery = useAssetDetail(selectedId ?? undefined)

  return (
    <div className="mx-auto max-w-3xl p-4 sm:p-6">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <h2 className="text-lg font-semibold text-(--text)">Evidence drawer</h2>
        <label className="ml-auto flex items-center gap-2 text-xs text-(--text-muted)">
          Work
          <select
            value={selectedId ?? ''}
            onChange={(e) => setSelectedId(Number(e.target.value))}
            className="rounded-md border border-(--border-strong) bg-(--surface-2) px-2 py-1 text-(--text)"
          >
            {assetsQuery.data?.features.map((f) => (
              <option key={f.properties.id} value={f.properties.id}>
                {f.properties.work_code ?? `#${f.properties.id}`} — {f.properties.activity}
              </option>
            ))}
          </select>
        </label>
      </div>

      {(assetsQuery.isLoading || assetQuery.isLoading) && <SkeletonBlock lines={8} />}
      {assetsQuery.isError && <ErrorState message={(assetsQuery.error as Error).message} onRetry={() => assetsQuery.refetch()} />}
      {assetQuery.isError && <ErrorState message={(assetQuery.error as Error).message} onRetry={() => assetQuery.refetch()} />}
      {assetQuery.data && <EvidenceContent asset={assetQuery.data} />}
    </div>
  )
}
