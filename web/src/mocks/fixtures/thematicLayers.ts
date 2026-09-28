/**
 * Mocks for `GET /mws/{id}/thematic/{layer}`. PRD §9 only says this
 * endpoint returns "Tile URL or GeoJSON" — the `kind: 'raster' | 'vector'`
 * envelope here is this app's own design (flagged as an open assumption,
 * see src/schemas/domain.ts's header comment), built to be confirmed
 * against geospatial-engineer's actual precompute output at Sync Point 1.
 *
 * Raster `tile_url`s below point at public OpenStreetMap tiles as a DEV-ONLY
 * placeholder texture, purely so ThematicLayerControl/SwipeControl have
 * something real to render while wired up against mocks — this is NOT real
 * NDVI/LULC/water data and must never be mistaken for it. Every fixture's
 * `legend` labels this plainly, and none of this ships past mock mode
 * (VITE_API_MODE=mock only).
 */
import type { ThematicLayer, ThematicLayerResponse } from '@/types/domain'

const MWS_BOUNDS: [number, number, number, number] = [92.05, 26.02, 92.55, 26.38]

const PLACEHOLDER_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

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
    tile_url: PLACEHOLDER_TILE_URL,
  },
  ndvi_before: {
    layer: 'ndvi_before',
    kind: 'raster',
    bounds: MWS_BOUNDS,
    legend: ndviLegend,
    tile_url: PLACEHOLDER_TILE_URL,
  },
  ndvi_after: {
    layer: 'ndvi_after',
    kind: 'raster',
    bounds: MWS_BOUNDS,
    legend: ndviLegend,
    tile_url: PLACEHOLDER_TILE_URL,
  },
  ndvi_change: {
    layer: 'ndvi_change',
    kind: 'raster',
    bounds: MWS_BOUNDS,
    legend: ndviChangeLegend,
    tile_url: PLACEHOLDER_TILE_URL,
  },
  water: {
    layer: 'water',
    kind: 'raster',
    bounds: MWS_BOUNDS,
    legend: waterLegend,
    tile_url: PLACEHOLDER_TILE_URL,
  },
}
