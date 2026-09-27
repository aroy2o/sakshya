# SIH 2026 — PS 26015 Playbook
## Geospatial Visualization & Analysis of Geo-Coded Images for Watershed Development Outcomes
**Ministry of Rural Development · Dept. of Land Resources (DoLR) · Software · Agriculture, FoodTech & Rural Development**

---

## 0. TL;DR — what to build

Build an **analytics layer on top of SRISHTI–DRISHTI** that turns the lakhs of geo-tagged field photos (currently used only as "proof of work") into **verified, satellite-backed evidence of watershed outcomes**.

For every geo-coded photo of a watershed asset (check dam, farm pond, plantation, bund…):

1. **Validate the photo** — GPS accuracy, inside the micro-watershed, timestamp sane, not a duplicate/reused image.
2. **Interpret the photo with AI** — what structure is it, what stage, is there water/vegetation, does it match the declared activity?
3. **Cross-check with 30 m satellite data** — did vegetation/water around that asset actually improve after the intervention, compared to untreated land nearby and adjusted for rainfall?
4. **Score it** — an *Evidence Score* per asset and a *Watershed Outcome Index* per micro-watershed.
5. **Visualize it** — map dashboard with thematic layers (LULC, drainage, vegetation, water, change detection), before/after swipe, photo pins coloured by verification status, district drill-down, auto-generated PDF report.

**One-line pitch:** *"Photos show what was built. Satellites show whether it worked. We fuse both so DoLR knows which of its 9 lakh+ watershed works are delivering — and which ones need a field visit."*

Working name suggestion: **SAKSHYA** (साक्ष्य = evidence) — or anything you like.

---

## 1. Understand the problem (plain language)

### 1.1 What is watershed development?
A watershed = an area of land where all rain drains to one common outlet (a stream/river point). Government treats it as the unit for rural land & water development. Under **WDC-PMKSY 2.0** (Watershed Development Component of Pradhan Mantri Krishi Sinchayee Yojana, run by DoLR), they build things like:

- **Structural / water**: check dams, farm ponds, percolation tanks, recharge pits, gully plugs, nala deepening
- **Bunds / soil**: contour bunds, field bunds, boulder bunds, trenches, terracing
- **Vegetative**: block plantation, grass turfing, agro-forestry
- **Livelihood / livestock / production**: horticulture, fisheries, vermicompost etc.

### 1.2 What are SRISHTI and DRISHTI?
Both were built by **NRSC (ISRO)** for DoLR on the **Bhuvan** platform.

| Name | What it is | Who uses it |
|---|---|---|
| **SRISHTI** | Web GIS portal on Bhuvan — satellite imagery, micro-watershed boundaries, thematic layers (LULC, soil, erosion), swipe comparison, DPR/action plan upload | DoLR admins, State Level Nodal Agencies (SLNA), district cells (WCDC), citizens (view-only) |
| **DRISHTI** | Android app for field staff — captures geo-coded, time-stamped photos of each watershed work and sends to Bhuvan | Field functionaries |

Per the official Srishti–Drishti user manual, **a DRISHTI record contains**: activity category (9 categories, ~85 activities: Agronomic, Vegetative, Structural, Pond-Tanks, Nala-Channels, Bunds, Livestock, Livelihood, Others), latitude, longitude, GPS accuracy (field staff are told to wait until accuracy ≤ 10 m), photo orientation, timestamp, 2 photographs, a text tag, activity status, remarks, and observer profile (user ID, name, phone, organisation).

👉 **Use exactly this schema** for your data model. Judges from DoLR/NRSC will instantly recognise it — shows you did homework.

### 1.3 The actual gap (read the PS carefully)
The PS says it directly:
- Geo-tagged photos are used **only for documentation**, not analysis.
- No **standardized visualization framework** to get actionable insight from them.
- Hard to **integrate field photos with satellite data, thematic layers and watershed boundaries**.
- Hard to **track spatial change and measure intervention impact**.

So the problem is **NOT** "build a new portal" or "build a new photo app". DoLR already has both. The problem is: **the data exists, nobody is interpreting it.** Your solution = the interpretation + visualization brain.

⚠️ **Do not pitch a replacement for Srishti.** The judges' own organisation built it. Pitch an *analytics layer that plugs into Srishti/Drishti via API*.

### 1.4 Real numbers for your PPT (from the public WDC-PMKSY 2.0 MIS)
From the MIS report **"GT2 – Work Code Status with Geotagging Details"** (public, report as on 27 Sep 2026):

| Metric (All India) | Value |
|---|---|
| Projects | 1,221 |
| Total work codes (excl. foreclosed) | 9,23,594 |
| Geo-tagged work codes | 7,06,303 |
| **Not geo-tagged** | **2,17,291** (~23.5%) |

