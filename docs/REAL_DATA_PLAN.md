# REAL_DATA_PLAN.md — Making SAKSHYA run on real data

Companion to `PRD.md` / `AGENTS.md`. Written 2026-09-28 after a source hunt.
Legend: ✅ = opened and read during the hunt · ⚠️ = could not verify; a human or agent must check before relying on it.

---

## 0. TL;DR

- **What can be made real in the time left:** the watershed boundary, the satellite analysis, the programme statistics, the work-code registry (aggregates), the classifier's measured accuracy, and a small sample of real public photos.
- **What cannot be real:** DRISHTI's WDC photo archive is not public (login-gated). Do not pretend otherwise. Public geotagged photos of the *same asset class* exist under MGNREGA (Bhuvan), see §2 — a small, honestly-labelled sample is possible.
- **Hard rule:** never attach a synthetic coordinate or synthetic photo to a real government work code. That would fabricate a claim about a real public work.
- **Best real story found:** Marigaon (Assam) has a real WDC-PMKSY project, `MARIGAON-WDC - 1 /2021-22`, with 73 completed NRM works. Baseline 2019-20 → latest 2025-26 brackets the project start cleanly.

---

## 1. Verified facts (all ✅, live figures as on 27–28 Sep 2026)

Source: WDC-PMKSY 2.0 MIS, Report GT2 (public). State → district → project → work-code drill-down works by URL:
`https://wdcpmksy.dolr.gov.in/getAllAssetGeoData` → `getDistWiseAssetGeoData?stcode=18&stname=ASSAM` → `getProjWiseAssetGeoData?dcode=296&stname=ASSAM&distname=MARIGAON` → `getProjDtlAssetGeoData?projid=90&...`

| Fact | Value |
|---|---|
| India | 1,221 projects · 9,23,594 work codes · 7,06,303 geotagged · 2,17,291 not geotagged |
| Assam | 38 projects · 15,178 work codes · 13,972 geotagged (~92%) |
| Other NE states (work codes / geotagged) | Meghalaya 13,460 / 4,299 (~32%) · Tripura 15,648 / 2,775 (~18%) · Arunachal 3,515 / 2,406 (~68%) |
| Marigaon district | 2 projects · 309 work codes · 267 geotagged · 42 not |
| `MARIGAON-WDC - 1 /2021-22` (projid 90) | 263 work codes (NRM 73, EPA 11, Livelihood 112, Production 67) · 240 geotagged · all 73 NRM works "Completed" |
| `MARIGAON-WDC - 2 /2025-26` (projid 1278) | 46 work codes (NRM 42: 12 not started, 30 completed; EPA 4) · 27 geotagged. Too recent for outcome analysis |

Notes:
- Figures drift between pages (Assam geotagged is 13,972 on the state page and 13,974 on the district page). Re-fetch on submission day and quote the "as on" timestamp.
- **Work-code format** (inferred from the pattern, ⚠️ confirm): `P18296000090-11264` = `P` + state 18 + district 296 + project 000090 + `-` + work no.
- **Each work code has Pre / Mid / Post implementation columns** whose values are `Accepted`, `Yet to Moderate` or `Rejected`. My reading: the moderation state of the geotagged photo at each stage. ⚠️ Confirm in the Srishti–Drishti user manual before stating it as fact.
- **Approximate NRM mix in project 1** (from page text, not a parsed table): ~21 farm ponds, ~21 contour bunds, 2 check dams, 2 Amrit Sarovar, plus graded bunds and drainage channels. Roughly a third of NRM rows show only `Yet to Moderate`. **Recompute exactly with a script (R3) before quoting any number.**

---

## 2. Source catalogue

