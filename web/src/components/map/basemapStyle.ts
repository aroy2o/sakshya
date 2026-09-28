import type { StyleSpecification } from '@maplibre/maplibre-gl-style-spec'

/**
 * Free, no-API-key raster basemap (OpenStreetMap tiles). PRD §11's
 * precompute-first / free-data rule is about satellite processing, not the
 * basemap, but the same instinct applies — no paid tile provider needed for
 * a hackathon demo.
 */
export const basemapStyle: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [
    {
      id: 'osm',
      type: 'raster',
      source: 'osm',
    },
  ],
}
