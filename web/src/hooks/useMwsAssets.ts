import { useQuery } from '@tanstack/react-query'
import { api } from '@/api'

/** Powers the map pins — PRD §9's `GET /mws/{id}/assets`. */
export function useMwsAssets(mwsId: string | undefined) {
  return useQuery({
    queryKey: ['mws-assets', mwsId],
    queryFn: () => api.getMwsAssets(mwsId as string),
    enabled: mwsId !== undefined,
  })
}
