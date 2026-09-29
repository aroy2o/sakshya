import { useQuery } from '@tanstack/react-query'
import { api } from '@/api'

/** Beat 5 (Evidence drawer) — model-reliability note, `GET /classifier/benchmark`. */
export function useClassifierBenchmark() {
  return useQuery({
    queryKey: ['classifier-benchmark'],
    queryFn: () => api.getClassifierBenchmark(),
    staleTime: 5 * 60 * 1000,
  })
}
