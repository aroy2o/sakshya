import { useQuery } from '@tanstack/react-query'
import { api } from '@/api'

/** Powers the district choropleth (FR5.5) — PRD §9's `GET /districts/geotag-coverage`. */
export function useDistrictCoverage() {
  return useQuery({
    queryKey: ['district-coverage'],
    queryFn: () => api.getDistrictCoverage(),
  })
}
