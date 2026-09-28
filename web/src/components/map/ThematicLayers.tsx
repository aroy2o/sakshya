import type * as maplibregl from 'maplibre-gl'
import { ThematicLayerRenderer } from './ThematicLayerRenderer'
import type { IndependentLayerToggles, NdviVariant } from '@/state/mapUiStore'

/**
 * Mounts one `ThematicLayerRenderer` per active toggle. `drainage`/`lulc`/
 * `water` are independent checkboxes; the NDVI variant is a single
 * mutually-exclusive selection (before/after/change) — showing before and
 * after simultaneously is what `SwipeControl` (FR5.4) is for instead.
 * `hidden` is set while the swipe control is active so the two views never
 * fight for the same map canvas.
 */
export function ThematicLayers({
  map,
  mwsId,
  independentLayers,
  ndviVariant,
  hidden,
}: {
  map: maplibregl.Map
  mwsId: string
  independentLayers: IndependentLayerToggles
  ndviVariant: NdviVariant | 'off'
  hidden: boolean
}) {
  if (hidden) return null

  return (
    <>
      {independentLayers.drainage && <ThematicLayerRenderer map={map} mwsId={mwsId} layer="drainage" />}
      {independentLayers.lulc && <ThematicLayerRenderer map={map} mwsId={mwsId} layer="lulc" />}
      {independentLayers.water && <ThematicLayerRenderer map={map} mwsId={mwsId} layer="water" />}
      {ndviVariant !== 'off' && <ThematicLayerRenderer map={map} mwsId={mwsId} layer={ndviVariant} />}
    </>
  )
}
