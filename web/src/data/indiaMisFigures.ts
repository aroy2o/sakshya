/**
 * India-wide WDC-PMKSY MIS totals for beat 1's command strip. No API
 * endpoint returns an India-wide rollup (`GET /districts/geotag-coverage`
 * only covers the 3 NE states SAKSHYA focuses on, 51 districts) — these
 * three numbers are cited verbatim from `docs/REAL_DATA_PLAN.md` §1's
 * researched, dated, sourced table (WDC-PMKSY 2.0 MIS Report GT2, "as on
 * 27-28 Sep 2026"), not fabricated and not a live fetch.
 *
 * This is the one place in the dashboard that shows a real number without
 * a live API call behind it — `CommandStrip.tsx` chips it distinctly as
 * "REAL · cited (not live-fetched)" rather than letting it read as if it
 * came from a `GET` the way every other beat's numbers do. If a future
 * endpoint exposes a live India-wide rollup, swap this constant for that
 * fetch and delete this file.
 */
export const INDIA_MIS_FIGURES = {
  projects: 1221,
  work_codes: 923594,
  geotagged: 706303,
  not_geotagged: 217291,
  as_on: 'REAL_DATA_PLAN.md §1, live figures as on 27–28 Sep 2026',
  source_url: 'https://wdcpmksy.dolr.gov.in/getAllAssetGeoData',
} as const
