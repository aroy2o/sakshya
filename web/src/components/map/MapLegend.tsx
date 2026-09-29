import { useMapUi } from '@/state/mapUiStore'
import { useThematicLayer } from '@/hooks/useThematicLayer'
import { ProvenanceChip } from '@/components/shared/ProvenanceChip'
import { BAND_COLORS, BAND_LABELS, UNSCORED_COLOR, UNSCORED_LABEL } from '@/utils/band'
import { provenanceFromPlaceholderFlag } from '@/utils/provenance'
import type { ThematicLayer } from '@/types/domain'

/**
 * Band color key (always shown) + the legend of whichever thematic layer(s)
 * are currently on, read straight from that layer's own `legend` field —
 * never a legend hardcoded for a layer that isn't actually rendered.
 * React Query's cache means these hooks don't trigger extra fetches beyond
 * what `ThematicLayerRenderer` already pulled for the same layer.
 */
function ActiveLayerLegend({ mwsId, layer }: { mwsId: string; layer: ThematicLayer }) {
  const { data } = useThematicLayer(mwsId, layer)
  if (!data) return null
  return (
    <div className="mt-2">
      <div className="mb-0.5 flex items-center gap-1.5">
        <p className="text-xs font-medium capitalize text-(--text-muted)">{layer.replace(/_/g, ' ')}</p>
        <ProvenanceChip kind={provenanceFromPlaceholderFlag(data.placeholder)} />
      </div>
      {data.legend.map((entry) => (
        <div key={entry.label} className="flex items-center gap-1.5 text-xs text-(--text-muted)">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: entry.color }} />
          {entry.label}
        </div>
      ))}
    </div>
  )
}

export function MapLegend({ mwsId }: { mwsId: string }) {
  const { independentLayers, ndviVariant } = useMapUi()
  const activeLayers: ThematicLayer[] = [
    ...(independentLayers.drainage ? (['drainage'] as const) : []),
    ...(independentLayers.lulc ? (['lulc'] as const) : []),
    ...(independentLayers.water ? (['water'] as const) : []),
    ...(ndviVariant !== 'off' ? [ndviVariant] : []),
  ]

  return (
    <div className="absolute bottom-3 left-3 z-10 rounded-lg border border-(--border) bg-(--surface)/95 p-3 text-xs shadow-sm backdrop-blur">
      <p className="mb-1.5 font-semibold uppercase tracking-wide text-(--text-muted)">Evidence band</p>
      {(['verified', 'review', 'flag'] as const).map((band) => (
        <div key={band} className="flex items-center gap-1.5 text-(--text-muted)">
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: BAND_COLORS[band] }} />
          {BAND_LABELS[band]}
        </div>
      ))}
      <div className="flex items-center gap-1.5 text-(--text-muted)">
        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: UNSCORED_COLOR }} />
        {UNSCORED_LABEL}
      </div>

      {activeLayers.map((layer) => (
        <ActiveLayerLegend key={layer} mwsId={mwsId} layer={layer} />
      ))}
    </div>
  )
}