North-East angle (useful since you're from Assam):

| State | Total work codes | Geo-tagged | Share geo-tagged |
|---|---|---|---|
| Assam | 15,178 | 13,972 | ~92% |
| Meghalaya | 13,460 | 4,299 | ~32% |
| Tripura | 15,648 | 2,775 | ~18% |
| Arunachal | 3,515 | 2,406 | ~68% |

**Story for the pitch:** ~7 lakh works are geo-tagged — nobody can manually inspect 7 lakh photos. Our system triages them automatically and tells officers which ~5% to physically visit. And for states with low geotag coverage, the dashboard exposes the gap.

(Re-check these numbers on the day of submission — the page updates live. Link in §5.)

---

## 2. Expected solutions (a–g) → decoded into features

| PS expectation | What it really means | Your feature |
|---|---|---|
| **a) Integrated Geospatial Visualization Framework** | One map where photos + satellite + watershed boundaries + thematic layers live together | Map dashboard with layer stack: MWS boundaries, photo pins, LULC, drainage, NDVI, water, change maps |
| **b) Improved Geo-Coded Image Interpretation** | Convert photos into information (what, what stage, water? vegetation?) | AI photo interpreter + geo-integrity validator |
| **c) Thematic Maps & Visualization Products** | Land use map, drainage map, vegetation map, intervention map, change detection | Auto-generated per micro-watershed; exportable PNG/PDF/GeoJSON |
| **d) Enhanced Monitoring & Assessment** | Fusion of photos + satellite improves accuracy & efficiency | Per-asset Satellite Response check (before vs after vs control) |
| **e) Scientific Support for Decision-Making** | Spatially validated, defensible evidence | Evidence Score + Watershed Outcome Index + methodology note + PDF report card |
| **f) Scalable & Cost-Effective** | Must work nationally, cheaply | 100% free/open data (Landsat, Sentinel, SRTM), server-side processing (Earth Engine), open-source stack |
| **g) Strengthen SRISHTI-DRISHTI usage** | Make their platform more valuable | Drishti-compatible schema, Srishti integration API, optional "Drishti++" smart capture checks |

The scope table also says: **"Narrow, specialized, analytical, and visualization-oriented."** → Judges want depth and scientific correctness, not 40 shallow features. Don't build login systems, role hierarchies, SMS alerts etc. beyond the bare minimum.

---

## 3. The key technical insight (this is what will impress NRSC judges)

**30 m resolution cannot see a check dam.** A typical check dam or farm pond is 5–30 m. At 30 m, it's 1 mixed pixel or less. Teams who say "we'll detect check dams from 30 m satellite imagery" will get torn apart by NRSC scientists.

The correct framing:

| Source | What it's good at | What it can't do |
|---|---|---|
| **Geo-coded photo** | Ground truth of the *structure*: exists? type? built? condition? | Can't show impact over the landscape or over years |
| **30 m satellite (Landsat / SRISHTI data)** | *Landscape response*: vegetation greening, water spread, cropland change in the area around/downstream of the structure and across the whole micro-watershed | Can't see the structure itself |
| **10 m Sentinel-2 (bonus)** | Bigger ponds / plantation blocks directly visible | Still not small bunds |

**So: photo = "was it built?", satellite = "did it work?"** Fusion = both. Say this sentence in the pitch.

Second insight — **impact needs a control**. Vegetation can increase just because it rained more that year. So compare:
- **Treated zone** (buffer around asset / inside micro-watershed) vs **control zone** (similar land just outside), before vs after → **Difference-in-Differences (DiD)**.
- Normalize with rainfall (CHIRPS).
- Compare the **same season** each year (e.g., post-monsoon Oct–Dec or Rabi Jan–Mar), never monsoon vs summer.

Third insight (NE-specific, shows maturity) — **clouds**. In Assam/Meghalaya, optical imagery is cloudy June–Sept. Use dry-season median composites, and **Sentinel-1 SAR** (radar sees through clouds) for water-body extent.

---

## 4. Solution architecture

```
            ┌────────────────────────────────────────────────────────────┐
            │                   INPUT LAYER                              │
            │  DRISHTI-format records (photo + lat/lon + accuracy +      │
            │  timestamp + activity + status)  ·  MWS boundaries  ·     │
            │  Satellite (Landsat 8/9 30m, Sentinel-2 10m, S1 SAR)      │
            │  DEM (SRTM/CartoDEM 30m) · LULC · Rainfall (CHIRPS)       │
            └──────────────┬─────────────────────────────┬──────────────┘
                           │                             │
             ┌─────────────▼────────────┐   ┌────────────▼─────────────┐
             │ M1 Geo-Integrity         │   │ M4 Watershed             │
             │ Validator                │   │ Characterization         │
             │ EXIF/GPS/boundary/dup    │   │ drainage, slope, LULC,   │
             └─────────────┬────────────┘   │ morphometry              │
             ┌─────────────▼────────────┐   └────────────┬─────────────┘
             │ M2 AI Image Interpreter  │                │
             │ type, stage, water, veg, │                │
             │ match vs declared        │                │
             └─────────────┬────────────┘                │
             ┌─────────────▼────────────┐                │
             │ M3 Satellite Response    │                │
             │ NDVI/MNDWI pre-post,     │                │
             │ DiD vs control, rainfall │                │
             └─────────────┬────────────┘                │
                           │                             │
             ┌─────────────▼─────────────────────────────▼─────────────┐
             │ M5 Scoring: Evidence Score (asset) + Outcome Index (MWS) │
             └─────────────┬────────────────────────────────────────────┘
             ┌─────────────▼────────────────────────────────────────────┐
             │ M6 Visualization Dashboard + Reports + Integration API   │
             └──────────────────────────────────────────────────────────┘
                      (stretch) M7 Drishti++ smart capture PWA
```

