import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import { AssetPinsLayer } from './AssetPinsLayer'
import { basemapStyle } from './basemapStyle'
import { MapLegend } from './MapLegend'
import { MwsBoundaryLayer } from './MwsBoundaryLayer'
import { MwsStatsBar } from './MwsStatsBar'
import { SwipeControl } from './SwipeControl'
import { ThematicLayerControl } from './ThematicLayerControl'
import { ThematicLayers } from './ThematicLayers'
import { AssetDrawer } from '@/components/drawer/AssetDrawer'
import { ErrorState } from '@/components/layout/ErrorState'
import { LoadingState } from '@/components/layout/LoadingState'
import { useMws } from '@/hooks/useMws'
import { useMwsAssets } from '@/hooks/useMwsAssets'
import { useMapUi } from '@/state/mapUiStore'
import { multiPolygonBounds } from '@/utils/geo'

/**
 * FR5.1/FR5.2 root: owns the single MapLibre instance and mounts the
 * boundary/pin/thematic-layer children once it's loaded. Also mounts
 * `AssetDrawer` (FR5.3) and `SwipeControl` (FR5.4), both driven by
 * `MapUiContext` so clicking a pin or toggling swipe doesn't need prop
 * drilling through this component.
 */
export function WatershedMap({ mwsId }: { mwsId: string }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [map, setMap] = useState<maplibregl.Map | null>(null)

  const mwsQuery = useMws(mwsId)
  const assetsQuery = useMwsAssets(mwsId)
  const { selectedAssetId, selectAsset, independentLayers, ndviVariant, swipeActive } = useMapUi()

  useEffect(() => {
    if (!containerRef.current) return
    const instance = new maplibregl.Map({
      container: containerRef.current,
      style: basemapStyle,
      center: [92.3, 26.2],
      zoom: 9,
    })
    instance.addControl(new maplibregl.NavigationControl(), 'top-right')
    instance.once('load', () => setMap(instance))

    return () => {
      instance.remove()
      setMap(null)
    }
  }, [])

  useEffect(() => {
    if (map && mwsQuery.data) {
      map.fitBounds(multiPolygonBounds(mwsQuery.data.boundary.coordinates), { padding: 40, duration: 0 })
    }
  }, [map, mwsQuery.data])

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="maplibre-map-container" />

      {map && mwsQuery.data && <MwsBoundaryLayer map={map} mws={mwsQuery.data} />}
      {map && assetsQuery.data && (
        <AssetPinsLayer map={map} featureCollection={assetsQuery.data} onSelect={selectAsset} />
      )}
      {map && (
        <ThematicLayers
          map={map}
          mwsId={mwsId}
          independentLayers={independentLayers}
          ndviVariant={ndviVariant}
          hidden={swipeActive}
        />
      )}
      {swipeActive && <SwipeControl mwsId={mwsId} />}

      {mwsQuery.data && assetsQuery.data && <MwsStatsBar mws={mwsQuery.data} assets={assetsQuery.data} />}
      <ThematicLayerControl />
      <MapLegend mwsId={mwsId} />

      {(mwsQuery.isLoading || assetsQuery.isLoading || !map) && (
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2">
          <LoadingState label="Loading watershed map…" />
        </div>
      )}
      {mwsQuery.isError && (
        <div className="absolute inset-x-0 top-4 mx-auto w-fit">
          <ErrorState message={(mwsQuery.error as Error).message} onRetry={() => mwsQuery.refetch()} />
        </div>
      )}
      {assetsQuery.isError && (
        <div className="absolute inset-x-0 top-4 mx-auto w-fit">
          <ErrorState message={(assetsQuery.error as Error).message} onRetry={() => assetsQuery.refetch()} />
        </div>
      )}

      {selectedAssetId !== null && (
        <AssetDrawer assetId={selectedAssetId} onClose={() => selectAsset(null)} />
      )}
    </div>
  )
}
