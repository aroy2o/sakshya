/**
 * Zod schemas mirroring PRD.md §8 (data model) and §9 (API contract).
 *
 * These are the single source of truth for the shapes this app works with —
 * `src/types/domain.ts` just re-exports `z.infer<...>` aliases from here so
 * the rest of the codebase imports plain TS types without touching zod.
 *
 * Every fetch in `src/api/endpoints.ts` parses its response through one of
 * these schemas. `zAiResult`/`zSatResult` are `.strict()` deliberately: at
 * Sync Point 1 (2026-09-28) this app's original guessed shapes for those two
 * nested JSONB blobs both turned out to have extra real fields that zod's
 * default "strip unknown keys" behaviour was silently discarding instead of
 * erroring on — `needs_review` in particular went unrendered for a while.
 * `.strict()` on those two means the next drift fails loudly instead of
 * quietly dropping a field a reviewer needed to see. The top-level
 * field_record/asset_evidence columns stay non-strict — that shape is
 * governed by PRD §8's own "update the doc first" rule, a process guarantee
 * `.strict()` would just fight with if backend adds a column ahead of a doc
 * edit.
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
// PRD §12.1 — geo-integrity flags. Rule slugs + shape ({rule, passed,
// points, max, detail}) confirmed verbatim against a live
// `GET /assets/18` response on 2026-09-28 (Sync Point 1).
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
// PRD §12.2 — AI Image Interpreter output. Confirmed verbatim against a live
// `GET /assets/18` response on 2026-09-28 (Sync Point 1) — the original
// PLAYBOOK §8.3-derived guess was missing `needs_review`, `flags`,
// `provider`, `model`, `classified_at`. `.strict()` so the next drift errors
// instead of silently stripping a field like `needs_review` did here.
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

export const zAiResult = z
  .object({
    predicted_category: z.union([zCategoryCode, z.literal('UNKNOWN')]),
    predicted_activity: z.string(),
    construction_stage: zConstructionStage,
    water_visible: zYesNoUnclear,
    vegetation_cover: zVegetationCover,
    matches_declared: zMatchesDeclared,
    confidence: z.number().min(0).max(1),
    evidence: z.string(),
    /** FR2.2's confidence-gate flag — "needs a second look regardless of the score." Always surface this, never just parse-and-discard it. */
    needs_review: z.boolean(),
    flags: z.array(z.string()),
    provider: z.string(),
    model: z.string().nullable(),
    classified_at: z.string(),
  })
  .strict()

// ---------------------------------------------------------------------------
// PRD §12.3 — satellite response (DiD). Fully rewritten 2026-09-28 (Sync
// Point 1) against a live `GET /assets/18` response — the original guess
// (zone_radius_m, flat treated_before:{NDVI,MNDWI}, a time_series array,
// before/after image URLs) matched none of the real shape.
// geospatial-engineer's precompute produces exactly one baseline/latest
// pair per zone, NOT a continuous time series, and no per-asset imagery —
// `SatelliteIndexChart` renders a 2-window comparison accordingly, and
// `SatelliteChips` no longer shows a per-asset before/after image swipe.
// `.strict()` for the same reason as zAiResult above.
// ---------------------------------------------------------------------------
export const zSatIndex = z.enum(['NDVI', 'MNDWI', 'NDMI', 'water_fraction'])

export const zZoneIndices = z
  .object({
    NDVI: z.number(),
    MNDWI: z.number(),
    NDMI: z.number(),
    water_fraction: z.number(),
  })
  .strict()

export const zSatDiD = z
  .object({
    NDVI: z.number(),
    MNDWI: z.number(),
    NDMI: z.number(),
    water_fraction: z.number(),
  })
  .strict()

/** Matches PRD §12.3's DiD bands (renamed from this app's earlier `interpretation` guess — the real field is `did_classification`). */
export const zSatInterpretation = z.enum([
  'strongly_positive',
  'weakly_positive',
  'inconclusive',
  'negative',
  'neutral_no_signal',
])

