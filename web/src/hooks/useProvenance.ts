import { useQuery } from '@tanstack/react-query'
import { api } from '@/api'

/** Beat 7 (provenance panel / Methods & limits drawer) — `GET /provenance`. */
export function useProvenance() {
  return useQuery({
    queryKey: ['provenance'],
    queryFn: () => api.getProvenance(),
    staleTime: 5 * 60 * 1000,
  })
}
