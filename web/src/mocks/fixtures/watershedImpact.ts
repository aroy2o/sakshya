/**
 * Mock for `GET /mws/{id}/watershed-impact` (beat 4's data source). Values
 * mirror a real captured live response (2026-09-28) — `control_polygons`
 * trimmed to 4 of the real ~53 for mock-payload size; the chart only plots
 * `control_mean`, never individual polygons, so this doesn't change what
 * renders. `placeholder: true` throughout matches the real backend's
 * current state (no GEE credentials yet) — the bootstrap DiD code itself
 * is real, only the NDVI/MNDWI/rainfall numbers underneath it are not.
 */
import type { WatershedImpact } from '@/types/domain'

export const watershedImpact: WatershedImpact = {
  mws_id: '4120883730',
  summary: {
    mws_id: '4120883730',
    generated_at: '2026-09-28T10:48:55.794963+00:00',
    placeholder: true,
    source: 'synthetic_no_gee_credentials',
    method_params: {
      project_start_year: 2021,
      n_bootstrap: 2000,
      ci: 0.95,
      bootstrap_unit: 'control polygons (resampled with replacement), per REAL_DATA_PLAN.md §4.2',
      n_control_polygons: 53,
    },
    NDVI: {
      effect: 0.028032452830188716,
      ci_low: 0.025212452830188734,
      ci_high: 0.03086566037735855,
      n_bootstrap: 2000,
      ci: 0.95,
      n_control_polygons: 53,
      pre_mean_gap: 0.03776075471698113,
      post_mean_gap: 0.06579320754716984,
      pre_years: [2016, 2017, 2018, 2019, 2020],
      post_years: [2021, 2022, 2023, 2024, 2025],
    },
    MNDWI: {
      effect: 0.004063018867924527,
      ci_low: 0.0026550943396226405,
      ci_high: 0.005482264150943394,
      n_bootstrap: 2000,
      ci: 0.95,
      n_control_polygons: 53,
      pre_mean_gap: -0.012128679245283018,
      post_mean_gap: -0.00806566037735849,
      pre_years: [2016, 2017, 2018, 2019, 2020],
      post_years: [2021, 2022, 2023, 2024, 2025],
    },
    caveats: [
      "Watershed-level DiD only — no asset coordinates used (REAL_DATA_PLAN.md §4.1's explicit design goal, sidesteps public work-code pages carrying no coordinates).",
      'Marigaon is Brahmaputra floodplain — floods/erosion/sandbar shifts can swamp water signals (REAL_DATA_PLAN.md §4.3). Water metrics (MNDWI) are secondary to NDVI here.',
      'Control matching used crop-share + slope only — NDVI matching pending live GEE.',
      'placeholder=true: every NDVI/MNDWI value above is synthetic (no GEE credentials this run) — do not present as a real effect size.',
    ],
  },
  timeseries: {
    mws_id: '4120883730',
    generated_at: '2026-09-28T10:48:53.217060+00:00',
    placeholder: true,
    source: 'synthetic_no_gee_credentials',
    method: {
      season_window: 'Nov 1 (year) -> Feb 28/29 (year+1), dry season, labelled by the November it starts in',
      years: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
      project_start_year: 2021,
      rainfall_window: 'Jun 1 -> Sep 30, same calendar year',
      n_control_polygons: 53,
      control_selection:
        'REAL_DATA_PLAN.md §4.1 — crop share ±15%, slope ±3deg (see candidate_ranking.py); NDVI ±10% matching NOT applied (pending_gee)',
    },
    treated: {
      polygon_source: 'data/real/treated_boundary.geojson (R1 automated pick, pending_human_confirmation)',
      NDVI: {
        '2016': 0.5518,
        '2017': 0.5353,
        '2018': 0.527,
        '2019': 0.5629,
        '2020': 0.512,
        '2021': 0.5238,
        '2022': 0.5561,
        '2023': 0.5815,
        '2024': 0.5695,
        '2025': 0.5986,
      },
      MNDWI: {
        '2016': -0.0565,
        '2017': -0.0648,
        '2018': -0.0689,
        '2019': -0.051,
        '2020': -0.0764,
        '2021': -0.0705,
        '2022': -0.0593,
        '2023': -0.0516,
        '2024': -0.0626,
        '2025': -0.0531,
      },
    },
    control_mean: {
      NDVI: {
        '2016': 0.5030811320754717,
        '2017': 0.5006169811320754,
        '2018': 0.49684150943396227,
        '2019': 0.4983867924528302,
        '2020': 0.5012698113207547,
        '2021': 0.5004830188679246,
        '2022': 0.5036320754716981,
        '2023': 0.5020792452830188,
        '2024': 0.4972924528301887,
        '2025': 0.49704716981132074,
      },
      MNDWI: {
        '2016': -0.049869811320754714,
        '2017': -0.0511,
        '2018': -0.05299056603773585,
        '2019': -0.05222264150943396,
        '2020': -0.05077358490566038,
        '2021': -0.05116603773584906,
        '2022': -0.04958867924528302,
        '2023': -0.050371698113207554,
        '2024': -0.0527622641509434,
        '2025': -0.05288301886792453,
      },
    },
    control_polygons: {
      'g_mws.141183': {
        mws_code: '3B1C8b7',
        district: 'Kamrup Metro',
        NDVI: { '2016': 0.4861, '2020': 0.49, '2025': 0.4797 },
        MNDWI: { '2016': -0.0567, '2020': -0.0547, '2025': -0.0599 },
      },
      'g_mws.139271': {
        mws_code: '3A2D1b4',
        district: 'Darrang',
        NDVI: { '2016': 0.5052, '2020': 0.5316, '2025': 0.5319 },
        MNDWI: { '2016': -0.0915, '2020': -0.0783, '2025': -0.0781 },
      },
      'g_mws.140878': {
        mws_code: '3B2A6a2',
        district: 'Nagaon',
        NDVI: { '2016': 0.5644, '2020': 0.5618, '2025': 0.5377 },
        MNDWI: { '2016': -0.0045, '2020': -0.0058, '2025': -0.0179 },
      },
      'g_mws.135308': {
        mws_code: '3A2D7n4',
        district: 'Sonitpur',
        NDVI: { '2016': 0.4986, '2020': 0.5087, '2025': 0.5408 },
        MNDWI: { '2016': -0.0625, '2020': -0.0575, '2025': -0.0414 },
      },
    },
    rainfall_mm_jun_sep: {
      '2016': 770.1,
      '2017': 637.8,
      '2018': 838.6,
      '2019': 1224.3,
      '2020': 855.5,
      '2021': 603.9,
      '2022': 1235.7,
      '2023': 1034.1,
      '2024': 996.4,
      '2025': 651.5,
    },
  },
}