| # | Dataset | Use in SAKSHYA | Where | Licence / terms | Status |
|---|---|---|---|---|---|
| 1 | **SLUSI micro-watersheds** (3,21,763 polygons; the finest watershed tier) | Real boundary instead of HydroBASINS L12 | bharatlas mirror: `https://bharatlas.com/view/slusi_micro_watersheds` · parquet 452.9 MB (`pub-0429b8e3b5a946e69ea007df844a6f1c.r2.dev/environment/slusi-micro-watersheds/SLUSI_MicroWatersheds.parquet`), PMTiles 151 MB, viewer exports filtered GeoJSON | CC0-1.0 | ✅ listing read. ⚠️ third-party mirror of SLUSI data; confirm attributes and that codes match SRISHTI's MWS codes (likely same tier, not guaranteed) |
| 2 | **CWC WRIS layers** on bharatlas: watersheds (4,569), waterbodies (8,51,093 polygons), rivers (30,546), dams, sub-basins | Context layers: real ponds/tanks/rivers on the map | `bharatlas.com/view/wris_waterbodies`, `wris_watersheds`, `wris_rivers` | CC0-1.0 | ✅ listing read |
| 3 | **LGD district / block boundaries** (785 districts; 7,146 blocks) | District choropleth; locating Marigaon | `bharatlas.com/api/dl/admin/districts/LGD_Districts.parquet` (21 MB) | CC0-1.0 / CC-BY-4.0 | ✅ listing read |
| 4 | **WDC-PMKSY MIS GT2** | Real coverage numbers, work-code registry | URLs in §1 | Public government data. Fetch once, politely, cite "as on" | ✅ opened |
| 5 | **data.gov.in**: district-wise KPIs of WDC-PMKSY 2.0; shape files of watershed boundaries; hydrological boundaries | Cross-check of #1 and #4 | `data.gov.in/resource/district-wise-data-key-performance-indicators-wdc-pmksy-20-date` | GODL-India | ⚠️ site blocks automated fetch (robots). Human downloads manually |
| 6 | **Landsat 8/9 C2 L2, Sentinel-2 SR, Sentinel-1 GRD, CHIRPS daily, ESA WorldCover v200, MERIT Hydro, JRC GSW, SRTM** | The whole satellite pipeline | Earth Engine | Open; Earth Engine terms apply (see §9 on non-commercial registration) | ✅ (IDs from PLAYBOOK §5.3) |
| 7 | **Bhuvan-MGNREGA geotagged assets with two photos each** (crores of assets; MoRD/NRSC state they are in the public domain) | Small sample of real geotagged NRM photos (ponds, check dams) | Bhuvan portal / Jan-MGNREGA app: `bhuvan-app2.nrsc.gov.in/mgnrega/` | Public per MoRD statements. ⚠️ **No documented bulk API found; bulk-scraping terms unverified.** | ✅ existence confirmed via news/NRSC pages. ⚠️ access path untested |
| 8 | **CoRE Stack** pan-India datasets (incl. NREGA geotagged-asset metadata, micro-watershed hydrology, GEE app) | Possible asset metadata for MGNREGA works | `core-stack.org/datasets/` | ⚠️ download links were blank on the page; site says "write to us" | ⚠️ |
| 9 | **Wikimedia Commons "Category:Check dams"** (39 files incl. a 2025 Kerala check-dam photo) | Real photos for the classifier benchmark | `commons.wikimedia.org/wiki/Category:Check_dams` | **CC licence differs per file.** Record author + licence per file | ✅ category read; ⚠️ per-file licences unchecked |
| 10 | **TERI case study, RCC check dam, Dhubri-III IWMP (Assam)** | Narrative evidence that these interventions matter in Assam | `teriin.org/sites/default/files/2018-03/case-study-RCC-check-dams-Assam.pdf` | Cite only | ✅ |
| 11 | Srishti WDC 2.0 public viewer and Tejas Bharat map | Locate the Marigaon project on the map; find its micro-watersheds | `bhuvan-app1.nrsc.gov.in/wdc2.0/` · `wdcpmksy.dolr.gov.in/tejasBharatMap` | Public | ⚠️ both are JavaScript apps I could not read. **Human step (§9)** |

---

## 3. Reality ladder and integrity rules

| Tier | What | How | Labels in DB and UI |
|---|---|---|---|
| **1 — real, automated** | MWS boundary, satellite series, programme stats, work-code registry aggregates, WRIS water layers | R1–R4 | `REAL` chip with source + retrieved_at |
| **2 — real, semi-manual** | 10–25 real geotagged NRM assets with photos from the public Bhuvan viewer | Human curates a CSV + photos (R7); no scraping | `is_synthetic=false`, `photo_source='field'`, and `source='Bhuvan MGNREGA public view'`. **Say plainly it is MGNREGA, not WDC.** |
| **3 — synthetic, on purpose** | Planted bad records (duplicate photo, out-of-boundary, mismatch) | Existing seed | `SYNTHETIC` chip, IDs like `DEMO-0001`, never a real work code |

Rules:
1. Real work-code registry rows carry **no coordinates or photos unless a real source provides them.**
2. Every dataset has an entry in `docs/DATA_SOURCES.md` and in `GET /provenance` (name, URL, licence, retrieved_at, real/synthetic).
3. Never show a number in the UI that the API did not return.
4. Wording: "association", not "impact proven". 30 m data cannot see a check dam; say so before a judge does.

---

## 4. Real analysis design

