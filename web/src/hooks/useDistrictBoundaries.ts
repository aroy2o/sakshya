import { useQuery } from '@tanstack/react-query'
import type { DistrictBoundaryCollection } from '@/utils/districtJoin'

/**
 * Fetches the bundled district boundary polygons at runtime from
 * `/public/data/india-districts.geojson` (Datameet, CC-BY 2.5 India — see
 * `public/data/README.md` for source/license/conversion). Not part of
 * `src/api` — this is a static frontend asset, not something the backend
 * serves; PRD §9's `/districts/geotag-coverage` only returns the numeric
 * MIS table, no geometry.
 */
export function useDistrictBoundaries() {
  return useQuery({
    queryKey: ['district-boundaries'],
    queryFn: async (): Promise<DistrictBoundaryCollection> => {
      const res = await fetch('/data/india-districts.geojson')
      if (!res.ok) {
        throw new Error(`Failed to load district boundaries: ${res.status} ${res.statusText}`)
      }
      return res.json() as Promise<DistrictBoundaryCollection>
    },
    staleTime: Infinity, // static file, never changes within a session
  })
}
