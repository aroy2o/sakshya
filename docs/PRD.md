# SAKSHYA — Product Requirements Document
### SIH 2026 · Problem Statement 26015 · Ministry of Rural Development, Dept. of Land Resources (DoLR)

**Working name:** SAKSHYA (साक्ष्य = evidence). Rename freely — it's not load-bearing.
**Status:** Living document. Update phase checkboxes as we go. This file is the source of truth for scope, schema and scoring — `CLAUDE.md` points here instead of duplicating it.
**Companion doc:** `PLAYBOOK.md` (research, rationale, GEE code, demo script, PPT structure, Q&A prep) — read that for *why*, read this for *exactly what to build*.

---

## 1. One-liner

An analytics layer on top of SRISHTI–DRISHTI that fuses geo-tagged field photos with 30 m satellite evidence to verify whether watershed development works were actually built and whether they're actually working — surfaced as a per-asset **Evidence Score** and a per-watershed **Outcome Index** on an interactive map dashboard.

**Core sentence to never lose sight of:** *Photo answers "was it built?" Satellite answers "did it work?" We fuse both.*

---

## 2. Problem statement (condensed from PS 26015)

- DRISHTI (NRSC/Bhuvan mobile app) captures geo-tagged, time-stamped field photos of watershed assets nationally — ~7 lakh+ geotagged work codes as of the last public MIS pull. Today these are used only as proof-of-upload, not analysed.
- No framework fuses these photos with the 30 m satellite data DoLR already accesses via SRISHTI to assess actual outcomes.
- No standardized way to flag suspect, duplicate, or mislabeled evidence at scale — manual review of lakhs of photos is impossible.
- No thematic visualization (drainage, LULC, vegetation, water, change detection) tied to individual assets or micro-watersheds.
- Full PS text, expected solutions (a–g), and scope table: see `PLAYBOOK.md` §2.

---

## 3. Goals (hackathon scope)

| ID | Goal |
|---|---|
| G1 | Ingest DRISHTI-schema field records (photo + geo + activity metadata) |
| G2 | Validate geo-integrity of each record automatically (accuracy, boundary, duplicates, timestamp) |
| G3 | Classify each photo with AI and check it matches the declared activity |
| G4 | Measure satellite-observed landscape response (NDVI/MNDWI) around each asset vs. a control zone, normalized for rainfall |
| G5 | Combine into a defensible, explainable Evidence Score (asset) and Outcome Index (watershed) |
| G6 | Visualize on a map dashboard: thematic layers, before/after swipe, drill-down, review queue |
| G7 | Expose an integration-ready API so this plugs into a real SRISHTI deployment |

## 4. Non-goals (explicit — do not build these for the hackathon)

