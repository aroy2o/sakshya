/**
 * Mock for `GET /mws/{id}` and `GET /mws`. Boundary is a coarse placeholder
 * polygon around the Marigaon (HYBAS_ID 4120883730) area per PROGRESS.md's
 * recorded default (PRD §14) — not the real MWS polygon, which
 * geospatial-engineer/backend-engineer will provide once Phase 1/3 seed
 * data is live. Marked `is_synthetic_boundary: true` accordingly.
 */
import type { Mws, MwsListItem } from '@/types/domain'

export const DEMO_MWS_ID = '4120883730'

export const mwsDetail: Mws = {
  id: DEMO_MWS_ID,
  name: 'Marigaon MWS (placeholder boundary)',
  project_id: 'WDC-PMKSY-AS-MRG-01',
  state: 'Assam',
  district: 'Marigaon',
  geom: {
    type: 'MultiPolygon',
    coordinates: [
      [
        [
          [92.05, 26.02],
          [92.55, 26.02],
          [92.55, 26.38],
          [92.05, 26.38],
          [92.05, 26.02],
        ],
      ],
    ],
  },
  baseline_start: '2019-10-01',
  baseline_end: '2020-01-31',
  latest_start: '2024-10-01',
  latest_end: '2025-01-31',
  is_synthetic_boundary: true,
  stats: {
    total_assets: 7,
    verified: 2,
    review: 2,
    flag: 2,
    unscored: 1,
  },
}

export const mwsList: MwsListItem[] = [
  {
    id: mwsDetail.id,
    name: mwsDetail.name,
    project_id: mwsDetail.project_id,
    state: mwsDetail.state,
    district: mwsDetail.district,
    baseline_start: mwsDetail.baseline_start,
    baseline_end: mwsDetail.baseline_end,
    latest_start: mwsDetail.latest_start,
    latest_end: mwsDetail.latest_end,
    is_synthetic_boundary: mwsDetail.is_synthetic_boundary,
    stats: mwsDetail.stats,
  },
]
