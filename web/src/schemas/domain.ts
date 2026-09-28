/**
 * Zod schemas mirroring PRD.md §8 (data model) and §9 (API contract) exactly.
 *
 * These are the single source of truth for the shapes this app works with —
 * `src/types/domain.ts` just re-exports `z.infer<...>` aliases from here so
 * the rest of the codebase imports plain TS types without touching zod.
 *
 * Every fetch in `src/api/endpoints.ts` parses its response through one of
 * these schemas. That's deliberate: when `backend-engineer`'s real endpoints
 * replace the mock adapter at Sync Point 1, any shape drift from what's
 * documented here fails loudly (a thrown ZodError) instead of silently
 * rendering wrong/undefined data — see CLAUDE.md's "never fabricate a
 * number" rule.
 */
import { z } from 'zod'

// ---------------------------------------------------------------------------
// PRD §15.1 — fixed DRISHTI activity category codes. Do not add to this list
// without updating PRD.md §15.1 first (CLAUDE.md domain rule).
// ---------------------------------------------------------------------------
export const CATEGORY_CODES = [
  'AM',
  'VM',
  'SM',
  'PT',
  'NC',
  'BN',
  'LS',
  'LH',
  'OM',
] as const

export const zCategoryCode = z.enum(CATEGORY_CODES)

/** Categories for which PRD §12.3 says satellite evidence isn't meaningful. */
export const NO_SATELLITE_SIGNAL_CATEGORIES = ['LS', 'LH', 'OM'] as const

// ---------------------------------------------------------------------------
// Shared enums
// ---------------------------------------------------------------------------
export const zBand = z.enum(['verified', 'review', 'flag'])

export const zPhotoSource = z.enum(['field', 'ai_generated', 'stock_cc', 'unknown'])

export const zReviewerDecision = z.enum(['confirmed', 'rejected']).nullable()

// ---------------------------------------------------------------------------
// PRD §12.1 — geo-integrity flags. Rule slugs confirmed against
// backend-engineer's `services/geo_integrity.py` at the FR1.4 sync
// (2026-09-28): `exif_consistency` and `duplicate_photo`, not the
// `exif_consistent` / `not_duplicate` names this app used before that check.
// ---------------------------------------------------------------------------
export const zGeoFlagRule = z.enum([
  'gps_accuracy',
  'inside_boundary',
  'exif_consistency',
  'duplicate_photo',
  'timestamp_sane',
])

export const zGeoFlag = z.object({
  rule: zGeoFlagRule,
  passed: z.boolean(),
  points: z.number().int().min(0),
  max: z.number().int().min(0),
  detail: z.string(),
})

// ---------------------------------------------------------------------------
// PRD §12.2 / PLAYBOOK §8.3 — AI Image Interpreter output. Shape taken
// verbatim from the vision prompt's JSON schema in PLAYBOOK.md §8.3, since
// PRD §9 doesn't restate it. Flagged as an open assumption for
// vision-ai-engineer to confirm at Sync Point 1.
// ---------------------------------------------------------------------------
export const zConstructionStage = z.enum([
  'not_started',
  'under_construction',
  'completed',
  'damaged',
  'unclear',
])

export const zYesNoUnclear = z.enum(['yes', 'no', 'unclear'])
export const zVegetationCover = z.enum(['low', 'medium', 'high', 'unclear'])
export const zMatchesDeclared = z.enum(['yes', 'no', 'uncertain'])

export const zAiResult = z.object({
  predicted_category: z.union([zCategoryCode, z.literal('UNKNOWN')]),
  predicted_activity: z.string(),
  construction_stage: zConstructionStage,
  water_visible: zYesNoUnclear,
  vegetation_cover: zVegetationCover,
  matches_declared: zMatchesDeclared,
  confidence: z.number().min(0).max(1),
  evidence: z.string(),
})

