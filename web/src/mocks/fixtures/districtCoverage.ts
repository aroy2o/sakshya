/**
 * Mock for `GET /districts/geotag-coverage`. PRD §9 says this endpoint
 * serves "real MIS numbers, entered manually or scraped once" — these
 * figures are NOT that; they are placeholder values so the choropleth can
 * be built and its district-name join exercised before backend-engineer
 * loads the actual WDC-PMKSY MIS table. District names below are exact
 * matches against `src/data/india-districts.geojson`'s `DISTRICT` field
 * (confirmed for Assam) so the mock also proves out `districtJoin.ts`.
 * MUST be replaced with the real endpoint before this is shown as fact.
 */
import type { DistrictCoverage } from '@/types/domain'

export const districtCoverage: DistrictCoverage[] = [
  { district: 'Marigaon', state: 'Assam', total_works: 1240, geotagged_works: 980, geotag_coverage_pct: 79.0 },
  { district: 'Nagaon', state: 'Assam', total_works: 2100, geotagged_works: 1350, geotag_coverage_pct: 64.3 },
  { district: 'Kamrup', state: 'Assam', total_works: 1580, geotagged_works: 1510, geotag_coverage_pct: 95.6 },
  { district: 'Nalbari', state: 'Assam', total_works: 860, geotagged_works: 410, geotag_coverage_pct: 47.7 },
  { district: 'Darrang', state: 'Assam', total_works: 990, geotagged_works: 210, geotag_coverage_pct: 21.2 },
]
