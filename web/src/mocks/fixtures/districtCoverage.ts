/**
 * Mock for `GET /districts/geotag-coverage`. Reality Pass R3/R4 (2026-09-28)
 * made this endpoint real — all 51 rows below are a verbatim capture of a
 * live response (WDC-PMKSY 2.0 MIS Report GT2: 31 Assam + 12 Meghalaya + 8
 * Tripura districts). Kept as the full set (not trimmed) so beat 1's NE
 * comparison bars aggregate to the same per-state totals in mock mode as
 * live mode — both are computed the same way, by summing whatever
 * `getDistrictCoverage()` returns (see `utils/neStateTotals.ts`), never a
 * separately-hardcoded constant that could drift from the per-district rows.
 *
 * District spelling is `'Morigaon'` (the real MIS/Census spelling), which
 * does NOT match `public/data/india-districts.geojson`'s `'Marigaon'` —
 * same real spelling mismatch as `mocks/fixtures/mws.ts` documents; this
 * row correctly lands in `DistrictTable`'s unmatched list in mock mode too,
 * same as it does live.
 */
import type { DistrictCoverage } from '@/types/domain'

const SOURCE_REPORT = 'WDC-PMKSY 2.0 MIS, Report GT2 (Work Code Status with Geotagging Details)'
const AS_OF = '2026-09-28'