// ---------------------------------------------------------------------------
// PRD §12.3 / PLAYBOOK §8.2 — satellite response (DiD). Shape extends
// PLAYBOOK §8.2's `zone_stats`/`did` output with a `time_series` array (for
// the treated-vs-control chart) and two image URLs (for the swipe/chips).
// Flagged as an open assumption — geospatial-engineer's precompute script
// needs to confirm it emits more than 2 dates for the chart to be meaningful.
// ---------------------------------------------------------------------------
export const zZoneStats = z.object({
  NDVI: z.number(),
  MNDWI: z.number(),
})

export const zSatInterpretation = z.enum([
  'strongly_positive',
  'weakly_positive',
  'inconclusive',
  'negative',
  'neutral_no_signal',
])

export const zSatTimePoint = z.object({
  date: z.string(),
  ndvi_treated: z.number(),
  ndvi_control: z.number(),
  mndwi_treated: z.number(),
  mndwi_control: z.number(),
  rainfall_mm: z.number().min(0),
})

export const zSatResult = z.object({
  zone_radius_m: z.object({
    treated: z.number(),
    control_inner: z.number(),
    control_outer: z.number(),
  }),
  treated_before: zZoneStats,
  treated_after: zZoneStats,
  control_before: zZoneStats,
  control_after: zZoneStats,
  did: z.object({ NDVI: z.number(), MNDWI: z.number() }),
  rainfall_baseline_mm: z.number().min(0),
  rainfall_latest_mm: z.number().min(0),
  expected_direction: z.string(),
  interpretation: zSatInterpretation,
  time_series: z.array(zSatTimePoint),
  before_image_url: z.string(),
  after_image_url: z.string(),
})

// ---------------------------------------------------------------------------
// PRD §8 — field_record (minus geom, which the FeatureCollection carries as
// GeoJSON geometry rather than a duplicated lat/lon+geom pair)
// ---------------------------------------------------------------------------
export const zFieldRecordStatus = z.enum(['planned', 'ongoing', 'completed', 'damaged']).nullable()

const zFieldRecordCore = z.object({
  id: z.number().int(),
  work_code: z.string().nullable(),
  mws_id: z.string(),
  category: zCategoryCode,
  activity: z.string(),
  status: zFieldRecordStatus,
  lat: z.number(),
  lon: z.number(),
  gps_accuracy_m: z.number().nullable(),
  orientation: z.number().nullable(),
  captured_at: z.string().nullable(), // ISO datetime
  photo1_url: z.string().nullable(),
  photo2_url: z.string().nullable(),
  remarks: z.string().nullable(),
  observer_id: z.string().nullable(),
  observer_name: z.string().nullable(),
  organisation: z.string().nullable(),
  is_synthetic: z.boolean(),
  photo_source: zPhotoSource.nullable(),
})

/**
 * Minimal per-pin properties — what `GET /mws/{id}/assets` (a GeoJSON
 * FeatureCollection) puts on each Feature. Deliberately lighter than the
 * full asset detail: PRD §9 says the assets endpoint carries
 * `evidence_score`/`band` (null until scored) for pin rendering; the full
 * evidence breakdown is a separate `GET /assets/{id}` fetch on click.
 */
export const zAssetPinProperties = z.object({
  id: z.number().int(),
  work_code: z.string().nullable(),
  category: zCategoryCode,
  activity: z.string(),
  status: zFieldRecordStatus,
  evidence_score: z.number().int().min(0).max(100).nullable(),
  band: zBand.nullable(),
  is_synthetic: z.boolean(),
})

export const zAssetPinFeature = z.object({
  type: z.literal('Feature'),
  geometry: z.object({
    type: z.literal('Point'),
    coordinates: z.tuple([z.number(), z.number()]),
  }),
  properties: zAssetPinProperties,
})

export const zAssetPinFeatureCollection = z.object({
  type: z.literal('FeatureCollection'),
  features: z.array(zAssetPinFeature),
})

