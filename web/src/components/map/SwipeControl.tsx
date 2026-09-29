import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import { CompareSlider } from '@/components/shared/CompareSlider'
import { LoadingState } from '@/components/layout/LoadingState'
import { useThematicLayer } from '@/hooks/useThematicLayer'
import { useMapUi } from '@/state/mapUiStore'
import { basemapStyle } from './basemapStyle'
import { boundsArrayToLngLatBounds, boundsToImageCoordinates } from '@/utils/geo'

/**
 * FR5.4 — before/after satellite swipe control. Two MapLibre instances
 * (one showing `ndvi_before`, one `ndvi_after`) with their cameras kept in
 * sync on every pan/zoom, composited through `CompareSlider`'s clip-path
 * divider. This is the standard "compare" technique (as in
 * mapbox-gl-compare) hand-rolled with plain MapLibre + CSS rather than an
 * extra dependency, per the plan.
 */
export function SwipeControl({ mwsId }: { mwsId: string }) {
  const beforeContainerRef = useRef<HTMLDivElement>(null)
  const afterContainerRef = useRef<HTMLDivElement>(null)
  const beforeMapRef = useRef<maplibregl.Map | null>(null)
  const afterMapRef = useRef<maplibregl.Map | null>(null)

  const { data: beforeLayer, isLoading: beforeLoading, isError: beforeError } = useThematicLayer(mwsId, 'ndvi_before')
  const { data: afterLayer, isLoading: afterLoading, isError: afterError } = useThematicLayer(mwsId, 'ndvi_after')
  const { swipePosition, setSwipePosition } = useMapUi()

  // Create the two map instances once, and keep their cameras mirrored.
  useEffect(() => {
    if (!beforeContainerRef.current || !afterContainerRef.current) return

    const beforeMap = new maplibregl.Map({
      container: beforeContainerRef.current,
      style: basemapStyle,
      center: [92.3, 26.2],
      zoom: 9,
    })
    const afterMap = new maplibregl.Map({
      container: afterContainerRef.current,
      style: basemapStyle,
      center: [92.3, 26.2],
      zoom: 9,
    })
    beforeMapRef.current = beforeMap
    afterMapRef.current = afterMap

    let syncing = false
    const mirror = (source: maplibregl.Map, target: maplibregl.Map) => () => {
      if (syncing) return
      syncing = true
      target.jumpTo({
        center: source.getCenter(),
        zoom: source.getZoom(),
        bearing: source.getBearing(),
        pitch: source.getPitch(),
      })
      syncing = false
    }
    const onBeforeMove = mirror(beforeMap, afterMap)
    const onAfterMove = mirror(afterMap, beforeMap)
    beforeMap.on('move', onBeforeMove)
    afterMap.on('move', onAfterMove)

    return () => {
      beforeMap.off('move', onBeforeMove)
      afterMap.off('move', onAfterMove)
      beforeMap.remove()
      afterMap.remove()
      beforeMapRef.current = null
      afterMapRef.current = null
    }
  }, [])

  // Add the "before" raster layer once both the map and precomputed layer are ready.
  useEffect(() => {
    const map = beforeMapRef.current
    if (!map || !beforeLayer || beforeLayer.kind !== 'raster') return
    const add = () => {
      if (map.getSource('swipe-before')) return
      // Single bounds-anchored static image, not an XYZ tile pyramid — see ThematicLayerRenderer.tsx.
      map.addSource('swipe-before', {
        type: 'image',
        url: beforeLayer.tile_url,
        coordinates: boundsToImageCoordinates(beforeLayer.bounds),
      })
      map.addLayer({ id: 'swipe-before-layer', type: 'raster', source: 'swipe-before' })
      map.fitBounds(boundsArrayToLngLatBounds(beforeLayer.bounds), { padding: 20, duration: 0 })
    }
    if (map.loaded()) add()
    else map.once('load', add)
  }, [beforeLayer])

  // Add the "after" raster layer likewise (no fitBounds here — the before
  // map's fitBounds already drives both cameras via the mirror above).
  useEffect(() => {
    const map = afterMapRef.current
    if (!map || !afterLayer || afterLayer.kind !== 'raster') return
    const add = () => {
      if (map.getSource('swipe-after')) return
      map.addSource('swipe-after', {
        type: 'image',
        url: afterLayer.tile_url,
        coordinates: boundsToImageCoordinates(afterLayer.bounds),
      })
      map.addLayer({ id: 'swipe-after-layer', type: 'raster', source: 'swipe-after' })
    }
    if (map.loaded()) add()
    else map.once('load', add)
  }, [afterLayer])

  return (
    <div className="absolute inset-0 z-20 bg-(--surface)">
      <CompareSlider
        position={swipePosition}
        onPositionChange={setSwipePosition}
        beforeLabel="Before (baseline season)"
        afterLabel="After (latest season)"
        className="h-full w-full"
        before={<div ref={beforeContainerRef} className="h-full w-full" />}
        after={<div ref={afterContainerRef} className="h-full w-full" />}
      />
      {(beforeLoading || afterLoading) && (
        <div className="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2">
          <LoadingState label="Loading before/after NDVI…" />
        </div>
      )}
      {(beforeError || afterError) && (
        <p className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded bg-(--flag)/10 px-2 py-1 text-xs text-red-300">
          Couldn&apos;t load one of the NDVI layers for comparison.
        </p>
      )}
    </div>
  )
}
