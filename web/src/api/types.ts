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
  ClassifierBenchmark,
  DistrictCoverage,
  Mws,
  MwsListItem,
  ProgrammeMarigaon,
  ProvenanceEntry,
  ThematicLayer,
  ThematicLayerResponse,
  WatershedImpact,
} from '@/types/domain'

export interface Api {
  getMwsList(): Promise<MwsListItem[]>
  getMws(id: string): Promise<Mws>
  getMwsAssets(id: string): Promise<AssetPinFeatureCollection>
  getAssetDetail(id: number): Promise<AssetDetail>
  getThematicLayer(mwsId: string, layer: ThematicLayer): Promise<ThematicLayerResponse>
  getDistrictCoverage(): Promise<DistrictCoverage[]>
  /** Reality Pass R6 — beat 4's data source. */
  getWatershedImpact(mwsId: string): Promise<WatershedImpact>
  /** Reality Pass R6 — beat 5's classifier-reliability note. */
  getClassifierBenchmark(): Promise<ClassifierBenchmark>
  /** Reality Pass R6 — beat 6's real moderation backlog + registry. */
  getProgrammeMarigaon(): Promise<ProgrammeMarigaon>
  /** Reality Pass R6 — beat 7's provenance panel / Methods & limits drawer. */
  getProvenance(): Promise<ProvenanceEntry[]>
}
