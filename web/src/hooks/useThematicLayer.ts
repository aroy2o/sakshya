import { useQuery } from '@tanstack/react-query'
import { api } from '@/api'
import type { ThematicLayer } from '@/types/domain'

/**
 * One precomputed thematic layer (FR5.1) — PRD §9's
 * `GET /mws/{id}/thematic/{layer}`. Only fetched when the layer is actually
 * toggled on, never all six at once.
 */
export function useThematicLayer(mwsId: string | undefined, layer: ThematicLayer | null) {
  return useQuery({
    queryKey: ['thematic-layer', mwsId, layer],
    queryFn: () => api.getThematicLayer(mwsId as string, layer as ThematicLayer),
    enabled: mwsId !== undefined && layer !== null,
  })
}
