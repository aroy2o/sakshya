/**
 * Mock for `GET /mws/{id}/assets` — derived from the same assetDetailsById
 * fixtures so the map pins and the drawer never disagree in mock mode.
 * Only carries the minimal per-pin properties PRD §9 documents
 * (evidence_score/band nullable until scored) — not the full breakdown.
 */
import type { AssetPinFeatureCollection } from '@/types/domain'
import { assetDetailsById } from './assetDetails'

export const assetsFeatureCollection: AssetPinFeatureCollection = {
  type: 'FeatureCollection',
  features: Object.values(assetDetailsById).map((asset) => ({
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [asset.lon, asset.lat],
    },
    properties: {
      id: asset.id,
      work_code: asset.work_code,
      category: asset.category,
      activity: asset.activity,
      status: asset.status,
      evidence_score: asset.evidence_score,
      band: asset.band,
      is_synthetic: asset.is_synthetic,
    },
  })),
}
