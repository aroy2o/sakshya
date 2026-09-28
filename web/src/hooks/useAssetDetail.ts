import { useQuery } from '@tanstack/react-query'
import { api } from '@/api'

/** Powers the asset drawer (FR5.3) — PRD §9's `GET /assets/{id}`. */
export function useAssetDetail(assetId: number | undefined) {
  return useQuery({
    queryKey: ['asset-detail', assetId],
    queryFn: () => api.getAssetDetail(assetId as number),
    enabled: assetId !== undefined,
  })
}
