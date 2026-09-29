/**
 * Mock for `GET /mws/{id}` and `GET /mws`. Reality Pass R1 (2026-09-28)
 * replaced the placeholder boundary with a real SLUSI micro-watershed
 * union — `is_synthetic_boundary: false` and `boundary_source` below
 * mirror that real captured live response's metadata verbatim. The
 * polygon geometry itself stays a simplified rectangle stand-in (the real
 * one is a multi-thousand-vertex union of 5 SLUSI polygons, too large to
 * usefully hand-maintain here) — clearly a mock-only simplification, not
 * something presented as the real shape.
 *
 * `district: 'Morigaon'` (not "Marigaon") matches the live backend's
 * actual value — the MWS is named "Marigaon" but its `district` field uses
 * the official Census/MIS spelling "Morigaon". The bundled boundary
 * polygons (`public/data/india-districts.geojson`) use "Marigaon" (that
 * file's own Census-sourced spelling), so this one district won't join in
 * `DistrictChoropleth` — it shows correctly in `DistrictTable`'s unmatched
 * list instead, same as it does live.
 */
import type { Mws, MwsListItem } from '@/types/domain'

export const DEMO_MWS_ID = '4120883730'

export const mwsDetail: Mws = {
  id: DEMO_MWS_ID,
  name: 'Marigaon',
  project_id: 'SAKSHYA-DEMO',
  state: 'Assam',
  district: 'Morigaon',
  boundary: {
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
  baseline_start: '2023-01-01',
  baseline_end: '2023-03-31',
  latest_start: '2025-01-01',
  latest_end: '2025-03-31',
  is_synthetic_boundary: false,
  boundary_source:
    "REAL boundary — union of 5 SLUSI micro-watershed polygon(s) in Marigaon district (pick_method=automated_ranking_pending_human_confirmation), source: https://pub-0429b8e3b5a946e69ea007df844a6f1c.r2.dev/environment/slusi-micro-watersheds/SLUSI_MicroWatersheds.parquet (CC0-1.0). Pending human confirmation against the real MARIGAON-WDC-1/2021-22 project's actual MWS codes (REAL_DATA_PLAN.md §9 item 2). Applied 2026-09-28T10:52:55.837369+00:00 from cached ranking generated 2026-09-28T10:45:18.087259+00:00.",
  // Not served by the live API — kept here so mock mode still demonstrates
  // the "server provides stats" rendering path; live mode falls back to
  // utils/mwsStats.ts's client-side computation instead.
  stats: {
    total_assets: 17,
    verified: 0,
    review: 0,
    flag: 0,
    unscored: 17,
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
    boundary_source: mwsDetail.boundary_source,
    stats: mwsDetail.stats,
  },
]
