import { useQuery } from '@tanstack/react-query'
import { api } from '@/api'

export function useMws(mwsId: string | undefined) {
  return useQuery({
    queryKey: ['mws', mwsId],
    queryFn: () => api.getMws(mwsId as string),
    enabled: mwsId !== undefined,
  })
}
