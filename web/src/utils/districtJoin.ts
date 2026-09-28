/**
 * Joins `GET /districts/geotag-coverage` rows (numeric MIS data, no
 * geometry — see PRD §9) onto the bundled district boundary polygons in
 * `src/data/india-districts.geojson` (source: Datameet `maps` repo, Census
 * 2011 district boundaries, CC-BY 2.5 India — see `src/data/README.md`).
 *
 * The join key is the district name; PRD §9's endpoint doesn't document a
 * shared numeric code, so names have to be normalised (case, whitespace,
 * common suffixes) to match reasonably well. Any coverage row that still
 * doesn't find a polygon is returned separately, never silently dropped —
 * `DistrictTable.tsx` renders those rows in table form so the data isn't
 * lost just because the map can't place it.
 */
import type { Feature, FeatureCollection, MultiPolygon, Polygon } from 'geojson'
import type { DistrictCoverage } from '@/types/domain'

export interface DistrictBoundaryProperties {
  DISTRICT: string
  ST_NM: string
  ST_CEN_CD: number
  DT_CEN_CD: number
  censuscode: number
}

export type DistrictBoundaryFeature = Feature<Polygon | MultiPolygon, DistrictBoundaryProperties>
export type DistrictBoundaryCollection = FeatureCollection<Polygon | MultiPolygon, DistrictBoundaryProperties>

/** Normalizes a district/state name for fuzzy-ish exact matching. */
export function normalizeDistrictName(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/\s+district$/, '')
    .replace(/[.\-']/g, '')
    .replace(/\s+/g, ' ')
}

export interface JoinedDistrict {
  coverage: DistrictCoverage
  feature: DistrictBoundaryFeature
}

export interface DistrictJoinResult {
  joined: JoinedDistrict[]
  /** Coverage rows that found no matching boundary polygon — never dropped silently. */
  unmatched: DistrictCoverage[]
}

export function joinDistrictCoverage(
  coverage: readonly DistrictCoverage[],
  boundaries: DistrictBoundaryCollection,
): DistrictJoinResult {
  const byName = new Map<string, DistrictBoundaryFeature>()
  for (const feature of boundaries.features) {
    const key = normalizeDistrictName(feature.properties.DISTRICT)
    byName.set(key, feature)
  }

  const joined: JoinedDistrict[] = []
  const unmatched: DistrictCoverage[] = []

  for (const row of coverage) {
    const feature = byName.get(normalizeDistrictName(row.district))
    if (feature) {
      joined.push({ coverage: row, feature })
    } else {
      unmatched.push(row)
    }
  }

  return { joined, unmatched }
}