export const zSatResult = z
  .object({
    record_id: z.number().int(),
    mws_id: z.string(),
    category: zCategoryCode,
    primary_index_for_category: zSatIndex,
    indices: z
      .object({
        treated_before: zZoneIndices,
        treated_after: zZoneIndices,
        control_before: zZoneIndices,
        control_after: zZoneIndices,
      })
      .strict(),
    did: zSatDiD,
    did_classification: zSatInterpretation,
    satellite_score: z.number().int().min(0).max(30),
    rainfall: z
      .object({
        baseline_mm: z.number().nullable(),
        latest_mm: z.number().nullable(),
        pct_change: z.number().nullable(),
      })
      .strict(),
    baseline_window: z.tuple([z.string(), z.string()]),
    latest_window: z.tuple([z.string(), z.string()]),
    treated_buffer_m: z.number(),
    control_ring_m: z.tuple([z.number(), z.number()]),
    data_source: z
      .object({
        optical: z.string().nullable(),
        sar_fallback_used: z.boolean(),
      })
      .strict(),
    valid_pixel_fraction: z
      .object({
        treated: z.number().nullable(),
        control: z.number().nullable(),
      })
      .strict(),
    low_confidence: z.boolean(),
    /** True while geospatial-engineer's precompute has no real GEE credentials — see `source` for why. Render this prominently; never let placeholder zeros read as a real satellite verdict. */
    placeholder: z.boolean(),
    source: z.string(),
    /** Server-authored caveat strings (e.g. PRD §12.3's "too early post-work" note for a negative DiD) — render verbatim, don't re-derive client-side. */
    notes: z.array(z.string()),
    computed_at: z.string(),
  })
  .strict()

// ---------------------------------------------------------------------------
// PRD §8 — field_record (minus lat/lon+geom's geometry, which the
// FeatureCollection/asset-detail responses carry directly).
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
  photo1_phash: z.string().nullable().optional(),
  photo2_phash: z.string().nullable().optional(),
  remarks: z.string().nullable(),
  observer_id: z.string().nullable(),
  observer_name: z.string().nullable(),
  organisation: z.string().nullable(),
  is_synthetic: z.boolean(),
  photo_source: zPhotoSource.nullable(),
  created_at: z.string().nullable().optional(),
})

/**
 * Minimal per-pin properties — what `GET /mws/{id}/assets` (a GeoJSON
 * FeatureCollection) puts on each Feature. Deliberately lighter than the
 * full asset detail: PRD §9 says the assets endpoint carries
 * `evidence_score`/`band` (null until scored) for pin rendering; the full
 * evidence breakdown is a separate `GET /assets/{id}` fetch on click. The
 * live response also includes `captured_at`/`photo1_url` on each feature;
 * harmless extras this schema doesn't need for pin rendering, left
 * unmodelled (non-strict, so they're simply ignored here).
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
// fresh out of `POST /records` only has geo_score/geo_flags filled; as of
// the 2026-09-28 sync, temporal_score/evidence_score/band are still null
// project-wide (Phase 4, not built yet) even though geo/visual/satellite
// are populated for all 17 seeded records.
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
// PRD §8 — mws. Field renamed 2026-09-28 (Sync Point 1): the live
// `GET /mws/{id}` response calls the boundary geometry `boundary`, not
// `geom` as this app originally guessed, and doesn't serve `stats` at all
// yet (Phase 4 territory even though §9 lists it under Phase 1/5) — `stats`
// is optional here and `useMwsStats.ts` computes an equivalent client-side
// from `GET /mws/{id}/assets` when the server doesn't provide it, so the
// UI never just goes blank waiting on a field that may not land before demo.
// ---------------------------------------------------------------------------
export const zMwsStats = z.object({
  total_assets: z.number().int().min(0),
  verified: z.number().int().min(0),
  review: z.number().int().min(0),
  flag: z.number().int().min(0),
  unscored: z.number().int().min(0),
})

export const zMwsBoundary = z.object({
  type: z.literal('MultiPolygon'),
  coordinates: z.array(z.array(z.array(z.tuple([z.number(), z.number()])))),
})

export const zMws = z.object({
  id: z.string(),
  name: z.string().nullable(),
  project_id: z.string().nullable(),
  state: z.string().nullable(),
  district: z.string().nullable(),
  baseline_start: z.string().nullable(),
  baseline_end: z.string().nullable(),
  latest_start: z.string().nullable(),
  latest_end: z.string().nullable(),
  is_synthetic_boundary: z.boolean(),
  created_at: z.string().nullable().optional(),
  boundary: zMwsBoundary,
  stats: zMwsStats.optional(),
  /**
   * Reality Pass R6 (2026-09-28): free-text provenance string, e.g. "REAL
   * boundary — union of 5 SLUSI micro-watershed polygon(s)...
   * (pick_method=automated_ranking_pending_human_confirmation)...". Drive
   * the "candidate watershed (project area unconfirmed)" caveat label off
   * the substring `pending_human_confirmation` in this string — see
   * utils/boundarySource.ts. Never hardcode the caveat as always-on; once a
   * human confirms the MWS codes and this substring disappears, the label
   * must disappear too, automatically.
   */
  boundary_source: z.string().nullable().optional(),
})

export const zMwsListItem = zMws.omit({ boundary: true, stats: true }).extend({
  stats: zMwsStats.optional(),
})

