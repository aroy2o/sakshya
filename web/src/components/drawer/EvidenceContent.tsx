import { AiClassifierCard } from './AiClassifierCard'
import { GeoIntegrityChecklist } from './GeoIntegrityChecklist'
import { PhotoPanel } from './PhotoPanel'
import { SatelliteChips } from './SatelliteChips'
import { ScoreBreakdown } from './ScoreBreakdown'
import { ScoreReasonText } from './ScoreReasonText'
import { ProvenanceChip } from '@/components/shared/ProvenanceChip'
import { useClassifierBenchmark } from '@/hooks/useClassifierBenchmark'
import type { AssetDetail } from '@/types/domain'

/**
 * The evidence sections shared by `AssetDrawer` (map-pin slide-over) and
 * beat 5's standalone `EvidenceBeat` — factored out at Reality Pass R6 so
 * neither duplicates the photos → checklist → AI reading → satellite →
 * score composition. Leads with a provenance chip: every current asset is
 * Tier 3 synthetic demo data (REAL_DATA_PLAN.md §3) — shown honestly, not
 * disguised as a real work.
 *
 * The two-column split below is a CSS container query (`@container`/`@lg:`),
 * not a viewport media query or a layout prop — it responds to *this
 * component's own* width, so the same markup renders as one narrow column
 * inside `AssetDrawer`'s ~28rem slide-over (correct there) and as two
 * columns inside beat 5's wider standalone page (fixing that page's
 * left-column-with-empty-space-on-the-right issue), with no branching and
 * no risk of the drawer accidentally picking up the wide layout.
 */
export function EvidenceContent({ asset }: { asset: AssetDetail }) {
  const { data: benchmark } = useClassifierBenchmark()

  return (
    <div className="@container">
      <div className="mb-5 flex flex-wrap items-center gap-2">
        <ProvenanceChip kind={asset.is_synthetic ? 'synthetic' : 'real'} detail={asset.is_synthetic ? 'demo' : asset.photo_source ?? undefined} />
        {asset.work_code && <span className="text-xs text-(--text-faint)">Work code: {asset.work_code}</span>}
      </div>
      <div className="space-y-5 @lg:grid @lg:grid-cols-2 @lg:gap-x-8 @lg:gap-y-0 @lg:space-y-0">
        <div className="space-y-5">
          <PhotoPanel asset={asset} />
          <GeoIntegrityChecklist flags={asset.geo_flags} geoScore={asset.geo_score} />
          <AiClassifierCard result={asset.ai_result} visualScore={asset.visual_score} benchmark={benchmark} />
        </div>
        <div className="space-y-5">
          <SatelliteChips asset={asset} />
          <ScoreBreakdown asset={asset} />
          <ScoreReasonText asset={asset} />
        </div>
      </div>
    </div>
  )
}
