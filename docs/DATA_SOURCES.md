# DATA_SOURCES.md — provenance register

Companion to `docs/REAL_DATA_PLAN.md` §3 rule 2 ("Every dataset has an entry in `docs/DATA_SOURCES.md` and in `GET /provenance`"). Every real (non-synthetic) dataset SAKSHYA uses gets one row here: source, URL, licence, and when it was retrieved. This file is the source of truth `GET /provenance` (R4, backend-engineer) should read from or mirror — coordinate with backend-engineer before restructuring the table, add rows rather than rebuilding it.

Legend: **REAL** = sourced from the dataset below, unmodified in substance. **SYNTHETIC** = generated, not from this table (see `is_synthetic`/`photo_source` on the record itself).

---

## Geospatial boundaries (R1 — geospatial-engineer)

| Dataset | Use in SAKSHYA | URL | Licence | Retrieved | Notes |
|---|---|---|---|---|---|
| SLUSI micro-watersheds | Real treated/control watershed boundary polygons, replacing the Phase 1 placeholder | `https://pub-0429b8e3b5a946e69ea007df844a6f1c.r2.dev/environment/slusi-micro-watersheds/SLUSI_MicroWatersheds.parquet` (bharatlas.com mirror) | CC0-1.0 | 2026-09-28T16:08Z | Third-party mirror of SLUSI (Soil and Land Use Survey of India) data. **Not confirmed** that its MWS codes (e.g. `3B2E1b9`) match SRISHTI's own official MWS codes — flagged in `docs/REAL_DATA_PLAN.md` §2 row 1 and unresolved as of this pass. 453 MB file; read via bbox-column pushdown (duckdb+httpfs, row groups pruned via the file's own `xmin/ymin/xmax/ymax` columns), never loaded whole — see `scripts/fetch_real_boundaries.py`. 1,968 candidate polygons fetched across Marigaon + 5 neighboring districts in ~50s. |
| LGD district boundaries | District geometry (Marigaon + 5 spatially-adjacent districts: Kamrup Metro, West Karbi Anglong, Darrang, Sonitpur, Nagaon — found via `ST_Intersects` against Marigaon, not hardcoded); used to scope the SLUSI query and label candidates by district | `https://bharatlas.com/api/dl/admin/districts/LGD_Districts.parquet` | CC0-1.0 / CC-BY-4.0 (bharatlas.com mirror of Local Government Directory) | 2026-09-28T16:08Z | 785 India districts, 21 MB. `dist_lgd=296` for Marigaon matches the WDC-PMKSY MIS's own `dcode=296` (`docs/REAL_DATA_PLAN.md` §1) — cross-confirms this is the right district (LGD spells it "Marigaon"; WDC-PMKSY/common usage spells it "Morigaon" — same district, `scripts/fetch_real_boundaries.py._fuzzy()` matches either). |
| ESA WorldCover v200 (2021) | Land-cover fractions (crop / built-up / water / tree share) per candidate micro-watershed, used only for the automated treated-candidate ranking (`scripts/candidate_ranking.py`) since no human-confirmed `config/treated_mws.txt` exists yet | `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N24E090_Map.tif` (public AWS Open Data, no auth) | CC-BY-4.0 (ESA WorldCover) | 2026-09-28T16:10Z | 10 m resolution. Single 3°×3° tile `N24E090` covers all 6 target districts except a small sliver of Nagaon/West Karbi Anglong past 93°E (documented gap — candidates entirely in that sliver get `pixel_count=0` and are excluded). Read via `/vsicurl/` windowed access (17,396×17,270 px window, ~40s) — the 98 MB tile is never downloaded whole. Chosen specifically because it needs **no Earth Engine call** — usable while GEE credentials are still blocked (see PROGRESS.md). |
| Copernicus DEM GLO-30 | Mean slope per candidate micro-watershed, same automated-ranking use as above | `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{tile}_DEM/Copernicus_DSM_COG_10_{tile}_DEM.tif` (public AWS Open Data, no auth) | Copernicus DEM licence (free, attribution required — see `spacedata.copernicus.eu`) | 2026-09-28T16:15Z | 30 m resolution, 1°×1° COG tiles; 9 tiles (`N25/N26/N27` × `E091/E092/E093`) mosaicked to cover the full 6-district bbox. Slope computed locally via a simple finite-difference gradient (not a GIS-grade algorithm like GDAL's `DEMProcessing` or `richdem`) — coarse but real, documented as an approximation in `scripts/fetch_real_boundaries.py`. Also needs **no Earth Engine call**. |

**Automated treated-candidate ranking — real result, this run**: with no human-supplied `config/treated_mws.txt` (`docs/REAL_DATA_PLAN.md` §9 item 2, still an open human step), `scripts/fetch_real_boundaries.py` ranked 180 real Marigaon-district candidates by crop share / low built-up / low water share (weights and exclusion thresholds documented in `scripts/candidate_ranking.py` and echoed into `data/real/candidate_ranking.json`'s `method_params`), selected the top-5 (SLUSI codes `3B2E1b9`, `3B2E1r5`, `3B2A4a5`, `3B2E1v2`, `3B2E1r3` — crop share 91-95%, built-up <0.7%, water <2%, mean slope 0.7-4.7°, 700-1,410 ha each) as the demo's "treated" boundary (union polygon, `data/real/treated_boundary.geojson`, centroid ~92.25°E/26.28°N — a few km from the old placeholder polygon's location, in the same part of the district), and found 53 matching control candidates across the 5 neighboring districts (crop share ±15%, slope ±3° — NDVI matching still `"pending_gee"`, see the R2 row below). Every output is labelled `pick_method: "automated_ranking_pending_human_confirmation"`. This is **not** a confirmed mapping to the real `MARIGAON-WDC-1/2021-22` project's actual work sites — the UI must not present it as such. Full ranked list (all 180 candidates, excluded ones with their reason) is in `data/real/candidate_ranking.json`.

---

## Programme statistics (R3 — backend-engineer)

| Dataset | Use in SAKSHYA | URL | Licence | Retrieved | Notes |
|---|---|---|---|---|---|
| WDC-PMKSY 2.0 MIS, Report GT2 — State/District geotag coverage | Real geotag-coverage numbers, `GET /districts/geotag-coverage` (district choropleth, FR5.5) | `https://wdcpmksy.dolr.gov.in/getAllAssetGeoData` (state level) + `getDistWiseAssetGeoData?stcode=<n>&stname=<STATE>` (district level) | Public government data (DoLR/MoRD) — no formal open-data licence tag on the portal itself | 2026-09-28 (report's own "as on" stamp: 28/09/2026 01:09 PM; figures drift live, re-fetch and re-quote before final submission) | 51 districts (Assam 31, Meghalaya 12, Tripura 8). 4 Assam districts show geotagged > total in the government's own live MIS — a source-side reconciliation quirk, not a transcription error (see `api/app/services/district_coverage.py`'s docstring). **Cross-checked against the row below's independent, more granular fetch for Morigaon: 309 total / 267 geotagged / 42 non-geotagged in both — no discrepancy.** |
| WDC-PMKSY 2.0 MIS, Report GT2 — Marigaon work-code registry (`MARIGAON-WDC - 1 /2021-22`, projid 90) | Real registry aggregates + exact moderation backlog, `GET /programme/marigaon`; per-work-code detail, `scripts/output/registry/workcodes_marigaon_wdc1.csv` | Full drill-down: `getAllAssetGeoData` → `getDistWiseAssetGeoData?stcode=18&stname=ASSAM` → `getProjWiseAssetGeoData?dcode=296&stname=ASSAM&distname=MARIGAON` → `getProjDtlAssetGeoData?projid=90&stname=ASSAM&distname=MARIGAON&projname=MARIGAON-WDC - 1 /2021-22` | Public government data (DoLR/MoRD) — same as above | 2026-09-28T10:25:58+00:00 (work-code detail page; earlier drill-down steps retrieved a few seconds before, see `scripts/output/registry/programme_marigaon.json`'s `retrieved_at`) | 263 total work codes, 240 geotagged (73 NRM / 11 EPA / 112 Livelihood / 67 Production) — the work-code detail table itself only lists the 240 **geotagged** ones (no Pre/Mid/Post status exists for the 23 non-geotagged codes). **Moderation backlog, computed exactly, not estimated: 51.2% (123/240) of geotagged work codes are still "Yet to Moderate" at Pre-Implementation** (mid/post are mostly `not_submitted` — most works haven't reached those stages yet). A 4th status state ("Not Submitted", blank cell) and a rare "mixed" state (one work code has both "Accepted" and "Rejected" at Pre-Implementation — two separate submissions) were found empirically; neither is documented in `docs/REAL_DATA_PLAN.md` §1. Activity → PRD §15.1 category mapping follows `docs/REAL_DATA_PLAN.md` §5's proposed keyword table exactly; 4 activities it doesn't cover (`Borewell and Hand Pump`, `Rural Infrastructure`, `Farm implement`, the NRM group's literal `Others`) default to `OM` and are listed in the JSON output's `unmapped_activities`, never silently guessed as something more specific. Fetched once, ≤1 req/sec, identified User-Agent, raw HTML cached at `scripts/cache/gt2/` (gitignored, reproducible — reruns of `scripts/fetch_gt2.py` read that cache and make zero new requests). |

---

## Synthetic / demo data (Phase 1 — backend-engineer)

Not from an external source — generated by this project. Listed here for R4 completeness (`docs/REAL_DATA_PLAN.md` §3 rule 2: *every* dataset gets an entry, real or synthetic) and because CLAUDE.md treats `is_synthetic` transparency as non-negotiable, not optional polish.

| Dataset | Use in SAKSHYA | Source | Licence | `is_synthetic` / `photo_source` | Notes |
|---|---|---|---|---|---|
| Drishti-schema seed field records | Phase 1 demo dataset powering the map dashboard (asset pins, evidence drawer) | Generated by `scripts/seed_data.py` / `scripts/seed/generate_records_csv.py` — not sourced from any third party | N/A | `is_synthetic=true`, `photo_source='ai_generated'` on every row, no exceptions | Point coordinates placed programmatically inside the demo watershed boundary (Shapely random-point-in-polygon), never hand-typed. Photos are Pollinations.ai-generated JPEGs with matching (or, for 3-4 deliberately-bad rows, deliberately mismatched/missing) EXIF GPS/timestamp tags — no field visit occurred in this timeline (PRD FR1.5/FR2.0). **Never attached to a real government work code** — kept fully separate from the real WDC-PMKSY registry rows above, per `docs/REAL_DATA_PLAN.md`'s hard rule. |

---

## Satellite analysis (R2 — geospatial-engineer)

| Dataset | Use in SAKSHYA | Source | Licence | Status |
|---|---|---|---|---|
| Landsat 8/9 Collection 2 Level 2 | Dry-season NDVI/MNDWI/NDMI composites, treated-vs-control DiD | Google Earth Engine (`LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2`) | Open (USGS); Earth Engine terms of use apply | **Blocked** — GEE service account lacks `roles/serviceusage.serviceUsageConsumer` on the `green-dukan` GCP project (see PROGRESS.md "Needs your attention"). Methodology and scripting are complete and ready to run the moment credentials work; no live numbers exist yet — `placeholder: true` everywhere a real value would go. |
| CHIRPS daily rainfall | Seasonal rainfall bars, DiD confounder context | Google Earth Engine (`UCSB-CHG/CHIRPS/DAILY`) | Open (UCSB Climate Hazards Group) | **Blocked**, same reason as above. |
| ESA WorldCover v200 | Watershed-level LULC thematic layer | Google Earth Engine (`ESA/WorldCover/v200`) *or* the direct AWS S3 COG source (see geospatial row above) | CC-BY-4.0 | Thematic-layer raster export via GEE is blocked; the AWS S3 COG source is already in real use for R1's candidate ranking and could serve this layer too without GEE if needed. |
| SRTM 30m / Copernicus DEM | Slope layer for the watershed report card | Google Earth Engine (`USGS/SRTMGL1_003`) *or* the direct Copernicus DEM S3 COG source (see geospatial row above) | Open (USGS) / Copernicus DEM licence | GEE path blocked; the S3 COG source is already in real use for R1 and is the practical fallback. |

---

## Photo/classifier benchmark (R5 — vision-ai-engineer)

*(vision-ai-engineer: add rows here for the ≥20 CC-licensed real photos used in the classifier accuracy benchmark — source URL, author, licence per file, per `docs/REAL_DATA_PLAN.md` §8's R5 row.)*

---

## Maintenance

- Add a row here **before** a script depends on a new external dataset, not after.
- `retrieved_at` should be the actual fetch date, not the date this file was edited, if they differ.
- If a source is later found to be wrong, blocked, or superseded, strike it through and say why rather than deleting the row — keeps the provenance history honest for judge Q&A.