export const zMwsList = z.array(zMwsListItem)

// ---------------------------------------------------------------------------
// PRD §9 — GET /mws/{id}/thematic/{layer}. Envelope confirmed 2026-09-28
// (Sync Point 1) against live `ndvi_before` (raster) and `drainage`
// (vector) responses. One correction from this app's original guess: a
// raster layer's `tile_url` is a single bounds-anchored static PNG (one
// precomputed composite image), not an XYZ tile pyramid — rendered as a
// MapLibre `ImageSource`, not a `RasterSource` with a `{z}/{x}/{y}`
// template (see ThematicLayerRenderer.tsx / SwipeControl.tsx).
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
  /** True while this is geospatial-engineer's placeholder precompute output rather than a real GEE-derived composite — surface this, don't let it read as real satellite evidence. */
  placeholder: z.boolean(),
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
// GET /districts/geotag-coverage — now live and real (Reality Pass R3/R4,
// 2026-09-28): 51 districts across Assam/Meghalaya/Tripura, real WDC-PMKSY
// MIS GT2 numbers. `source_report`/`as_of` added here 2026-09-28 (were
// present live but unmodelled before — same "silently stripped" risk class
// as the earlier ai_result bug); beat 1/2's "as on" stamp reads `as_of`.
// ---------------------------------------------------------------------------
export const zDistrictCoverage = z.object({
  district: z.string(),
  state: z.string(),
  total_works: z.number().int().min(0),
  geotagged_works: z.number().int().min(0),
  geotag_coverage_pct: z.number().min(0).max(100),
  source_report: z.string().nullable().optional(),
  as_of: z.string().nullable().optional(),
})

export const zDistrictCoverageList = z.array(zDistrictCoverage)

// ---------------------------------------------------------------------------
// Reality Pass R6 (2026-09-28) — GET /mws/{id}/watershed-impact. Beat 4's
// data source: matched-control DiD effect + annual NDVI/MNDWI/rainfall
// time series. Shape confirmed live against a real response (summary +
// timeseries, both independently `placeholder`-flagged — REAL_DATA_PLAN.md
// §4.2's bootstrap-over-control-polygons DiD is real code, running on
// synthetic numbers only because GEE credentials aren't wired up yet).
// `.strict()` on the per-index effect block since it's the number the
// impact-curve headline reads directly.
// ---------------------------------------------------------------------------
const zImpactEffect = z
  .object({
    effect: z.number(),
    ci_low: z.number(),
    ci_high: z.number(),
    n_bootstrap: z.number().int(),
    ci: z.number(),
    n_control_polygons: z.number().int(),
    pre_mean_gap: z.number(),
    post_mean_gap: z.number(),
    pre_years: z.array(z.number().int()),
    post_years: z.array(z.number().int()),
  })
  .strict()

export const zWatershedImpactSummary = z.object({
  mws_id: z.string(),
  generated_at: z.string(),
  placeholder: z.boolean(),
  source: z.string(),
  method_params: z.object({
    project_start_year: z.number().int(),
    n_bootstrap: z.number().int(),
    ci: z.number(),
    bootstrap_unit: z.string(),
    n_control_polygons: z.number().int(),
  }),
  NDVI: zImpactEffect,
  MNDWI: zImpactEffect,
  caveats: z.array(z.string()),
})

const zYearlyValues = z.record(z.string(), z.number())

const zControlPolygon = z.object({
  mws_code: z.string(),
  district: z.string(),
  NDVI: zYearlyValues,
  MNDWI: zYearlyValues,
})

export const zWatershedImpactTimeseries = z.object({
  mws_id: z.string(),
  generated_at: z.string(),
  placeholder: z.boolean(),
  source: z.string(),
  method: z.object({
    season_window: z.string(),
    years: z.array(z.number().int()),
    project_start_year: z.number().int(),
    rainfall_window: z.string(),
    n_control_polygons: z.number().int(),
    control_selection: z.string(),
  }),
  treated: z.object({
    polygon_source: z.string(),
    NDVI: zYearlyValues,
    MNDWI: zYearlyValues,
  }),
  control_mean: z.object({
    NDVI: zYearlyValues,
    MNDWI: zYearlyValues,
  }),
  // Individual control polygons exist for methodology transparency (§4.1's
  // matched-control set) but beat 4's chart only plots treated vs
  // control_mean — this app doesn't render all ~53 individually.
  control_polygons: z.record(z.string(), zControlPolygon),
  rainfall_mm_jun_sep: zYearlyValues,
})

export const zWatershedImpact = z.object({
  mws_id: z.string(),
  summary: zWatershedImpactSummary,
  timeseries: zWatershedImpactTimeseries,
})

