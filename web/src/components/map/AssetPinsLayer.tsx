import { useEffect } from 'react'
import type * as maplibregl from 'maplibre-gl'
import type { MapLayerMouseEvent } from 'maplibre-gl'
import { BAND_COLORS, UNSCORED_COLOR } from '@/utils/band'
import type { AssetPinFeatureCollection } from '@/types/domain'

const SOURCE_ID = 'asset-pins'
const LAYER_ID = 'asset-pins-circle'

/**
 * FR5.2 — asset pins coloured by band. `band` is nullable (not yet scored),
 * so the MapLibre match expression has to handle null explicitly rather
 * than let an unscored pin fall through to some arbitrary default color.
 */
export function AssetPinsLayer({
  map,
  featureCollection,
  onSelect,
}: {
  map: maplibregl.Map
  featureCollection: AssetPinFeatureCollection
  onSelect: (id: number) => void
}) {
  useEffect(() => {
    map.addSource(SOURCE_ID, { type: 'geojson', data: featureCollection })
    map.addLayer({
      id: LAYER_ID,
      type: 'circle',
      source: SOURCE_ID,
      paint: {
        'circle-radius': 8,
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
        'circle-color': [
          'match',
          ['coalesce', ['get', 'band'], 'unscored'],
          'verified',
          BAND_COLORS.verified,
          'review',
          BAND_COLORS.review,
          'flag',
          BAND_COLORS.flag,
          UNSCORED_COLOR, // fallback for 'unscored' (band === null)
        ],
      },
    })

    const handleClick = (e: MapLayerMouseEvent) => {
      const feature = e.features?.[0]
      const id = feature?.properties?.id as number | undefined
      if (id !== undefined) onSelect(id)
    }
    const handleEnter = () => {
      map.getCanvas().style.cursor = 'pointer'
    }
    const handleLeave = () => {
      map.getCanvas().style.cursor = ''
    }

    map.on('click', LAYER_ID, handleClick)
    map.on('mouseenter', LAYER_ID, handleEnter)
    map.on('mouseleave', LAYER_ID, handleLeave)

    return () => {
      map.off('click', LAYER_ID, handleClick)
      map.off('mouseenter', LAYER_ID, handleEnter)
      map.off('mouseleave', LAYER_ID, handleLeave)
      if (map.getLayer(LAYER_ID)) map.removeLayer(LAYER_ID)
      if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID)
    }
  }, [map, featureCollection, onSelect])

  return null
}
