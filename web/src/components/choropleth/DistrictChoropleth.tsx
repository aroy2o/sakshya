import { useEffect, useMemo, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { FeatureCollection, Polygon, MultiPolygon } from 'geojson'
import { ChoroplethLegend, CHOROPLETH_RAMP } from './ChoroplethLegend'
import { DistrictTable } from './DistrictTable'
import { basemapStyle } from '@/components/map/basemapStyle'
import { ErrorState } from '@/components/layout/ErrorState'
import { LoadingState } from '@/components/layout/LoadingState'
import { ProvenanceChip } from '@/components/shared/ProvenanceChip'
import { useDistrictBoundaries } from '@/hooks/useDistrictBoundaries'
import { useDistrictCoverage } from '@/hooks/useDistrictCoverage'
import { joinDistrictCoverage, type DistrictBoundaryProperties } from '@/utils/districtJoin'

const SOURCE_ID = 'district-coverage'
const FILL_LAYER_ID = 'district-coverage-fill'
const LINE_LAYER_ID = 'district-coverage-line'

type CoverageFeatureProperties = DistrictBoundaryProperties & { coverage_pct: number | null }

/** FR5.5 — district-level choropleth from GET /districts/geotag-coverage. */
export function DistrictChoropleth() {
  const containerRef = useRef<HTMLDivElement>(null)
  const [map, setMap] = useState<maplibregl.Map | null>(null)

  const coverageQuery = useDistrictCoverage()
  const boundariesQuery = useDistrictBoundaries()

  const { joined, unmatched } = useMemo(() => {
    if (!coverageQuery.data || !boundariesQuery.data) return { joined: [], unmatched: [] }
    return joinDistrictCoverage(coverageQuery.data, boundariesQuery.data)
  }, [coverageQuery.data, boundariesQuery.data])

  const choroplethGeojson = useMemo<FeatureCollection<Polygon | MultiPolygon, CoverageFeatureProperties> | null>(() => {
    if (joined.length === 0) return null
    return {
      type: 'FeatureCollection',
      features: joined.map(({ feature, coverage }) => ({
        ...feature,
        properties: { ...feature.properties, coverage_pct: coverage.geotag_coverage_pct },
      })),
    }
  }, [joined])

  useEffect(() => {
    if (!containerRef.current) return
    const instance = new maplibregl.Map({
      container: containerRef.current,
      style: basemapStyle,
      center: [82, 22],
      zoom: 4,
    })
    instance.addControl(new maplibregl.NavigationControl(), 'top-right')
    instance.once('load', () => setMap(instance))
    return () => {
      instance.remove()
      setMap(null)
    }
  }, [])

  useEffect(() => {
    if (!map || !choroplethGeojson) return

    map.addSource(SOURCE_ID, { type: 'geojson', data: choroplethGeojson })
    map.addLayer({
      id: FILL_LAYER_ID,
      type: 'fill',
      source: SOURCE_ID,
      paint: {
        'fill-color': [
          'case',
          ['==', ['get', 'coverage_pct'], null],
          '#cbd5e1', // grey — no coverage data (see ChoroplethLegend)
          [
            'interpolate',
            ['linear'],
            ['get', 'coverage_pct'],
            ...CHOROPLETH_RAMP.flatMap(([stop, color]) => [stop, color]),
          ],
        ],
        'fill-opacity': 0.75,
      },
    })
    map.addLayer({
      id: LINE_LAYER_ID,
      type: 'line',
      source: SOURCE_ID,
      paint: { 'line-color': '#475569', 'line-width': 0.5 },
    })

    const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false })
    const handleMove = (e: maplibregl.MapLayerMouseEvent) => {
      const feature = e.features?.[0]
      if (!feature) return
      const props = feature.properties as CoverageFeatureProperties
      map.getCanvas().style.cursor = 'pointer'
      popup
        .setLngLat(e.lngLat)
        .setHTML(
          `<strong>${props.DISTRICT}</strong>, ${props.ST_NM}<br/>${
            props.coverage_pct === null ? 'No coverage data' : `${props.coverage_pct.toFixed(1)}% geotagged`
          }`,
        )
        .addTo(map)
    }
    const handleLeave = () => {
      map.getCanvas().style.cursor = ''
      popup.remove()
    }
    map.on('mousemove', FILL_LAYER_ID, handleMove)
    map.on('mouseleave', FILL_LAYER_ID, handleLeave)

    return () => {
      map.off('mousemove', FILL_LAYER_ID, handleMove)
      map.off('mouseleave', FILL_LAYER_ID, handleLeave)
      popup.remove()
      if (map.getLayer(LINE_LAYER_ID)) map.removeLayer(LINE_LAYER_ID)
      if (map.getLayer(FILL_LAYER_ID)) map.removeLayer(FILL_LAYER_ID)
      if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID)
    }
  }, [map, choroplethGeojson])

  const isLoading = coverageQuery.isLoading || boundariesQuery.isLoading
  const error = coverageQuery.error ?? boundariesQuery.error

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-wrap items-center gap-2 border-b border-(--border) bg-(--surface) px-4 py-2">
        <h2 className="text-sm font-semibold text-(--text)">Assam → Marigaon drill-down: geotag coverage</h2>
        <ProvenanceChip kind="real" detail="WDC-PMKSY MIS, live" />
        {coverageQuery.data?.[0]?.as_of && (
          <span className="text-xs text-(--text-faint)">as on {coverageQuery.data[0].as_of}</span>
        )}
      </div>
      <div className="relative flex-1">
        <div ref={containerRef} className="maplibre-map-container" />
        <ChoroplethLegend />
        {(isLoading || !map) && (
          <div className="absolute inset-x-0 top-1/2 -translate-y-1/2">
            <LoadingState label="Loading district coverage…" />
          </div>
        )}
        {error && (
          <div className="absolute inset-x-0 top-4 mx-auto w-fit">
            <ErrorState message={(error as Error).message} />
          </div>
        )}
      </div>
      {coverageQuery.data && (
        <div className="max-h-64 overflow-y-auto border-t border-(--border) px-4 py-2">
          <DistrictTable rows={coverageQuery.data} unmatchedDistricts={unmatched.map((d) => d.district)} />
        </div>
      )}
    </div>
  )
}
