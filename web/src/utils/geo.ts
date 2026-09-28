/** Small geometry helpers — kept local instead of pulling in turf for one bbox computation. */
import type { LngLatBoundsLike } from 'maplibre-gl'

export function multiPolygonBounds(
  coordinates: readonly (readonly (readonly (readonly [number, number])[])[])[],
): LngLatBoundsLike {
  let minLng = Infinity
  let minLat = Infinity
  let maxLng = -Infinity
  let maxLat = -Infinity

  for (const polygon of coordinates) {
    for (const ring of polygon) {
      for (const [lng, lat] of ring) {
        if (lng < minLng) minLng = lng
        if (lng > maxLng) maxLng = lng
        if (lat < minLat) minLat = lat
        if (lat > maxLat) maxLat = lat
      }
    }
  }

  return [
    [minLng, minLat],
    [maxLng, maxLat],
  ]
}

export function boundsArrayToLngLatBounds(bounds: readonly [number, number, number, number]): LngLatBoundsLike {
  return [
    [bounds[0], bounds[1]],
    [bounds[2], bounds[3]],
  ]
}

/**
 * MapLibre's `ImageSource` needs its four corners in
 * top-left/top-right/bottom-right/bottom-left order, not a bbox. Used for
 * thematic raster layers — confirmed live at Sync Point 1 (2026-09-28) that
 * `tile_url` is one bounds-anchored static PNG per layer, not an XYZ tile
 * pyramid, so these render as `ImageSource`s rather than `RasterSource`s.
 */
export function boundsToImageCoordinates(
  bounds: readonly [number, number, number, number],
): [[number, number], [number, number], [number, number], [number, number]] {
  const [minLng, minLat, maxLng, maxLat] = bounds
  return [
    [minLng, maxLat], // top-left
    [maxLng, maxLat], // top-right
    [maxLng, minLat], // bottom-right
    [minLng, minLat], // bottom-left
  ]
}
