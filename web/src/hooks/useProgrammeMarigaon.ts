import { useQuery } from '@tanstack/react-query'
import { api } from '@/api'

/** Beat 6 (Moderation queue) — real registry + backlog, `GET /programme/marigaon`. */
export function useProgrammeMarigaon() {
  return useQuery({
    queryKey: ['programme-marigaon'],
    queryFn: () => api.getProgrammeMarigaon(),
    staleTime: 5 * 60 * 1000,
  })
}