**4.1 Watershed-level DiD (no asset coordinates needed).** Treated = micro-watersheds of the Marigaon WDC-1 project area. Controls = neighbouring micro-watersheds with no WDC project, matched on baseline dry-season NDVI (±10%), crop share (±15%) and slope, excluding polygons with high built-up or permanent-water share. This sidesteps the fact that public work-code pages carry no coordinates, and it avoids the "30 m cannot see a check dam" trap.

**4.2 Time series (the chart that wins the room).** Annual dry-season (Nov–Feb) median NDVI and MNDWI per polygon, 2016→2026, Landsat 8/9 (add Sentinel-2 from 2019 if cheap). Plot treated vs control mean with a band, a vertical line at project start (2021-22), CHIRPS Jun–Sep rainfall as bars. Effect = change in the treated–control gap, pre vs post, with a bootstrap interval over control polygons. Document the year-labelling convention.

**4.3 Confounders to state openly.** Marigaon is Brahmaputra floodplain: floods, erosion and sandbar shifts can swamp water signals. Prefer polygons away from the main channel, keep dry-season windows, and show the rainfall bars. Water metrics are secondary to NDVI here.

**4.4 Asset-level (Tier 2 only).** Keep the treated-buffer vs control-ring DiD from PRD §12.3 for real assets that have real coordinates. Nothing else gets asset-level satellite scores.

---

## 5. Work-code registry and the moderation backlog

Script (R3) fetches the GT2 project page once, parses by **column index** (not by text order, since the raw text loses column positions), and writes `workcodes_marigaon_wdc1.csv`: `work_code, head, activity, drishti_category, pre_status, mid_status, post_status, source_url, retrieved_at`.

Proposed activity → category mapping (⚠️ confirm against the Srishti manual): Farm Ponds, Amrit Sarovar → `PT` · Check dams → `SM` · Contour/Graded Bunding → `BN` · Irrigation/Drainage Channel → `NC` · Others (vegetative/engineering) → `OM` · Goatery/Piggery/Dairy/Duckery → `LS` · Bee keeping, Weaving, Handloom, Handicraft, Horticulture, Fisheries → `LH`.

**Why this matters for the pitch:** the real workflow already has human moderators accepting or rejecting photos, and a visible share of works sits at `Yet to Moderate`. SAKSHYA is decision support for that queue: it ranks what to moderate first. Put the exact backlog percentage (computed by R3, not my estimate) on a slide.

---

## 6. Competitor note

A public repo, `M-Kishore92/Walkouts035-SIH26015` ("DRISHTI–SRISHTI Intelligence Bridge"), targets the same statement with a very similar core: photo classification, satellite cross-validation, a verification queue, a Watershed Impact Index, auto-generated reports and a hash-chained ledger. It is seeded with sample Nanded data and marked all-rights-reserved. **Do not copy from it.** Differentiate on:
- real Marigaon case (real MIS numbers, real project, real work-code registry);
- matched-control DiD with a visible time series and rainfall, not a single index;
- alignment with the real moderation workflow (Accepted / Yet to Moderate / Rejected);
- provenance chips and honest labelling of what is real and what is not;
- Northeast India focus (Assam 92% geotagged vs Tripura 18%).

SIH Buddy estimates 140–330 teams for this statement (its own guess; check the live counter). An indicative college report weights judging as technical approach 30%, innovation 20%, feasibility/scalability 20%, presentation 20% (not an official rubric).

---

## 7. Winning dashboard spec (R6)

**The 3-minute story, one screen per beat:**
1. **Command strip:** India MIS numbers (7,06,303 of 9,23,594 geotagged) with the "as on" stamp; NE comparison bars.
2. **Assam → Marigaon drill-down:** district choropleth (LGD boundaries) of geotag coverage; Marigaon 267 / 309.
3. **Project view:** real MWS boundary, WRIS waterbodies, drainage, Landsat before/after swipe (2019-20 vs 2025-26).
4. **Impact curve:** treated vs control NDVI 2016→2026, project-start marker, rainfall bars, effect size with interval, one-line caveat.
5. **Evidence drawer** for a Tier 2 or demo asset: photos, integrity checklist, AI reading, score breakdown, provenance chip.
6. **Moderation queue:** works ranked for review, with the real backlog figure.
7. **Report export** and a "Methods & limits" drawer.

**Design:** map-first, dark UI with one accent colour, strong type hierarchy, big KPI numerals, skeleton loaders, smooth layer transitions, keyboard-accessible, mobile-responsive, honest empty/error states. Use the `frontend-design` skill. A "Guided tour" button steps through the seven beats and resets cleanly.

**Provenance chips everywhere:** `REAL · <source>` / `SYNTHETIC · demo` / `PLACEHOLDER`. A visible provenance panel is a credibility feature, not clutter.