- Replacing SRISHTI/DRISHTI, or production-grade field capture (Drishti++ is a documented stretch idea only, see `PLAYBOOK.md` §4 M7 — not in any phase below unless we explicitly add one).
- User/role management beyond a single demo login.
- Training a custom CV model — use a vision LLM (strict JSON schema) or CLIP zero-shot.
- National-scale processing — one demo watershed, optionally 1–2 comparison watersheds.
- SMS/email alerting infrastructure.
- Real DRISHTI data access (we don't have it) — use our own field photos + clearly-flagged synthetic records (`is_synthetic = true`, always).

---

## 5. Users / stakeholders

- **DoLR / SLNA / WCDC administrators** — triage which assets (of lakhs) need a field visit.
- **SIH judges/evaluators** — need to see innovation + feasibility + correct science in a ~3 min demo.
- **Field functionaries** — out of scope for this build (Drishti++ is future work).
- **Citizens/researchers** — future view-only access, not built now.

---

## 6. Success metrics

**Hackathon demo:**
- One real (or best-effort real) watershed with ≥1 asset scoring Verified.
- ≥3 deliberately planted bad records (duplicate photo, out-of-boundary point, activity/photo mismatch) all correctly caught and explained.
- Every PS expected-solution point (a–g) mapped to a visible feature (table in `PLAYBOOK.md` §2).
- No number on screen that we can't trace to a real source or a labelled synthetic one.

**Notional real-world impact (PPT only, not built):** % reduction in manual verification effort via triage; faster flagging of stalled/non-geotagged works.

---

## 7. System architecture

```
INPUT: DRISHTI-format records (photo + geo + activity) · MWS boundary
       · Satellite (Landsat 30m, Sentinel-2 10m) · DEM · LULC · Rainfall
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                      ▼
 M1 Geo-Integrity      M4 Watershed          (parallel, independent
 Validator             Characterization       of the per-asset path)
        │              (drainage, slope,
        ▼               LULC, morphometry)
 M2 AI Image
 Interpreter
        │
        ▼
 M3 Satellite Response
 (NDVI/MNDWI DiD vs
 control, rainfall-adj.)
        │
        ▼
 M5 Scoring: Evidence Score (asset) + Outcome Index (watershed)
        │
        ▼
 M6 Dashboard + Reports + Integration API
```

Full module descriptions, code snippets and rationale: `PLAYBOOK.md` §4.

---

## 8. Data model (authoritative — do not deviate without updating this section first)

*(Switched from PostgreSQL+PostGIS to MongoDB, 2026-09-28 — explicit human decision, mid-build. This is a persistence-layer swap only: every field's name, meaning, and constraint below is identical in intent to the prior SQL version; only the storage mechanics changed. The API contract in §9 is unaffected — verified byte-for-byte identical against live requests before and after the swap.)*

Three collections in one MongoDB database, plus one internal `counters` collection supporting the auto-increment id scheme described below.

```
// mws — micro-watersheds (demo uses HydroBASINS L12 as a stand-in for
// official MWS polygons)
{
  _id:                    string,   // e.g. HYBAS_ID or official MWS code — natural key, not auto-generated
  name:                   string | null,
  project_id:             string | null,
  state:                  string | null,
  district:               string | null,
  geom:                   GeoJSON MultiPolygon,   // 2dsphere-indexed
  baseline_start:         string | null,  // ISO date "YYYY-MM-DD" — start of "before" season window
  baseline_end:           string | null,
  latest_start:           string | null,  // start of "after" season window
  latest_end:             string | null,
  is_synthetic_boundary:  bool,     // default false — true while using HydroBASINS proxy, not official MWS
  created_at:             datetime (UTC),
}
// Indexes: 2dsphere on geom.

// field_record — DRISHTI-style field records
{
  _id:              int,      // app-assigned auto-increment (see counters collection) — replaces SERIAL
  work_code:        string | null,
  mws_id:           string,   // references mws._id (no enforced FK — Mongo has none; app-level integrity only)
  category:         string,   // AM, VM, SM, PT, NC, BN, LS, LH, OM (see §15 Appendix)
  activity:         string,   // e.g. 'Check Dam', 'Farm Pond', 'Contour Bund'
  status:           string | null,  // planned / ongoing / completed / damaged
  lat:              float,
  lon:              float,
  gps_accuracy_m:   float | null,
  orientation:      float | null,
  captured_at:      datetime (UTC) | null,
  photo1_url:       string | null,
  photo2_url:       string | null,
  photo1_phash:     string | null,   // computed on ingest
  photo2_phash:     string | null,
  remarks:          string | null,
  observer_id:      string | null,
  observer_name:    string | null,
  organisation:     string | null,
  geom:             GeoJSON Point,   // 2dsphere-indexed; generated from lat/lon on insert
  is_synthetic:     bool,    // MUST be true for any non-real record. No exceptions.
  photo_source:     string | null,  // 'field' | 'ai_generated' | 'stock_cc' | 'unknown' — required whenever is_synthetic = true
  created_at:       datetime (UTC),
}
// Indexes: 2dsphere on geom; ascending on mws_id.

// asset_evidence — analysis outputs, one document per field_record
{
  _id:                int,      // == the owning field_record._id (1:1, app-enforced — replaces
                                 // `record_id INT PRIMARY KEY REFERENCES field_record(id) ON DELETE CASCADE`;
                                 // Mongo has no native FK/cascade, deletes must be handled in application code)
  geo_flags:          array<{rule, passed, points, max, detail}> | null,  // see §12.1
  geo_score:          int | null,     // 0-30, see §12
  ai_result:          object | null,  // raw classifier JSON, see §12
  visual_score:       int | null,     // 0-30
  sat_result:         object | null,  // ndvi/mndwi pre/post, DiD, rainfall context, see §12
  satellite_score:    int | null,     // 0-30
  temporal_score:     int | null,     // 0-10
  evidence_score:     int | null,     // 0-100, sum of above
  band:               string | null,  // 'verified' | 'review' | 'flag'
  reviewer_decision:  string | null,  // 'confirmed' | 'rejected' | null
  reviewed_at:        datetime (UTC) | null,
  scored_at:          datetime (UTC) | null,
}
// Indexes: ascending on band.

// counters — internal, not part of the domain model. Backs field_record's
// auto-increment id (Mongo has no SERIAL equivalent).
{ _id: "field_record_id", seq: int }
```

Any field added later must be added here first, then implemented — this section is the schema of record.

MongoDB geospatial semantics worth knowing (differ from PostGIS, don't change any of the above): no server-side JOINs (routers do two queries + an in-Python merge where SQL used to JOIN — fine at this scale); no cross-collection FK/cascade enforcement (moot today, no delete endpoint exists yet); `2dsphere` supports `$geoWithin`/`$near`/`$geoIntersects` natively if a future endpoint needs ad-hoc spatial queries — unused today since `services/geo_integrity.py`'s boundary check stays in-process Shapely, unaffected by this swap; BSON has no date-only type, so the `DATE`-shaped fields above are stored as plain ISO strings and parsed at the API boundary.

---

## 9. API contract

| Method & path | Phase | Purpose |
|---|---|---|
| `GET /health` | 1 | Liveness check |
| `POST /mws` | 1 | Create a watershed (boundary GeoJSON + metadata) — used by seed script |
| `GET /mws` | 1 | List watersheds |
| `GET /mws/{id}` | 1 | Watershed boundary (GeoJSON) + summary stats |
| `POST /records` | 1 | Ingest a DRISHTI-schema record (multipart: photo1, photo2, JSON metadata). Runs geo-integrity synchronously; creates `asset_evidence` row with `geo_score` filled, other scores null |
| `GET /mws/{id}/assets` | 1 | GeoJSON `FeatureCollection` of records in this MWS, each feature carrying `evidence_score`/`band` (null until scored) — powers the map pins |
| `GET /assets/{id}` | 1 | Full detail: record fields + full evidence breakdown |
| `POST /assets/{id}/classify` | 2 | Run/re-run AI vision classification, populate `ai_result` + `visual_score` |
| `GET /mws/{id}/thematic/{layer}` | 3 | Tile URL or GeoJSON for a thematic layer (`drainage`, `lulc`, `ndvi_before`, `ndvi_after`, `ndvi_change`, `water`) — reads precomputed results, never calls GEE live |
| `POST /assets/{id}/satellite` | 3 | Attach precomputed satellite response result, populate `sat_result` + `satellite_score` |
| `POST /assets/{id}/score` | 4 | Recompute `evidence_score`/`band` from stored sub-scores (pure function of already-stored data, no external calls) |
| `POST /assets/{id}/review` | 6 | Record a human reviewer decision (`confirmed`/`rejected`) |
| `GET /districts/geotag-coverage` | 5 | Static table of real MIS geotag-coverage numbers, for the district choropleth |
| `GET /mws/{id}/report` | 6 | Generate PDF report card |

Swagger (`/docs`) is our "integration API" evidence for the PPT — keep every endpoint's request/response Pydantic-typed so it renders well.

---

## 10. Functional requirements by phase

Each phase lists what to build **and nothing beyond it**. Phase boundaries exist so the human-review gate stays meaningful — a huge diff is hard to review; a phase-sized diff isn't.

### Phase 1 — Foundation *(serves PS points a, d — the data spine everything else sits on)*
- FR1.1 Repo scaffold: `/api` (FastAPI), `/web` (React+Vite, placeholder only), `/scripts` (empty, for Phase 3), `/docs` (this PRD + CLAUDE.md + PLAYBOOK.md live here)
- FR1.2 PostgreSQL + PostGIS connection (Supabase), schema from §8 as a migration (Alembic or plain versioned SQL — Claude Code's choice, document it)
- FR1.3 `POST /records`, `GET /mws`, `POST /mws`, `GET /mws/{id}`, `GET /mws/{id}/assets`, `GET /assets/{id}`, `GET /health` — implemented per §9
- FR1.4 Geo-integrity validator module (`services/geo_integrity.py`) implementing §12's rules exactly, called synchronously from `POST /records`
- FR1.5 Seed script: loads a watershed boundary from a **configurable GeoJSON file path** (not hardcoded — final watershed choice is still pending, see §14; any placeholder polygon works to unblock this phase, since the real one swaps in later at zero code cost). Generates a CSV of synthetic field records in the Drishti schema, with point coordinates picked **programmatically inside the actual boundary polygon** (e.g. Shapely random-point-in-polygon) rather than hand-typed lat/lons, so the seed data stays valid regardless of which watershed we finalize. Includes 3–4 deliberately-bad rows: one duplicate photo reused across two records, one point placed just outside the boundary, one with `gps_accuracy_m` > 25.
  - **Photo sourcing for this phase:** auto-generate placeholder JPEGs (Pillow + piexif) carrying EXIF GPS/timestamp tags that match — or, for the bad rows, deliberately mismatch or omit — the submitted metadata. No real photography is required to unblock Phase 1; photo *content* realism only starts to matter in Phase 2. Set `photo_source = 'ai_generated'` on every seeded row here — there is no field visit in this timeline (see Phase 2 note below and §13), so AI-generated/reference images are the actual plan, not a placeholder for something else.
- FR1.6 Pytest coverage for the geo-integrity validator: accuracy threshold, in/out of boundary, duplicate photo, missing EXIF, future timestamp
- FR1.7 `.env.example` documenting every required variable

### Phase 2 — AI Image Interpreter *(serves PS point b)*
- FR2.0 **Photo sourcing (no field visit in this timeline):** demo photos for realistic classifier testing come from an open-source image-generation model (tool TBC — see §14) and/or clearly-licensed (CC) reference images, never scraped/unlicensed web images. Every such photo is inserted with `is_synthetic = true` and `photo_source` set accordingly (`'ai_generated'` or `'stock_cc'`) — this stays true in the UI (Phase 5 badge) and in the judge Q&A (`PLAYBOOK.md` §12), not just in the database.
- FR2.1 Vision classifier service, strict enum JSON output per the prompt in `PLAYBOOK.md` §8.3
- FR2.2 `POST /assets/{id}/classify` wired to it; confidence-gating logic (< 0.6 or `uncertain` → band nudged toward `review` regardless of numeric score)
- FR2.3 Visual score computation per §12
- FR2.4 Batch-classify endpoint or script to run classification over all seeded records at once

### Phase 3 — Satellite Intelligence *(serves PS points a, c, d, f)*
- FR3.1 `scripts/precompute_gee.py` — per §12's DiD methodology and `PLAYBOOK.md` §8.2, run once per watershed + asset set, write results to a results table/JSON (never called live from the API)
- FR3.2 Watershed characterization: drainage network (Strahler order) + slope from DEM; LULC snapshot; exported as GeoJSON/PNG per watershed
- FR3.3 `GET /mws/{id}/thematic/{layer}` serving the precomputed outputs
- FR3.4 `POST /assets/{id}/satellite` ingesting precomputed per-asset results into `asset_evidence`
- FR3.5 Satellite score computation per §12

### Phase 4 — Evidence Scoring Engine *(serves PS points d, e)*
- FR4.1 `services/scoring.py` — pure function combining geo/visual/satellite/temporal sub-scores into `evidence_score` + `band`, weights as named constants (not magic numbers), per §12
- FR4.2 `POST /assets/{id}/score`
- FR4.3 Watershed-level Outcome Index (area-weighted satellite DiD + share of assets Verified) — new endpoint or field on `GET /mws/{id}`

### Phase 5 — Map Dashboard (frontend) *(serves PS points a, c, e)*
- FR5.1 React + MapLibre app: watershed map with boundary, toggleable thematic layers (drainage, LULC, NDVI before/after/change, water)
- FR5.2 Asset pins coloured by band (green/amber/red), click → drawer
- FR5.3 Asset drawer: both photos, geo-integrity checklist (✅/❌ per rule), AI result, satellite before/after chips + a treated-vs-control NDVI/MNDWI time-series chart with rainfall bars, final score with a plain-language reason
- FR5.4 Before/after satellite swipe control
- FR5.5 District-level choropleth using `GET /districts/geotag-coverage` (real MIS numbers, entered manually or scraped once — not live-scraped during demo)

### Phase 6 — Reports & Review Queue *(serves PS points e, g)*
- FR6.1 Review queue view: assets sorted by score ascending, reviewer can Confirm/Reject → `POST /assets/{id}/review`
- FR6.2 One-click PDF "Watershed Report Card" (`GET /mws/{id}/report`): maps, Outcome Index, asset table
- FR6.3 Swagger page polish (descriptions, examples) — this is the "integration-ready API" evidence

### Phase 7 — Deploy & Demo Prep
- FR7.1 Deploy: Vercel (frontend), Render/Railway (API), Supabase (DB, already there)
- FR7.2 Final data freeze: confirm demo watershed's precomputed results are loaded, planted bad-record scenarios verified end-to-end
- FR7.3 Record demo video backup (in case live demo fails)

---

## 11. Non-functional requirements

- **Precompute-first.** The live demo must never depend on a live Earth Engine call. GEE runs offline via `scripts/`; results are stored and served from Postgres/static files.
- **Free/open data only.** No paid APIs beyond a small vision-LLM budget for classification calls.
- **Synthetic-data transparency.** `is_synthetic` is enforced at the schema level and must be visually badged in the UI (Phase 5) — never presented as indistinguishable from real data.
- **Explainability over black-box.** Every score must be traceable to its four sub-scores and their underlying flags/results — no single opaque "AI score."
- **Response budget.** Dashboard interactions (layer toggle, pin click) should feel instant — this is why everything is precomputed and read from Postgres, not computed on request.

---

## 12. Scoring specification (authoritative)

### 12.1 Geo-integrity score (max 30) — `services/geo_integrity.py`

| Rule | Points | Logic |
|---|---|---|
| GPS accuracy | 8 / 4 / 0 | ≤10 m → 8; 10–25 m → 4; >25 m or missing → 0 |
| Inside MWS boundary | 8 / 0 | `ST_Contains(mws.geom, record.geom)` |
| EXIF present & consistent | 6 / 3 / 0 | Both GPS+timestamp present and within tolerance (~100 m, same day) of submitted metadata → 6; partial → 3; none → 0 |
| Not a near-duplicate | 5 / 0 | pHash Hamming distance > 6 from every other stored photo → 5; duplicate found → 0 (also raises a flag) |
| Timestamp sane | 3 / 0 | Within project window, not future-dated → 3; else 0 |

Every rule's pass/fail (not just the point total) is stored in `geo_flags` — the UI checklist in FR5.3 reads directly from this.

### 12.2 Visual match score (max 30) — AI Image Interpreter

Scope note: this score answers *"is this photo evidence of the declared activity?"* — not *"did the intervention work?"* (that's §12.3). Don't conflate them.

| `matches_declared` | `confidence` | Points |
|---|---|---|
| yes | ≥ 0.75 | 30 |
| yes | 0.5–0.75 | 20 |
| uncertain | any | 10 (also routes to review queue) |
| no | any | 0 (also raises a flag) |

### 12.3 Satellite response score (max 30) — DiD vs. activity-aware expectation

Expected direction by category (see Appendix §15 for category codes):

| Category | Expected satellite signal |
|---|---|
| PT, NC, SM (ponds, channels, structural/check-dams) | Water extent ↑ and/or NDMI ↑ |
| VM, AM (vegetative, agronomic) | NDVI ↑ |
| BN (bunds) | NDVI/NDMI ↑ in adjoining fields |
| LS, LH, OM (livestock, livelihood, other) | No reliable satellite signal — see note below |

| DiD result | Points |
|---|---|
| Strongly positive, matches expected direction | 30 |
| Weakly positive | 18 |
| ~Zero / inconclusive | 10 |
| Negative (worse than control) | 0 (flag — with a UI caveat that this can also mean "too early post-work," not necessarily failure) |

For LS/LH/OM categories, satellite evidence isn't meaningful — default to 15/30 (neutral) and say so explicitly in the UI rather than pretending precision that doesn't exist.

### 12.4 Temporal consistency score (max 10)

- Multiple photos over time showing logical stage progression (not_started → under_construction → completed) → up to 10.
- Only one time point exists (true for most of our seed data) → default 5/10 (neutral), not penalised. Document this as a known limitation, not a workaround to hide.

### 12.5 Combining into Evidence Score

```
evidence_score = geo_score + visual_score + satellite_score + temporal_score   # 0-100
band = 'verified' if evidence_score >= 70
     else 'review' if evidence_score >= 40
     else 'flag'
```

Weights are named constants in `services/scoring.py`, not scattered magic numbers, and are explicitly called out in the PPT as provisional — "to be calibrated with DoLR domain experts," which is honest and also true.

### 12.6 Outcome Index (per watershed)

Provisional formula (tune once real numbers are in):
```
outcome_index = 0.5 * normalized(area_weighted_ndvi_did)
              + 0.3 * normalized(water_extent_change)
              + 0.2 * (verified_assets / total_assets)
```

---

## 13. Risks & mitigations

| Risk | Mitigation |
|---|---|
| GEE quota/approval hiccups mid-build | Precompute early (Phase 3, hours 6–14 in the team plan); Planetary Computer STAC as fallback |
| Weak NDVI signal at the chosen watershed | Keep a semi-arid backup watershed's precomputed results ready if the primary signal is too subtle for the demo |
| Vision model hallucination | Enum-only JSON, confidence gating, `uncertain` always allowed, never forced to guess |
| Scope creep past a phase's FRs | CLAUDE.md's phase-tracker + "don't build ahead" rule; this PRD is the arbiter if there's disagreement |
| Presenting synthetic data as real | `is_synthetic` flag enforced in schema and UI from Phase 1 onward, no exceptions |
| Pitching as a Srishti replacement | Language check in Phase 6/7: every user-facing string says "plugs into" / "on top of," never "replaces" |
| No time for a field visit inside 48h | All demo photos are AI-generated or CC-licensed reference images, tagged via `photo_source`; judge Q&A (`PLAYBOOK.md` §12) states this plainly rather than implying a field survey happened |

---

## 14. Open decisions (update as resolved)

- [ ] **Final demo watershed** — leading candidate: Marigaon, `HYBAS_ID 4120883730` (strongest NDVI gain, lowest built-up among top candidates). Pending: visual coherence check + confirmation it appears in the WDC-PMKSY MIS district list. Backup candidates: Nalbari `4120885110`, Nalbari `4120874320`. **Schema and seed script must not hardcode this — read from config so switching costs zero code changes.**
- [ ] Vision LLM provider for Phase 2 — decide by cost/quota available on demo day.
- [ ] Scoring weights (§12) — provisional, revisit once real score distribution is visible.
- [ ] AI image-generation tool for synthetic photos — suggested default: **Pollinations.ai** (free, no API key, URL-based: `https://image.pollinations.ai/prompt/<description>`), since it needs zero setup inside a 48h window. Swap for anything else if preferred — the call lives in one place (Phase 2's photo-sourcing script), so switching costs nothing.

---

## 15. Appendix

### 15.1 DRISHTI activity categories (from the official Srishti–Drishti user manual — use these codes exactly, don't invent new ones)

| Code | Category | Example activities |
|---|---|---|
| AM | Agronomic measures | Bench terracing, contour bund, agro-forestry |
| VM | Vegetative measures | Block plantation, grass turfing, farm forestry |
| SM | Structural measures | Check dam, boulder structures, cattle-proof trench |
| PT | Pond–Tanks | Farm pond, percolation tank, recharge pit |
| NC | Nala–Channels | Nala deepening, diversion channel, gully check |
| BN | Bunds | Contour/field/boulder/earthen bund |
| LS | Livestock | Animal health camp, shelter for cattle |
| LH | Livelihood | Horticulture, sericulture, fisheries |
| OM | Others | Jungle clearance, agro service centres |

### 15.2 Reference links

See `PLAYBOOK.md` §5 for the full table (WDC-PMKSY MIS, SRISHTI portal, Bhuvan IWMP manuals, Earth Engine dataset IDs).

### 15.3 Team & parallel work

This PRD is built phase-by-phase through Claude Code with human review at each step (that's this document's audience). The original 6-person parallel role split (GIS, AI/photo, frontend×2, research/pitch) still applies for work that happens *outside* Claude Code — field photo trips, PPT, demo video — see `PLAYBOOK.md` §9. The phases here are the Claude-Code-driven backbone that those parallel workstreams plug data into.