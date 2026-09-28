import { useQuery } from '@tanstack/react-query'
import { api } from '@/api'

export function useMwsList() {
  return useQuery({
    queryKey: ['mws-list'],
    queryFn: () => api.getMwsList(),
  })
}
