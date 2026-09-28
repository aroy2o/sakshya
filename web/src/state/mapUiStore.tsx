/**
 * UI-only state for the watershed map view (FR5.1-FR5.4): which pin is
 * selected, which thematic layers are toggled on, and swipe-control state.
 * Server data (assets, layers, mws) stays in React Query's cache — this
 * context only ever holds view state, never fetched data, so there's
 * nothing here that could go stale against the API.
 */
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import type { ThematicLayer } from '@/types/domain'

export type NdviVariant = Extract<ThematicLayer, 'ndvi_before' | 'ndvi_after' | 'ndvi_change'>

export interface IndependentLayerToggles {
  drainage: boolean
  lulc: boolean
  water: boolean
}

interface MapUiValue {
  selectedAssetId: number | null
  selectAsset: (id: number | null) => void

  independentLayers: IndependentLayerToggles
  toggleIndependentLayer: (layer: keyof IndependentLayerToggles) => void

  ndviVariant: NdviVariant | 'off'
  setNdviVariant: (variant: NdviVariant | 'off') => void

  swipeActive: boolean
  setSwipeActive: (active: boolean) => void
  swipePosition: number // 0-100, percent from left
  setSwipePosition: (pos: number) => void
}

const MapUiContext = createContext<MapUiValue | null>(null)

export function MapUiProvider({ children }: { children: ReactNode }) {
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null)
  const [independentLayers, setIndependentLayers] = useState<IndependentLayerToggles>({
    drainage: false,
    lulc: false,
    water: false,
  })
  const [ndviVariant, setNdviVariant] = useState<NdviVariant | 'off'>('off')
  const [swipeActive, setSwipeActive] = useState(false)
  const [swipePosition, setSwipePosition] = useState(50)

  const value = useMemo<MapUiValue>(
    () => ({
      selectedAssetId,
      selectAsset: setSelectedAssetId,
      independentLayers,
      toggleIndependentLayer: (layer) =>
        setIndependentLayers((prev) => ({ ...prev, [layer]: !prev[layer] })),
      ndviVariant,
      setNdviVariant,
      swipeActive,
      setSwipeActive,
      swipePosition,
      setSwipePosition,
    }),
    [selectedAssetId, independentLayers, ndviVariant, swipeActive, swipePosition],
  )

  return <MapUiContext.Provider value={value}>{children}</MapUiContext.Provider>
}

export function useMapUi(): MapUiValue {
  const ctx = useContext(MapUiContext)
  if (!ctx) {
    throw new Error('useMapUi must be used within a MapUiProvider')
  }
  return ctx
}
