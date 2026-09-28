/**
 * The one interface both the live API client (`endpoints.ts`) and the mock
 * adapter (`mockAdapter.ts`) implement. Every hook in `src/hooks/` imports
 * `api` from `./index` and calls through this interface only — so swapping
 * `VITE_API_MODE=mock` for `live` at Sync Point 1 needs zero changes to any
 * component or hook, exactly as planned.
 */
import type {
  AssetDetail,
  AssetPinFeatureCollection,
  DistrictCoverage,
  Mws,
  MwsListItem,
  ThematicLayer,
  ThematicLayerResponse,
} from '@/types/domain'

export interface Api {
  getMwsList(): Promise<MwsListItem[]>
  getMws(id: string): Promise<Mws>
  getMwsAssets(id: string): Promise<AssetPinFeatureCollection>
  getAssetDetail(id: number): Promise<AssetDetail>
  getThematicLayer(mwsId: string, layer: ThematicLayer): Promise<ThematicLayerResponse>
  getDistrictCoverage(): Promise<DistrictCoverage[]>
}