// ---------------------------------------------------------------------------
// PRD §8 — asset_evidence, joined onto field_record for `GET /assets/{id}`.
// All *_score fields and the JSONB result blobs are nullable — a record
// fresh out of `POST /records` only has geo_score/geo_flags filled.
// ---------------------------------------------------------------------------
export const zAssetDetail = zFieldRecordCore.extend({
  geo_flags: z.array(zGeoFlag).nullable(),
  geo_score: z.number().int().min(0).max(30).nullable(),
  ai_result: zAiResult.nullable(),
  visual_score: z.number().int().min(0).max(30).nullable(),
  sat_result: zSatResult.nullable(),
  satellite_score: z.number().int().min(0).max(30).nullable(),
  temporal_score: z.number().int().min(0).max(10).nullable(),
  evidence_score: z.number().int().min(0).max(100).nullable(),
  band: zBand.nullable(),
  reviewer_decision: zReviewerDecision,
  reviewed_at: z.string().nullable(),
  scored_at: z.string().nullable(),
})

// ---------------------------------------------------------------------------
// PRD §8 — mws (+ the summary stats §9 says `GET /mws/{id}` carries).
// `outcome_index` is Phase 4 scope and intentionally absent — see
// src/schemas/domain.ts module doc; never stub a Phase-4 number early.
// ---------------------------------------------------------------------------
export const zMwsStats = z.object({
  total_assets: z.number().int().min(0),
  verified: z.number().int().min(0),
  review: z.number().int().min(0),
  flag: z.number().int().min(0),
  unscored: z.number().int().min(0),
})

export const zMws = z.object({
  id: z.string(),
  name: z.string().nullable(),
  project_id: z.string().nullable(),
  state: z.string().nullable(),
  district: z.string().nullable(),
  geom: z.object({
    type: z.literal('MultiPolygon'),
    coordinates: z.array(z.array(z.array(z.tuple([z.number(), z.number()])))),
  }),
  baseline_start: z.string().nullable(),
  baseline_end: z.string().nullable(),
  latest_start: z.string().nullable(),
  latest_end: z.string().nullable(),
  is_synthetic_boundary: z.boolean(),
  stats: zMwsStats,
})

export const zMwsListItem = zMws.omit({ geom: true, stats: true }).extend({
  stats: zMwsStats.optional(),
})

export const zMwsList = z.array(zMwsListItem)

// ---------------------------------------------------------------------------
// PRD §9 — GET /mws/{id}/thematic/{layer}. §9 only says "Tile URL or
// GeoJSON" without an envelope shape; this discriminated union is this
// app's own design, flagged as an open assumption for backend/geospatial to
// confirm at Sync Point 1.
// ---------------------------------------------------------------------------
export const THEMATIC_LAYERS = [
  'drainage',
  'lulc',
  'ndvi_before',
  'ndvi_after',
  'ndvi_change',
  'water',
] as const

export const zThematicLayer = z.enum(THEMATIC_LAYERS)

export const zLegendEntry = z.object({
  color: z.string(),
  label: z.string(),
})

const zThematicLayerBase = z.object({
  layer: zThematicLayer,
  bounds: z.tuple([z.number(), z.number(), z.number(), z.number()]),
  legend: z.array(zLegendEntry),
})

export const zThematicLayerResponse = z.discriminatedUnion('kind', [
  zThematicLayerBase.extend({
    kind: z.literal('raster'),
    tile_url: z.string(),
  }),
  zThematicLayerBase.extend({
    kind: z.literal('vector'),
    geojson: z.custom<GeoJSON.FeatureCollection>((v) => typeof v === 'object' && v !== null),
  }),
])

// ---------------------------------------------------------------------------
// PRD §9 — GET /districts/geotag-coverage (static real MIS numbers)
// ---------------------------------------------------------------------------
export const zDistrictCoverage = z.object({
  district: z.string(),
  state: z.string(),
  total_works: z.number().int().min(0),
  geotagged_works: z.number().int().min(0),
  geotag_coverage_pct: z.number().min(0).max(100),
})

export const zDistrictCoverageList = z.array(zDistrictCoverage)