// ---------------------------------------------------------------------------
// Reality Pass R6 (2026-09-28) — GET /classifier/benchmark. Measured
// accuracy on real (not AI-generated) photos, per model. `accuracy_status`
// ('measured' | 'not_established') is computed server-side from real
// signal (schema-validation failure rate, sample completeness) — displayed
// verbatim in AiClassifierCard's model-reliability note, never
// re-judged/re-labelled client-side.
// ---------------------------------------------------------------------------
export const zAccuracyStatus = z.enum(['measured', 'not_established'])

export const zClassifierBenchmarkModel = z.object({
  model: z.string(),
  provider: z.string(),
  n_photos: z.number().int(),
  n_correct: z.number().int(),
  n_errors: z.number().int(),
  accuracy: z.number(),
  axis_labels: z.array(z.string()),
  confusion_matrix: z.record(z.string(), z.record(z.string(), z.number())),
  generated_at: z.string(),
  note: z.string(),
  n_schema_invalid_responses: z.number().int(),
  is_full_dataset: z.boolean(),
  max_per_category: z.number().int().nullable(),
  neutral_declared_category: z.string(),
  neutral_declared_activity: z.string(),
  accuracy_status: zAccuracyStatus,
})

export const zClassifierBenchmark = z.object({
  dataset: z.object({
    n_photos: z.number().int(),
    source: z.string(),
    categories_covered: z.array(z.string()),
    categories_not_covered: z.array(z.string()),
    includes_none_distractors: z.boolean(),
    is_synthetic: z.boolean(),
    methodology_doc: z.string(),
    manifest_fields: z.array(z.string()),
  }),
  models: z.array(zClassifierBenchmarkModel),
  note: z.string(),
})

// ---------------------------------------------------------------------------
// Reality Pass R6 (2026-09-28) — GET /programme/marigaon. Real WDC-PMKSY
// registry aggregates for beat 6's moderation queue: exact Pre/Mid/Post
// backlog counts (not estimated), `moderation_backlog_note`'s
// not_submitted-vs-yet_to_moderate distinction (found empirically), and
// `moderation_backlog_denominator` (240) the percentages are of.
// ---------------------------------------------------------------------------
const zModerationStage = z.object({
  accepted: z.number().int(),
  yet_to_moderate: z.number().int(),
  rejected: z.number().int(),
  not_submitted: z.number().int(),
  mixed: z.number().int(),
  other: z.number().int(),
  yet_to_moderate_pct_of_geotagged: z.number(),
})

const zProgrammeProject = z.object({
  project_id: z.number().int(),
  project_name: z.string(),
  nrm_total: z.number().int(),
  epa_total: z.number().int(),
  livelihood_total: z.number().int(),
  production_total: z.number().int(),
  total_work_codes: z.number().int(),
  geotagged_work_codes: z.number().int(),
  non_geotagged_work_codes: z.number().int(),
})

export const zProgrammeMarigaon = z.object({
  district: z.string(),
  district_source_spelling: z.string(),
  state: z.string(),
  district_total_projects: z.number().int(),
  district_total_work_codes: z.number().int(),
  district_geotagged_work_codes: z.number().int(),
  district_non_geotagged_work_codes: z.number().int(),
  projects: z.array(zProgrammeProject),
  focus_project: zProgrammeProject.extend({ note: z.string() }),
  category_breakdown: z.array(
    z.object({
      category: zCategoryCode,
      work_code_count: z.number().int(),
      share_pct_of_geotagged: z.number(),
    }),
  ),
  unmapped_activities: z.array(z.string()),
  moderation_backlog: z.object({
    pre: zModerationStage,
    mid: zModerationStage,
    post: zModerationStage,
  }),
  moderation_backlog_denominator: z.number().int(),
  moderation_backlog_note: z.string(),
  activity_category_mapping_source: z.string(),
  source_report: z.string(),
  source_urls: z.record(z.string(), z.string()),
  retrieved_at: z.record(z.string(), z.string()),
  is_synthetic: z.boolean(),
})

// ---------------------------------------------------------------------------
// Reality Pass R6 (2026-09-28) — GET /provenance. Every real dataset used,
// for the "provenance panel" REAL_DATA_PLAN.md §7 calls "a credibility
// feature, not clutter."
// ---------------------------------------------------------------------------
export const zProvenanceEntry = z.object({
  name: z.string(),
  source_url: z.string().nullable(),
  licence: z.string(),
  retrieved_at: z.string().nullable(),
  is_synthetic: z.boolean(),
  photo_source: z.string().nullable(),
  used_for: z.string(),
  notes: z.string(),
  owner: z.string(),
})

export const zProvenanceList = z.array(zProvenanceEntry)
