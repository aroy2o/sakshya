import { useEffect } from 'react'
import type * as maplibregl from 'maplibre-gl'
import type { Mws } from '@/types/domain'

const SOURCE_ID = 'mws-boundary'
const FILL_LAYER_ID = 'mws-boundary-fill'
const LINE_LAYER_ID = 'mws-boundary-line'

/**
 * Renders the watershed boundary (FR5.1). Dashed outline when
 * `is_synthetic_boundary` is true (PRD §8's HydroBASINS-proxy flag) —
 * signals this isn't the official MWS polygon yet, the same transparency
 * spirit as the synthetic-asset badge, just for boundary provenance rather
 * than a single record.
 */
export function MwsBoundaryLayer({ map, mws }: { map: maplibregl.Map; mws: Mws }) {
  useEffect(() => {
    map.addSource(SOURCE_ID, {
      type: 'geojson',
      data: { type: 'Feature', properties: {}, geometry: mws.boundary },
    })
    map.addLayer({
      id: FILL_LAYER_ID,
      type: 'fill',
      source: SOURCE_ID,
      paint: { 'fill-color': '#0ea5e9', 'fill-opacity': 0.05 },
    })
    map.addLayer({
      id: LINE_LAYER_ID,
      type: 'line',
      source: SOURCE_ID,
      paint: {
        'line-color': '#0369a1',
        'line-width': 2,
        'line-dasharray': mws.is_synthetic_boundary ? [2, 2] : [1, 0],
      },
    })

    return () => {
      if (map.getLayer(LINE_LAYER_ID)) map.removeLayer(LINE_LAYER_ID)
      if (map.getLayer(FILL_LAYER_ID)) map.removeLayer(FILL_LAYER_ID)
      if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID)
    }
  }, [map, mws])

  return null
}