### M1 — Geo-Integrity Validator
For each photo record, compute flags:
- **EXIF present?** GPS lat/lon, DateTimeOriginal, orientation. Missing EXIF but metadata present = weaker evidence.
- **GPS accuracy** ≤ 10 m (Drishti's own rule).
- **Inside the micro-watershed polygon** (PostGIS `ST_Contains`) — outside = flag.
- **Timestamp** within project period; not in the future; not before sanction.
- **Duplicate / reused photo** — perceptual hash (pHash) across the whole dataset; Hamming distance ≤ ~6 = near-duplicate. Same photo submitted for two different works → strong flag.
- **Photo–photo consistency** — the 2 photos of the same asset should be within a few metres.
- **Image quality** — blur check (Laplacian variance), too dark, screenshot-of-screen detection (optional).

Output: `geo_integrity` sub-score 0–30 + list of flags.

### M2 — AI Image Interpreter
Classify each photo into Drishti's taxonomy + extract attributes:
- `predicted_category` (Structural / Pond-Tank / Bund / Vegetative / …) and `predicted_activity` (check dam, farm pond, contour bund, plantation…)
- `construction_stage`: not started / under construction / completed / damaged
- `water_visible`: yes/no; `vegetation_cover`: low/med/high
- `matches_declared_activity`: yes / no / uncertain + confidence

Two ways (pick one for 48h):
1. **Vision LLM with strict JSON schema** (Gemini / Claude / GPT vision) — fastest to build, best quality. Give it the fixed label list and force enum outputs. Low-confidence → "Needs human review" (don't let it guess).
2. **CLIP zero-shot (open_clip)** — offline, free, no API key; prompts like "a photo of a concrete check dam across a stream". Good fallback & a nice "can run on NIC servers without external API" talking point.

Recommended: use a vision LLM for the demo, mention CLIP/fine-tuned YOLO as the on-prem production path. **Do NOT try to train a custom YOLO in 48h.**

### M3 — Satellite Response Engine
For each asset point (and for each micro-watershed):
1. Define **treated zone** = buffer (e.g., 150–250 m; for ponds/check dams also a downstream sector) and **control zone** = ring outside (e.g., 300–1000 m) excluding other treated zones and water/built-up.
2. Build same-season median composites for **baseline year** (before work start) and **latest year**.
3. Compute indices:
   - **NDVI** = (NIR−Red)/(NIR+Red) → vegetation
   - **MNDWI** = (Green−SWIR1)/(Green+SWIR1) → surface water
   - **NDMI** = (NIR−SWIR1)/(NIR+SWIR1) → vegetation/soil moisture
4. **DiD** = (Treated_after − Treated_before) − (Control_after − Control_before).
5. Rainfall context from CHIRPS (seasonal totals for both years) — show it on the chart so judges see you controlled for it.
6. For ponds: water-pixel fraction post-monsoon via Sentinel-2 10 m MNDWI (+ Sentinel-1 SAR in cloudy regions); also check JRC Global Surface Water history.
7. Activity-aware expectation: plantation → NDVI↑; pond/check dam/percolation tank → water↑ + NDVI/NDMI↑ downstream; bunds/trenches → NDMI/NDVI↑ in fields.

Output: `satellite_response` sub-score 0–30 + time-series chart data.

### M4 — Watershed Characterization (thematic maps)
From DEM (SRTM 30 m / CartoDEM 30 m):
- Flow direction → flow accumulation → **drainage network** → **Strahler stream order**
- **Slope** map, elevation/relief
- **Morphometric parameters**: drainage density, stream frequency, bifurcation ratio, form factor, circularity ratio, elongation ratio → classic **watershed prioritization** (NRSC scientists love this; it's standard hydrology)

From LULC (ESA WorldCover 10 m / Dynamic World / Bhuvan LULC WMS):
- **Land use map**, and **LULC change** between baseline and latest year (Dynamic World has time series)

Thematic outputs (directly answers expectation c): land use map, drainage map, vegetation (NDVI) map, water map, **intervention map** (all photo-verified assets symbolised by type & score), **change detection map** (NDVI/MNDWI difference).

### M5 — Scoring
**Evidence Score (per asset, 0–100):**

| Component | Max | Basis |
|---|---|---|
| Geo-integrity | 30 | M1 flags (accuracy, in-boundary, timestamp, non-duplicate, EXIF) |
| Visual match | 30 | M2: predicted activity = declared, stage, confidence |
| Satellite response | 30 | M3: DiD sign & magnitude relative to activity expectation |
| Temporal consistency | 10 | Multiple photos over time show progression (planned → under construction → complete) |

Bands: **≥ 70 Verified** · **40–69 Needs review** · **< 40 Flag for field inspection**.
Make weights configurable in the UI — say "weights to be calibrated with DoLR experts". That's honest and judges like it.

**Watershed Outcome Index (per micro-watershed):** combine area-weighted NDVI DiD, surface-water extent change, cropland/fallow change, and share of assets Verified. Show as district/state choropleth.

Important framing: **the score is a triage tool, not a verdict.** It prioritises inspections; it doesn't accuse anyone. Say this proactively.

### M6 — Dashboard (the thing judges will actually see)
Screens:
1. **National/State/District view** — choropleth of Outcome Index & geotag coverage (use the real GT2 numbers here), click to drill down.
2. **Micro-watershed view** — map with boundary, drainage, LULC, NDVI layers (toggle), photo pins coloured green/amber/red by Evidence Score, **before/after swipe** slider on satellite composites.
3. **Asset drawer** (click a pin) — both photos, EXIF/geo-integrity checklist ✅❌, AI interpretation, satellite chips (before/after), NDVI/MNDWI time series treated vs control + rainfall bars, final score & reasons.
4. **Review queue** — list of "Needs review / Flag" assets sorted by score; officer can mark Confirmed / Rejected (human-in-the-loop; feedback improves the model later).
5. **Report** — one-click PDF "Watershed Report Card" (maps + indices + asset table).
6. **API docs** page (Swagger from FastAPI) — shows "Srishti integration ready".

### M7 — (Stretch) Drishti++ smart capture
A small PWA page that, at capture time, waits for GPS ≤ 10 m, checks the point is inside the selected MWS, runs a blur check, and warns if the photo looks like a duplicate. Message: *"prevent bad evidence at source instead of catching it later."* Only if time permits.

---

## 5. Data — where to get it

### 5.1 About the "dataset" in the PS
The Drive link in the PS appears to be a folder named "MoRD" — very likely it only holds these 5 problem-statement PDFs (26015 plus the 4 other DoLR PSs), **not an actual dataset**. Open it and confirm. If so, that's why teams find this PS "difficult": there's no ready data. Treat it as an advantage — most teams will give up or make a generic NDVI viewer.

Real DRISHTI photos sit behind **Data Provider / Admin logins** on Srishti; citizen access is view-only. You won't get bulk photo access in 48h. So:

> **Demo strategy (state it openly in the PPT):** "Our framework uses the DRISHTI record schema. For the prototype we used public satellite/DEM data, real field photos we captured ourselves, and simulated DRISHTI records for demonstration. In deployment it connects to SRISHTI–DRISHTI via API."

### 5.2 Government / programme sources
| Source | What you get | Link |
|---|---|---|
| WDC-PMKSY 2.0 MIS — GT2 report | State → district geotag coverage & work status (real numbers, Excel/PDF export) | https://wdcpmksy.dolr.gov.in/getAllAssetGeoData |
| WDC-PMKSY dashboards & map | Programme-level stats, Tejas Bharat map | https://wdcpmksy.dolr.gov.in/dolrDashBoard · https://wdcpmksy.dolr.gov.in/tejasBharatMap |
| SRISHTI (WDC 2.0 on Bhuvan) | See the actual portal UI, layers, citizen view | https://bhuvan-app1.nrsc.gov.in/wdc2.0/ |
| Bhuvan IWMP + manuals | Srishti–Drishti user manual (schema, activity codes) | https://bhuvan-app1.nrsc.gov.in/iwmp/ |
| WDC-PMKSY 2.0 Guidelines | Official activities, project phases, M&E requirements — cite in PPT | https://wdcpmksy.dolr.gov.in/reference/WDCPMKSY2.0_Guidelines.pdf |
| Bhuvan main portal | LULC layers via WMS, CartoDEM/LISS-III downloads (Open Data Archive, needs free login) | https://bhuvan.nrsc.gov.in |
| India-WRIS | Basin/sub-basin/watershed boundaries, hydrology layers | https://indiawris.gov.in |

**Read the WDC-PMKSY 2.0 Guidelines PDF (at least the M&E part) before building.** Quote it in the PPT.

### 5.3 Satellite / geospatial (free, fastest via Google Earth Engine)
| Data | Resolution | Earth Engine ID |
|---|---|---|
| Landsat 8 / 9 Surface Reflectance (**30 m — same class as SRISHTI's 30 m**) | 30 m | `LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2` |
| Sentinel-2 Surface Reflectance | 10 m | `COPERNICUS/S2_SR_HARMONIZED` |
| Sentinel-1 SAR (cloud-proof water) | 10 m | `COPERNICUS/S1_GRD` |
| SRTM DEM | 30 m | `USGS/SRTMGL1_003` |
| ESA WorldCover LULC | 10 m | `ESA/WorldCover/v200` |
| Dynamic World LULC (time series) | 10 m | `GOOGLE/DYNAMICWORLD/V1` |
| CHIRPS rainfall | ~5 km daily | `UCSB-CHG/CHIRPS/DAILY` |
| JRC Global Surface Water | 30 m | `JRC/GSW1_4/GlobalSurfaceWater` |
| HydroBASINS level 12 (fallback watershed boundaries) | vector | `WWF/HydroSHEDS/v1/Basins/hybas_12` |

- **Earth Engine signup:** https://code.earthengine.google.com — register for noncommercial/education use with a Google Cloud project. **Do this in hour 1**; if approval is slow, fallback to **Microsoft Planetary Computer** STAC (https://planetarycomputer.microsoft.com — reading data needs no approval) with `pystac-client` + `stackstac`/`odc-stac`.
- For the PPT: "Prototype uses Landsat 30 m (same resolution class as SRISHTI-DRISHTI) so the method transfers directly to the SRISHTI data feed."

### 5.4 Photos — no field trip fits in 48h, so the plan is AI-generated + licensed reference images, not a site visit
1. **AI-generated images (primary source)** — generate images of check dams, farm ponds, contour bunds, plantations etc. with an open-source image-generation model. Tag every one `photo_source = 'ai_generated'`, `is_synthetic = true`. This is the main photo source for both Phase 1 (EXIF mechanics) and Phase 2 (classifier test material).
2. **CC-licensed reference images (secondary, optional)** — Wikimedia Commons and similar occasionally have genuinely free-licensed photos of Indian watershed structures; usable only if the license is confirmed and noted, tagged `photo_source = 'stock_cc'`. Skip anything with an unclear license — judges will ask.
3. **Simulated DRISHTI records** — 10–30 records in a CSV in the exact Drishti schema, with coordinates generated programmatically inside the demo watershed boundary (Shapely random-point-in-polygon), not hand-picked.
4. **Deliberately planted bad records** (clearly labelled as test cases): a duplicate photo reused for two works, a point outside the boundary, a "check dam" record whose photo is actually a plantation, a GPS accuracy of 45 m. The demo *needs* these to show the flags working.
5. If a short site visit does become possible later, even for 1–2 real photos, swap them in as `photo_source = 'field'` — pure upside, never required for the demo to work.

### 5.5 Choosing the demo micro-watershed
- **Option A (strong satellite signal):** a semi-arid watershed (Rajasthan / Anantapur, AP / Marathwada, Maharashtra / Bundelkhand) — NDVI & water changes are very visible; clouds not a problem.
- **Option B (local + authentic):** a small watershed near Guwahati (Kamrup) where you can shoot real photos; or Karbi Anglong / Nagaon (historically in DoLR's Special IWMP monitoring list). Use dry-season composites + Sentinel-1 for water.
- **Best if you can manage:** B for real photos + field story, A for a strong impact chart. If time is tight, **pick one** and do it well.

Boundary: if you can't get the official MWS polygon, derive it from the DEM with `pysheds` from an outlet point, or use HydroBASINS L12. Say: "production uses official MWS polygons from SRISHTI."

---

## 6. Tech stack (optimised for 48 hours)

| Layer | Choice | Why |
|---|---|---|
| Frontend | **React + Vite + TypeScript + Tailwind** | You already ship React; fastest for the team |
| Maps | **MapLibre GL JS** (or react-leaflet + `leaflet-side-by-side` for swipe) | Open-source, vector + raster, smooth; Leaflet is simpler if the team knows it |
| Charts | Recharts | Quick time-series & bar charts |
| Backend API | **FastAPI (Python)** | All geo/ML libraries are Python; auto Swagger docs = "integration API" for free |
| DB | **PostgreSQL + PostGIS** (Supabase to skip DevOps) | Spatial queries (`ST_Contains`, buffers), PS family already suggests PostGIS |
| Satellite processing | **Google Earth Engine Python API** + `geemap` | No downloads, server-side processing, tile URLs direct to the map |
| Raster / vector | `rasterio`, `geopandas`, `shapely`, `pysheds` or `whitebox` (drainage), `rio-cogeo` | DEM analysis, exports |
| Photo pipeline | `Pillow`/`exifread` (EXIF), `imagehash` (pHash), `opencv-python` (blur) | Geo-integrity checks |
| Photo AI | Vision LLM with JSON schema (Gemini / Claude) + `open_clip` fallback | Fast, accurate; CLIP = on-prem story |
| Reports | WeasyPrint (HTML→PDF) or jsPDF on frontend | One-click report card |
| Deploy | Vercel (frontend) + Render/Railway (FastAPI) + Supabase | Free tiers, 10-min deploys |
| Production story (PPT only) | NIC MeghRaj cloud, GeoServer for OGC WMS/WFS, Srishti API integration | Government-ready narrative |

**Critical architecture decision for 48h: precompute.** Run the Earth Engine analysis for your demo watershed(s) in a script, store results (GeoJSON, COG/PNG tiles, time-series JSON) in PostGIS/static storage. The live app reads precomputed results — fast, no live GEE failures during judging. Keep one "Run analysis" button that works live on a single asset to prove it's real.

If you'd rather keep Node/Express (your comfort zone), do: Node API + Postgres/PostGIS, and a separate Python worker for GEE/photo processing. But for 48h, **one FastAPI service is simpler.**

---

## 7. Data model (Drishti-compatible)

```sql
-- micro-watersheds
CREATE TABLE mws (
  id TEXT PRIMARY KEY,              -- e.g. official MWS code
  project_id TEXT, state TEXT, district TEXT,
  geom GEOMETRY(MultiPolygon, 4326),
  baseline_year INT, latest_year INT
);

-- DRISHTI-style field records
CREATE TABLE field_record (
  id SERIAL PRIMARY KEY,
  work_code TEXT, mws_id TEXT REFERENCES mws(id),
  category TEXT,           -- AM, VM, SM, PT, NC, BN, LS, LH, OM
  activity TEXT,           -- e.g. 'Check Dam', 'Farm Pond'
  status TEXT,             -- planned / ongoing / completed
  lat DOUBLE PRECISION, lon DOUBLE PRECISION, gps_accuracy_m REAL,
  orientation REAL, captured_at TIMESTAMPTZ,
  photo1_url TEXT, photo2_url TEXT, remarks TEXT,
  observer_id TEXT, organisation TEXT,
  geom GEOMETRY(Point, 4326),
  is_synthetic BOOLEAN DEFAULT FALSE   -- be honest in the demo
);

-- analysis outputs
CREATE TABLE asset_evidence (
  record_id INT PRIMARY KEY REFERENCES field_record(id),
  geo_flags JSONB, geo_score INT,
  ai_result JSONB, visual_score INT,
  sat_result JSONB, satellite_score INT,   -- ndvi/mndwi pre-post, DiD, rainfall
  temporal_score INT, evidence_score INT,
  band TEXT,                               -- verified / review / flag
  reviewer_decision TEXT, reviewed_at TIMESTAMPTZ
);
```

---

## 8. Core code snippets

### 8.1 EXIF GPS + pHash (Python)
```python
from PIL import Image, ExifTags
import imagehash

def read_exif(path):
    img = Image.open(path)
    exif = img.getexif()
    gps = exif.get_ifd(0x8825)  # GPS IFD
    def dms_to_deg(dms, ref):
        d, m, s = [float(x) for x in dms]
        deg = d + m / 60 + s / 3600
        return -deg if ref in ("S", "W") else deg
    lat = lon = None
    if gps and 2 in gps and 4 in gps:
        lat = dms_to_deg(gps[2], gps[1])
        lon = dms_to_deg(gps[4], gps[3])
    dt = exif.get_ifd(0x8769).get(36867)  # DateTimeOriginal
    return {"lat": lat, "lon": lon, "datetime": dt,
            "phash": str(imagehash.phash(img))}

def near_duplicate(h1, h2, thresh=6):
    return imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2) <= thresh
```

### 8.2 Treated vs control NDVI/MNDWI with DiD (Earth Engine, Python)
```python
import ee
ee.Initialize(project="YOUR-GCP-PROJECT")

def prep_l89(img):
    qa = img.select("QA_PIXEL")
    clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))  # cloud, shadow
    sr = img.select(["SR_B3", "SR_B4", "SR_B5", "SR_B6"]).multiply(0.0000275).add(-0.2)
    ndvi = sr.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
    mndwi = sr.normalizedDifference(["SR_B3", "SR_B6"]).rename("MNDWI")
    return ee.Image(ndvi.addBands(mndwi).updateMask(clear)
                    .copyProperties(img, ["system:time_start"]))

landsat = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
           .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
           .map(prep_l89))

def zone_stats(geom, start, end):
    comp = landsat.filterBounds(geom).filterDate(start, end).median()
    return comp.reduceRegion(ee.Reducer.mean(), geom, 30, maxPixels=1e9).getInfo()

def asset_did(lon, lat, base=("2019-10-01", "2020-01-31"), post=("2024-10-01", "2025-01-31")):
    p = ee.Geometry.Point([lon, lat])
    treated = p.buffer(200)
    control = p.buffer(1000).difference(p.buffer(350))
    tb, ta = zone_stats(treated, *base), zone_stats(treated, *post)
    cb, ca = zone_stats(control, *base), zone_stats(control, *post)
    did = {k: (ta[k] - tb[k]) - (ca[k] - cb[k]) for k in ("NDVI", "MNDWI")}
    return {"treated_before": tb, "treated_after": ta,
            "control_before": cb, "control_after": ca, "did": did}

def seasonal_rain(geom, start, end):
    return (ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(start, end)
            .sum().reduceRegion(ee.Reducer.mean(), geom, 5000).getInfo())
```
(Use the monsoon rainfall preceding each post-monsoon window for context. In production, exclude other treated buffers and water/built-up from the control ring.)

### 8.3 Vision prompt (strict, anti-hallucination)
```
You are verifying a watershed field photo from India's WDC-PMKSY programme.
Declared activity: "{activity}" (category {category}).
Return ONLY JSON:
{"predicted_category": one of [AM,VM,SM,PT,NC,BN,LS,LH,OM,UNKNOWN],
 "predicted_activity": short label,
 "construction_stage": one of [not_started, under_construction, completed, damaged, unclear],
 "water_visible": one of [yes, no, unclear],
 "vegetation_cover": one of [low, medium, high, unclear],
 "matches_declared": one of [yes, no, uncertain],
 "confidence": 0.0-1.0,
 "evidence": "one sentence describing what in the image supports this"}
If the image is unclear, blurry, or not a field scene, use "unclear"/"uncertain" — do not guess.
```
Route `confidence < 0.6` or `uncertain` → human review queue.

---

## 9. 48-hour execution plan (team of 6)

**First confirm what the 48h is for.** The hard national deadline for SPOC nomination + idea submission is reportedly **30 Sept 2026**, and screening is on the **idea PPT (+ optional demo video)**. A working prototype strengthens you a lot, but the **PPT is what gets evaluated first** — don't let the build eat the PPT time. Also check the PS's idea counter on sih.gov.in (each PS closes after a cap of ideas) before assuming low competition.

### Roles
| # | Role | Owns |
|---|---|---|
| 1 | Lead / backend (you) | FastAPI, PostGIS schema, scoring engine, integration, deploy |
| 2 | GIS / remote sensing | GEE scripts: composites, NDVI/MNDWI, DiD, DEM → drainage/morphometry, thematic maps |
| 3 | AI / photo | EXIF + pHash + blur validator, vision classifier, review-queue logic |
| 4 | Frontend — map | MapLibre layers, swipe, pins, asset drawer |
| 5 | Frontend — dashboard/report | District drill-down, charts, review queue UI, PDF report |
| 6 | Research / data / pitch | Guidelines reading, GT2 data, AI-generated/CC reference photos, synthetic Drishti records, PPT, video |

### Timeline
| Hours | Goal |
|---|---|
| **0–2** | GEE signup, pick demo watershed, freeze schema (§7), repo + Supabase + deploy skeletons, divide work |
| **2–6** | GIS: boundary + composites + NDVI/MNDWI maps. AI: EXIF/pHash/blur working on sample photos. FE: map with boundary + basemap. #6: generate/source synthetic photos (AI-gen + CC) + build synthetic records CSV |
| **6–14** | GIS: DiD per asset + DEM drainage/stream order/slope + LULC. AI: vision classifier + JSON results. BE: ingest endpoint, scoring. FE: pins + drawer + layer toggles |
| **14–18** | 😴 Sleep in shifts (seriously — tired teams demo badly) |
| **18–28** | Integration: precompute everything for demo MWS → DB. Swipe before/after. Charts (treated vs control + rainfall). Review queue. District choropleth with real GT2 numbers |
| **28–34** | PDF report card, Swagger API page, planted bad-record scenarios verified, bug bash |
| **34–42** | PPT final, 2–3 min demo video recording, Q&A prep |
| **42–48** | Buffer. Freeze code at hour 42. Submit early |

### Must-have vs nice-to-have
- **Must:** map with MWS + thematic layers, photo pins with Evidence Score, asset drawer (photos + checks + AI + satellite chart), before/after swipe, 3–4 flagged bad-record examples, PPT.
- **Nice:** PDF report, district choropleth, review queue actions, Swagger page.
- **Stretch:** Drishti++ PWA, Sentinel-1 water, morphometric prioritization table, multilingual UI (Hindi/Assamese).
- **Skip:** auth/roles beyond a demo login, SMS/email alerts, custom model training, scraping Srishti.

---

## 10. Demo script (≈3 minutes)

1. **(20s) Problem:** "7 lakh+ watershed works are geo-tagged on SRISHTI–DRISHTI. Today these photos are only proof-of-upload. No one can manually check them, and they tell nothing about outcomes."
2. **(30s) District view:** choropleth — geotag coverage (real MIS numbers) + Outcome Index. Click into a district → micro-watershed.
3. **(40s) Thematic layers:** toggle LULC, drainage with stream order, NDVI, water. Swipe baseline vs latest.
4. **(50s) Green pin:** farm pond — photo ✅ in-boundary, ✅ accuracy 6 m, AI: "farm pond, completed, water visible", satellite: water ↑ and NDVI ↑ vs control while rainfall was similar → **Evidence 86, Verified**.
5. **(40s) Red pins:** duplicate photo reused for two works; "check dam" photo that AI reads as plantation; point 1.2 km outside MWS → **Flag for field inspection.**
6. **(20s) Report card PDF + API docs:** "plugs into SRISHTI via API; runs on open 30 m data; scales nationally."

---

## 11. PPT structure (SIH idea template style)

1. **Title** — team, PS ID 26015, PS title, theme, organisation (MoRD/DoLR).
2. **Proposed solution** — one diagram: Photo (built?) + Satellite (worked?) → Evidence Score → Dashboard. Innovation bullets: photo–satellite fusion, DiD with control & rainfall normalization, duplicate/geo-integrity checks, Drishti-native schema.
3. **Technical approach** — architecture (§4), tech stack (§6), screenshots of prototype.
4. **Feasibility & viability** — open data only, precomputation, human-in-the-loop, risks (clouds, 30 m limits, access) + mitigations.
5. **Impact & benefits** — for DoLR (triage 7 lakh+ works, evidence-based fund release), SLNA/WCDC (prioritised inspections), researchers, citizens (transparent outcomes); environmental (water, vegetation) & economic (targeted spending).
6. **Research & references** — WDC-PMKSY 2.0 Guidelines, Srishti–Drishti manual (NRSC), GT2 MIS report, Landsat/Sentinel/SRTM/CHIRPS docs, a couple of papers on watershed morphometric prioritization & NDVI-based impact assessment.

---

## 12. Judge Q&A prep

| Likely question | Your answer |
|---|---|
| "30 m can't see a check dam." | "Correct — so we don't try to. The photo verifies the structure; the satellite measures landscape response in the treated zone vs a control zone. We use 10 m Sentinel-2 where direct detection helps (ponds, plantation blocks)." |
| "How do you know the NDVI increase is due to the intervention?" | "Difference-in-differences against an untreated control ring, same season comparison, and rainfall normalization from CHIRPS. It's evidence, not proof — which is why the score triages for inspection." |
| "You don't have Drishti data." | "Our schema is Drishti-native (activity codes, accuracy, orientation, timestamp). Prototype uses AI-generated/reference photos + simulated records, all explicitly tagged; deployment connects to SRISHTI's data via API." |
| "Are these real photos?" | "No — 48 hours doesn't allow a proper field survey. These are AI-generated or CC-licensed reference images, tagged `is_synthetic` and `photo_source` in our own data model. The pipeline itself doesn't change for real DRISHTI photos; only the data source does." |
| "Cloud cover in NE / monsoon?" | "Dry-season median composites, cloud masking from QA bands, and Sentinel-1 SAR for water extent." |
| "Won't AI misclassify?" | "Strict label set, confidence gating, 'uncertain' is allowed, low-confidence goes to human review; reviewer decisions become training data." |
| "Cost and scale?" | "All data is free/open; heavy processing is server-side per watershed and cacheable; deployable on NIC MeghRaj." |
| "What's new vs Srishti?" | "Srishti stores and displays. We interpret: validate, classify, measure impact, score, and prioritise. It's an analytics layer on Srishti, not a replacement." |
| "Privacy of field staff data?" | "Observer PII is not shown in public views; role-based access; audit log of reviewer decisions." |

---

## 13. Honest risks & mitigations

| Risk | Mitigation |
|---|---|
| GEE approval delay | Planetary Computer STAC fallback; or precomputed rasters downloaded once |
| Weak NDVI signal in already-green Assam | Use semi-arid demo watershed for the impact chart; use water/NDMI and dry season in NE |
| Vision model hallucination | Enum-only JSON, confidence gate, "unclear" option, human review |
| Too many features, nothing polished | Stick to must-haves in §9; freeze at hour 42 |
| Presenting synthetic data as real | Mark `is_synthetic` and say it openly — judges respect it; getting caught faking destroys you |
| Pitching against Srishti | Always "on top of / plugs into Srishti" |

---

## 14. Starter Claude Code prompts (run them yourself, review before applying)

**Prompt 1 — Backend skeleton**
> Create a FastAPI project `sakshya-api` with PostgreSQL + PostGIS (SQLAlchemy + GeoAlchemy2). Implement tables `mws`, `field_record`, `asset_evidence` exactly as in this SQL: <paste §7>. Endpoints: `POST /records` (multipart: 2 photos + metadata in DRISHTI schema), `GET /mws/{id}` (GeoJSON boundary + stats), `GET /mws/{id}/assets` (GeoJSON points with evidence_score and band), `GET /assets/{id}` (full evidence JSON), `POST /assets/{id}/review`. Add a seed script that loads a CSV of synthetic records and a GeoJSON boundary. Don't implement scoring yet; leave a `services/scoring.py` stub. Show me the file tree and plan before writing code.

**Prompt 2 — Geo-integrity validator**
> In `services/geo_integrity.py`, implement: EXIF GPS + DateTimeOriginal extraction (Pillow), pHash via imagehash, blur score via OpenCV Laplacian variance, PostGIS in-boundary check, GPS accuracy ≤ 10 m rule, timestamp sanity against project period, near-duplicate search across all stored hashes (Hamming ≤ 6). Return `{flags: [...], geo_score: 0-30}` with a documented scoring table. Add pytest cases for: duplicate photo, outside-boundary point, missing EXIF, 45 m accuracy.

**Prompt 3 — Earth Engine precompute**
> Write `scripts/precompute_gee.py` that, for a given MWS GeoJSON and a CSV of asset points, computes Landsat 8/9 same-season median NDVI/MNDWI for a baseline and latest year, treated (200 m buffer) vs control ring (350–1000 m, excluding other buffers), difference-in-differences, CHIRPS seasonal rainfall for both years, and exports: per-asset JSON results, and map tile URLs (getMapId) for baseline NDVI, latest NDVI, and NDVI difference. Also compute from SRTM a drainage network with Strahler order and slope for the MWS and export as GeoJSON/PNG. Use the code in <paste §8.2> as the starting point.

**Prompt 4 — Map frontend**
> Create a React + Vite + TS + Tailwind app with MapLibre GL. Screens: MWS map with toggleable layers (boundary, drainage by stream order, LULC, NDVI baseline/latest/diff tiles from the API), asset pins coloured by band (verified green / review amber / flag red), a before/after swipe control, and a right-side drawer for an asset showing both photos, geo-integrity checklist, AI result, a Recharts line chart of treated vs control NDVI with rainfall bars, and the final score with reasons. Use mock JSON first, then wire to the API.

---

## 15. Note on the other 4 PDFs
The folder also contains sibling DoLR problem statements: 25017 (land acquisition delay prediction), 26016 (national land acquisition management system), 26018 (land record digitization/OCR), 26019 (research & policy innovation platform). 26015 is the only one centred on **remote sensing + geo-coded image interpretation**, which is why it's more niche. Ignore the others for this submission — don't dilute the idea by bolting on land-records features.

---

### Final checklist before submitting
- [ ] PPT explains: photo = built?, satellite = worked?, fusion = evidence
- [ ] Real MIS numbers (re-checked on submission day) on the problem slide
- [ ] Prototype screenshots (map, drawer, flags, report)
- [ ] Synthetic data clearly labelled
- [ ] "Plugs into SRISHTI–DRISHTI" stated
- [ ] 30 m limitation + DiD + rainfall + clouds addressed
- [ ] Demo video ≤ 3 min, backup recording in case live demo fails
- [ ] Submitted before deadline with buffer         