export const districtCoverage: DistrictCoverage[] = [
  { district: 'Baksa', state: 'Assam', total_works: 599, geotagged_works: 596, geotag_coverage_pct: 99.5, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Barpeta', state: 'Assam', total_works: 681, geotagged_works: 662, geotag_coverage_pct: 97.2, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Bongaigaon', state: 'Assam', total_works: 523, geotagged_works: 519, geotag_coverage_pct: 99.2, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Cachar', state: 'Assam', total_works: 445, geotagged_works: 365, geotag_coverage_pct: 82.0, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Charaideo', state: 'Assam', total_works: 46, geotagged_works: 27, geotag_coverage_pct: 58.7, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Chirang', state: 'Assam', total_works: 609, geotagged_works: 604, geotag_coverage_pct: 99.2, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Darrang', state: 'Assam', total_works: 688, geotagged_works: 686, geotag_coverage_pct: 99.7, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Dhemaji', state: 'Assam', total_works: 469, geotagged_works: 462, geotag_coverage_pct: 98.5, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Dhubri', state: 'Assam', total_works: 628, geotagged_works: 633, geotag_coverage_pct: 100.0, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Dibrugarh', state: 'Assam', total_works: 442, geotagged_works: 442, geotag_coverage_pct: 100.0, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Dima Hasao', state: 'Assam', total_works: 468, geotagged_works: 391, geotag_coverage_pct: 83.5, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Goalpara', state: 'Assam', total_works: 541, geotagged_works: 495, geotag_coverage_pct: 91.5, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Golaghat', state: 'Assam', total_works: 592, geotagged_works: 595, geotag_coverage_pct: 100.0, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Hailakandi', state: 'Assam', total_works: 552, geotagged_works: 431, geotag_coverage_pct: 78.1, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Hojai', state: 'Assam', total_works: 307, geotagged_works: 297, geotag_coverage_pct: 96.7, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Jorhat', state: 'Assam', total_works: 647, geotagged_works: 564, geotag_coverage_pct: 87.2, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Kamrup', state: 'Assam', total_works: 458, geotagged_works: 414, geotag_coverage_pct: 90.4, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Kamrup Metro', state: 'Assam', total_works: 59, geotagged_works: 60, geotag_coverage_pct: 100.0, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Karbi Anglong', state: 'Assam', total_works: 1056, geotagged_works: 1111, geotag_coverage_pct: 100.0, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Kokrajhar', state: 'Assam', total_works: 749, geotagged_works: 729, geotag_coverage_pct: 97.3, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Lakhimpur', state: 'Assam', total_works: 622, geotagged_works: 546, geotag_coverage_pct: 87.8, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Majuli', state: 'Assam', total_works: 404, geotagged_works: 368, geotag_coverage_pct: 91.1, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Morigaon', state: 'Assam', total_works: 309, geotagged_works: 267, geotag_coverage_pct: 86.4, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Nagaon', state: 'Assam', total_works: 364, geotagged_works: 277, geotag_coverage_pct: 76.1, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Nalbari', state: 'Assam', total_works: 723, geotagged_works: 694, geotag_coverage_pct: 96.0, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Sivasagar', state: 'Assam', total_works: 351, geotagged_works: 272, geotag_coverage_pct: 77.5, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Sonitpur', state: 'Assam', total_works: 234, geotagged_works: 189, geotag_coverage_pct: 80.8, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Tamulpur', state: 'Assam', total_works: 47, geotagged_works: 44, geotag_coverage_pct: 93.6, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Tinsukia', state: 'Assam', total_works: 441, geotagged_works: 440, geotag_coverage_pct: 99.8, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Udalguri', state: 'Assam', total_works: 500, geotagged_works: 478, geotag_coverage_pct: 95.6, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'West Karbi Anglong', state: 'Assam', total_works: 624, geotagged_works: 316, geotag_coverage_pct: 50.6, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Eastern West Khasi Hills', state: 'Meghalaya', total_works: 636, geotagged_works: 251, geotag_coverage_pct: 39.5, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'East Garo Hills', state: 'Meghalaya', total_works: 573, geotagged_works: 191, geotag_coverage_pct: 33.3, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'East Jaintia Hills', state: 'Meghalaya', total_works: 1225, geotagged_works: 443, geotag_coverage_pct: 36.2, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'East Khasi Hills', state: 'Meghalaya', total_works: 971, geotagged_works: 171, geotag_coverage_pct: 17.6, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'North Garo Hills', state: 'Meghalaya', total_works: 827, geotagged_works: 323, geotag_coverage_pct: 39.1, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Ri Bhoi', state: 'Meghalaya', total_works: 1687, geotagged_works: 606, geotag_coverage_pct: 35.9, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'South Garo Hills', state: 'Meghalaya', total_works: 469, geotagged_works: 123, geotag_coverage_pct: 26.2, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'South West Garo Hills', state: 'Meghalaya', total_works: 758, geotagged_works: 326, geotag_coverage_pct: 43.0, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'South West Khasi Hills', state: 'Meghalaya', total_works: 2201, geotagged_works: 1000, geotag_coverage_pct: 45.4, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'West Garo Hills', state: 'Meghalaya', total_works: 792, geotagged_works: 212, geotag_coverage_pct: 26.8, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'West Jaintia Hills', state: 'Meghalaya', total_works: 2673, geotagged_works: 443, geotag_coverage_pct: 16.6, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'West Khasi Hills', state: 'Meghalaya', total_works: 648, geotagged_works: 210, geotag_coverage_pct: 32.4, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Dhalai', state: 'Tripura', total_works: 3262, geotagged_works: 485, geotag_coverage_pct: 14.9, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Gomati', state: 'Tripura', total_works: 3011, geotagged_works: 509, geotag_coverage_pct: 16.9, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Khowai', state: 'Tripura', total_works: 2490, geotagged_works: 583, geotag_coverage_pct: 23.4, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'North Tripura', state: 'Tripura', total_works: 1053, geotagged_works: 81, geotag_coverage_pct: 7.7, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Sepahijala', state: 'Tripura', total_works: 1409, geotagged_works: 421, geotag_coverage_pct: 29.9, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'South Tripura', state: 'Tripura', total_works: 1965, geotagged_works: 428, geotag_coverage_pct: 21.8, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'Unakoti', state: 'Tripura', total_works: 756, geotagged_works: 90, geotag_coverage_pct: 11.9, source_report: SOURCE_REPORT, as_of: AS_OF },
  { district: 'West Tripura', state: 'Tripura', total_works: 1702, geotagged_works: 197, geotag_coverage_pct: 11.6, source_report: SOURCE_REPORT, as_of: AS_OF },
]
