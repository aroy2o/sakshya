import { useEffect } from 'react'
import type * as maplibregl from 'maplibre-gl'
import { useThematicLayer } from '@/hooks/useThematicLayer'
import { boundsToImageCoordinates } from '@/utils/geo'
import type { ThematicLayer } from '@/types/domain'

/**
 * Fetches and renders exactly one precomputed thematic layer (FR5.1). Only
 * mounted while its toggle is on — toggling off unmounts it and its effect
 * cleanup removes the MapLibre source/layer, so nothing accumulates.
 */
export function ThematicLayerRenderer({
  map,
  mwsId,
  layer,
}: {
  map: maplibregl.Map
  mwsId: string
  layer: ThematicLayer
}) {
  const { data } = useThematicLayer(mwsId, layer)

  useEffect(() => {
    if (!data) return

    const sourceId = `thematic-${layer}`
    const layerId = `${sourceId}-layer`

    if (data.kind === 'raster') {
      // One bounds-anchored static composite image per layer (confirmed
      // live at Sync Point 1), not an XYZ tile pyramid — an ImageSource,
      // not a tiled RasterSource.
      map.addSource(sourceId, {
        type: 'image',
        url: data.tile_url,
        coordinates: boundsToImageCoordinates(data.bounds),
      })
      map.addLayer({
        id: layerId,
        type: 'raster',
        source: sourceId,
        paint: { 'raster-opacity': 0.75 },
      })
    } else {
      map.addSource(sourceId, { type: 'geojson', data: data.geojson })
      map.addLayer({
        id: layerId,
        type: 'line',
        source: sourceId,
        paint: {
          'line-color': data.legend[0]?.color ?? '#0ea5e9',
          'line-width': 2,
        },
      })
    }

    return () => {
      if (map.getLayer(layerId)) map.removeLayer(layerId)
      if (map.getSource(sourceId)) map.removeSource(sourceId)
    }
  }, [map, layer, data])

  return null
}
