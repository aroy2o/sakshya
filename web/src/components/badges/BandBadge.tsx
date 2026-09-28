import { bandBgColor, bandColor, bandLabel } from '@/utils/band'
import type { Band } from '@/types/domain'

export function BandBadge({ band, className }: { band: Band | null; className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${className ?? ''}`}
      style={{ backgroundColor: bandBgColor(band), color: bandColor(band) }}
    >
      <span
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: bandColor(band) }}
        aria-hidden="true"
      />
      {bandLabel(band)}
    </span>
  )
}
