/**
 * Mock implementation of `Api`, backed by the fixtures in
 * `src/mocks/fixtures/`. Used when `VITE_API_MODE` is unset or `'mock'`
 * (the default — lets the whole app run with zero backend). Responses are
 * still parsed through the zod schemas so a mistake in a fixture fails the
 * same way a live contract-drift would, and a small artificial delay
 * exercises the same loading states the live path will hit.
 *
 * An unknown id throws `ApiError` rather than returning an empty/zeroed
 * object — CLAUDE.md's "never fabricate a number" applies to mocks too.
 */
import { ApiError } from './client'
import type { Api } from './types'
import {
  zAssetDetail,
  zAssetPinFeatureCollection,
  zDistrictCoverageList,
  zMws,
  zMwsList,
  zThematicLayerResponse,
} from '@/schemas/domain'
import { assetDetailsById } from '@/mocks/fixtures/assetDetails'
import { assetsFeatureCollection } from '@/mocks/fixtures/assetsFeatureCollection'
import { districtCoverage } from '@/mocks/fixtures/districtCoverage'
import { mwsDetail, mwsList } from '@/mocks/fixtures/mws'
import { thematicLayerFixtures } from '@/mocks/fixtures/thematicLayers'

const MOCK_LATENCY_MS = 250

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), MOCK_LATENCY_MS))
}

export const mockApi: Api = {
  async getMwsList() {
    return delay(zMwsList.parse(mwsList))
  },
  async getMws(id) {
    if (id !== mwsDetail.id) {
      throw new ApiError(404, `No mock MWS with id "${id}"`)
    }
    return delay(zMws.parse(mwsDetail))
  },
  async getMwsAssets(id) {
    if (id !== mwsDetail.id) {
      throw new ApiError(404, `No mock MWS with id "${id}"`)
    }
    return delay(zAssetPinFeatureCollection.parse(assetsFeatureCollection))
  },
  async getAssetDetail(id) {
    const asset = assetDetailsById[id]
    if (!asset) {
      throw new ApiError(404, `No mock asset with id ${id}`)
    }
    return delay(zAssetDetail.parse(asset))
  },
  async getThematicLayer(_mwsId, layer) {
    // Mock mode serves the same fixture regardless of mwsId — there's only
    // one demo watershed's worth of mock data.
    return delay(zThematicLayerResponse.parse(thematicLayerFixtures[layer]))
  },
  async getDistrictCoverage() {
    return delay(zDistrictCoverageList.parse(districtCoverage))
  },
}
