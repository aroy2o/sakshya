/**
 * Plain TS types for the app's domain model. Every one of these is
 * `z.infer<...>` off `src/schemas/domain.ts` — that file is the source of
 * truth (it's what actually validates fetch responses); this file exists so
 * components/hooks can `import type { AssetDetail } from '@/types/domain'`
 * without pulling zod into every file.
 */
import type { z } from 'zod'
import type {
  zAiResult,
  zAssetDetail,
  zAssetPinFeature,
  zAssetPinFeatureCollection,
  zAssetPinProperties,
  zBand,
  zCategoryCode,
  zDistrictCoverage,
  zGeoFlag,
  zGeoFlagRule,
  zLegendEntry,
  zMws,
  zMwsBoundary,
  zMwsListItem,
  zMwsStats,
  zPhotoSource,
  zSatIndex,
  zSatInterpretation,
  zSatResult,
  zThematicLayer,
  zThematicLayerResponse,
  zZoneIndices,
} from '@/schemas/domain'

export type CategoryCode = z.infer<typeof zCategoryCode>
export type Band = z.infer<typeof zBand>
export type PhotoSource = z.infer<typeof zPhotoSource>
export type GeoFlagRule = z.infer<typeof zGeoFlagRule>
export type GeoFlag = z.infer<typeof zGeoFlag>
export type AiResult = z.infer<typeof zAiResult>
export type SatIndex = z.infer<typeof zSatIndex>
export type ZoneIndices = z.infer<typeof zZoneIndices>
export type SatInterpretation = z.infer<typeof zSatInterpretation>
export type SatResult = z.infer<typeof zSatResult>
export type AssetPinProperties = z.infer<typeof zAssetPinProperties>
export type AssetPinFeature = z.infer<typeof zAssetPinFeature>
export type AssetPinFeatureCollection = z.infer<typeof zAssetPinFeatureCollection>
export type AssetDetail = z.infer<typeof zAssetDetail>
export type MwsBoundary = z.infer<typeof zMwsBoundary>
export type Mws = z.infer<typeof zMws>
export type MwsListItem = z.infer<typeof zMwsListItem>
export type MwsStats = z.infer<typeof zMwsStats>
export type ThematicLayer = z.infer<typeof zThematicLayer>
export type ThematicLayerResponse = z.infer<typeof zThematicLayerResponse>
export type LegendEntry = z.infer<typeof zLegendEntry>
export type DistrictCoverage = z.infer<typeof zDistrictCoverage>

export { CATEGORY_CODES, NO_SATELLITE_SIGNAL_CATEGORIES, THEMATIC_LAYERS } from '@/schemas/domain'
