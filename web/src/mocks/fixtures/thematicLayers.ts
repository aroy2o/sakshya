/**
 * Mocks for `GET /mws/{id}/thematic/{layer}`. Envelope confirmed against
 * live `ndvi_before` (raster) and `drainage` (vector) responses at Sync
 * Point 1 (2026-09-28) — see src/schemas/domain.ts's header comment.
 *
 * Raster `tile_url`s below point at placehold.co static images as a
 * DEV-ONLY placeholder texture (each labelled with its own layer name so
 * it's self-evidently not real data), matching the real shape: ONE
 * bounds-anchored static image per layer, not an XYZ tile pyramid — see
 * ThematicLayerRenderer.tsx / SwipeControl.tsx, which render these as
 * MapLibre ImageSources accordingly. None of this ships past mock mode
 * (VITE_API_MODE=mock only), and `placeholder: true` on every fixture
 * matches the real backend's current state (no GEE credentials wired up).
 */
import type { ThematicLayer, ThematicLayerResponse } from '@/types/domain'

const MWS_BOUNDS: [number, number, number, number] = [92.05, 26.02, 92.55, 26.38]

function placeholderImage(label: string, color: string): string {
  return `https://placehold.co/1024x768/${color}/ffffff/png?text=${encodeURIComponent(label)}`
}

const ndviLegend = [
  { color: '#a50026', label: 'Low NDVI (mock placeholder)' },
  { color: '#fee08b', label: 'Medium NDVI (mock placeholder)' },
  { color: '#1a9850', label: 'High NDVI (mock placeholder)' },
]

const ndviChangeLegend = [
  { color: '#d73027', label: 'NDVI decrease (mock placeholder)' },
  { color: '#f7f7f7', label: 'No change (mock placeholder)' },
  { color: '#1a9850', label: 'NDVI increase (mock placeholder)' },
]

const waterLegend = [
  { color: '#f0f0f0', label: 'No water (mock placeholder)' },
  { color: '#2166ac', label: 'Surface water (mock placeholder)' },
]

const lulcLegend = [
  { color: '#a6611a', label: 'Built-up / bare (mock placeholder)' },
  { color: '#dfc27d', label: 'Cropland (mock placeholder)' },
  { color: '#80cdc1', label: 'Forest / tree cover (mock placeholder)' },
  { color: '#018571', label: 'Water (mock placeholder)' },
]

export const thematicLayerFixtures: Record<ThematicLayer, ThematicLayerResponse> = {
  drainage: {
    layer: 'drainage',
    kind: 'vector',
    bounds: MWS_BOUNDS,
    legend: [{ color: '#0ea5e9', label: 'Drainage line (Strahler order, mock placeholder)' }],
    placeholder: true,
    geojson: {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          properties: { strahler_order: 2 },
          geometry: {
            type: 'LineString',
            coordinates: [
              [92.1, 26.05],
              [92.2, 26.15],
              [92.3, 26.25],
              [92.4, 26.33],
            ],
          },
        },
      ],
    },
  },
  lulc: {
    layer: 'lulc',
    kind: 'raster',
    bounds: MWS_BOUNDS,
    legend: lulcLegend,
    placeholder: true,
    tile_url: placeholderImage('LULC (MOCK)', 'a6611a'),
  },
  ndvi_before: {
    layer: 'ndvi_before',
    kind: 'raster',
    bounds: MWS_BOUNDS,
    legend: ndviLegend,
    placeholder: true,
    tile_url: placeholderImage('NDVI BEFORE (MOCK)', '1a9850'),
  },
  ndvi_after: {
    layer: 'ndvi_after',
    kind: 'raster',
    bounds: MWS_BOUNDS,
    legend: ndviLegend,
    placeholder: true,
    tile_url: placeholderImage('NDVI AFTER (MOCK)', '1a9850'),
  },
  ndvi_change: {
    layer: 'ndvi_change',
    kind: 'raster',
    bounds: MWS_BOUNDS,
    legend: ndviChangeLegend,
    placeholder: true,
    tile_url: placeholderImage('NDVI CHANGE (MOCK)', 'd73027'),
  },
  water: {
    layer: 'water',
    kind: 'raster',
    bounds: MWS_BOUNDS,
    legend: waterLegend,
    placeholder: true,
    tile_url: placeholderImage('WATER (MOCK)', '2166ac'),
  },
}
