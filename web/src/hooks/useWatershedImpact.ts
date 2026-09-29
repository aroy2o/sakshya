import { useQuery } from '@tanstack/react-query'
import { api } from '@/api'

/** Beat 4 (Impact curve) — `GET /mws/{id}/watershed-impact`. */
export function useWatershedImpact(mwsId: string | undefined) {
  return useQuery({
    queryKey: ['watershed-impact', mwsId],
    queryFn: () => api.getWatershedImpact(mwsId as string),
    enabled: mwsId !== undefined,
  })
}