**Performance:** everything precomputed and static; first meaningful paint < 2 s; no live Earth Engine call.

---

## 8. Reality Pass slices

| Slice | Owner | Work | Done when |
|---|---|---|---|
| **R0** | orchestrator | Smoke-test the service account: `ee.Initialize(creds, project=...)`, then count Landsat scenes over Marigaon. Fix `.env.example` (`GOOGLE_APPLICATION_CREDENTIALS`, `GEE_PROJECT_ID`). On failure, log the exact error and continue with other slices | Pass/fail with exact message in PROGRESS.md |
| **R1** | geospatial-engineer | Real boundaries: read SLUSI micro-watersheds + LGD districts (DuckDB spatial or pyarrow with a bbox filter, since the parquet is 453 MB and RAM is tight; or use a viewer-exported GeoJSON). Keep Marigaon and neighbouring districts. Treated polygon IDs come from `config/treated_mws.txt` (human step §9); fallback = rank candidates by crop share / low built-up / slope. Write `data/real/*.geojson`, load `mws` with `is_synthetic_boundary=false` and a source note | Real polygons load; UI shows REAL boundary |
| **R2** | geospatial-engineer | Real Earth Engine analysis per §4.1–4.3: annual series, matched controls, DiD with bootstrap, CHIRPS bars, thematic rasters (NDVI before/after/change, WorldCover, MERIT drainage). Export `timeseries.json`, `did_summary.json` with all method parameters. Keep `placeholder:true` wherever data is still not real | Real numbers in `did_summary.json`; parameters recorded |
| **R3** | backend-engineer | `scripts/fetch_gt2.py` (one pass, ≤1 req/s, cache raw HTML, identify the script in the User-Agent) → state/district/project JSON + the work-code CSV; implement `GET /districts/geotag-coverage` (FR5.5) and `GET /programme/marigaon` (registry aggregates + exact moderation backlog) | Coverage tab shows real numbers; backlog computed, not estimated |
| **R4** | backend-engineer | `docs/DATA_SOURCES.md` and `GET /provenance` for every dataset used | Every UI number traces to a source |
| **R5** | vision-ai-engineer | Real-photo benchmark: ≥20 CC-licensed real photos (record URL, author, licence per file), run the current Ollama model and one alternative, write `docs/CLASSIFIER_BENCHMARK.md` with a confusion matrix, expose measured accuracy via API. Never quote accuracy from the AI-generated set as real-world accuracy | Measured accuracy on real photos is in the UI |
| **R6** | frontend-engineer | Dashboard per §7 | Seven beats work end to end, with screenshots in `docs/screenshots/` |
| **R7** | human + backend | Optional Tier 2: you supply `data/real/assets_manual.csv` + photos; the agent adds an ingestion helper with EXIF/pHash checks. No scraping | Real assets show `photo_source='field'` and the MGNREGA source label |

Run order: R0 → (R1, R2, R3, R4, R5 in parallel, max three agents at once to avoid the earlier rate limit) → R6 → R7.

---

## 9. Human checklist (only you can do these)

1. **Earth Engine access.** In the Cloud project that owns the service account: enable the Earth Engine API, register the project for Earth Engine, grant the service account `roles/serviceusage.serviceUsageConsumer` **and** one of `roles/earthengine.viewer|writer`. **Prefer a separate project registered for non-commercial use** rather than the Green Dukan company project; commercial vs non-commercial is decided per project, and a company project may need a commercial registration.
2. **Find the project area (10 min).** Open Srishti (`bhuvan-app1.nrsc.gov.in/wdc2.0/`) or the Tejas Bharat map, locate `MARIGAON-WDC - 1 /2021-22`, and note its villages/blocks and micro-watershed codes. Save them in `config/treated_mws.txt` (or send screenshots).
3. **Optional Tier 2.** If Srishti or the Bhuvan MGNREGA viewer shows photos for assets near the project, record 10–25 of them by hand (lat/lon, activity, source URL, date) with a small note on scheme and licence.
4. **Check the SIH portal:** the deadline (reported as 30 Sep 2026) and the idea counter for 26015. **PPT and the demo video are not covered by any agent.**

---

## 10. Things I could not verify

- Whether Srishti's public view shows photos, and whether Bhuvan permits any bulk export (no documented API found).
- The exact meaning of Pre/Mid/Post statuses (reading is plausible, not confirmed).
- Whether SLUSI polygon codes match SRISHTI's micro-watershed codes.
- `bharatlas.com/mcp` (advertised MCP endpoint), CoRE Stack download links, and per-file Commons licences.
- data.gov.in resources (bot-blocked).
