/**
 * Live implementation of `Api` — calls `backend-engineer`'s real FastAPI
 * endpoints per PRD §9 and parses every response through the matching zod
 * schema. A shape mismatch throws a ZodError instead of rendering
 * undefined/garbage — that's intentional, see src/schemas/domain.ts.
 */
import { apiGet } from './client'
import type { Api } from './types'
import {
  zAssetDetail,
  zAssetPinFeatureCollection,
  zClassifierBenchmark,
  zDistrictCoverageList,
  zMws,
  zMwsList,
  zProgrammeMarigaon,
  zProvenanceList,
  zThematicLayerResponse,
  zWatershedImpact,
} from '@/schemas/domain'

export const liveApi: Api = {
  async getMwsList() {
    return zMwsList.parse(await apiGet('/mws'))
  },
  async getMws(id) {
    return zMws.parse(await apiGet(`/mws/${id}`))
  },
  async getMwsAssets(id) {
    return zAssetPinFeatureCollection.parse(await apiGet(`/mws/${id}/assets`))
  },
  async getAssetDetail(id) {
    return zAssetDetail.parse(await apiGet(`/assets/${id}`))
  },
  async getThematicLayer(mwsId, layer) {
    return zThematicLayerResponse.parse(await apiGet(`/mws/${mwsId}/thematic/${layer}`))
  },
  async getDistrictCoverage() {
    return zDistrictCoverageList.parse(await apiGet('/districts/geotag-coverage'))
  },
  async getWatershedImpact(mwsId) {
    return zWatershedImpact.parse(await apiGet(`/mws/${mwsId}/watershed-impact`))
  },
  async getClassifierBenchmark() {
    return zClassifierBenchmark.parse(await apiGet('/classifier/benchmark'))
  },
  async getProgrammeMarigaon() {
    return zProgrammeMarigaon.parse(await apiGet('/programme/marigaon'))
  },
  async getProvenance() {
    return zProvenanceList.parse(await apiGet('/provenance'))
  },
}
