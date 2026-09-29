/**
 * CLAUDE.md non-negotiable: "`is_synthetic` is never optional... the
 * frontend (Phase 5+) must badge it visibly." This is the one component
 * that renders that badge — every place a synthetic asset's photo or
 * record appears imports this instead of rolling its own badge markup, so
 * the visual treatment can never drift out of sync across the app.
 *
 * Also surfaces `photo_source` per CLAUDE.md: "Whenever is_synthetic =
 * true, also set photo_source... so the team — and the judges — always
 * know exactly how a given photo was produced."
 */
import type { PhotoSource } from '@/types/domain'

const SOURCE_LABELS: Record<PhotoSource, string> = {
  field: 'Field photo',
  ai_generated: 'AI-generated',
  stock_cc: 'Stock / CC-licensed',
  unknown: 'Source unknown',
}

export function SyntheticBadge({
  isSynthetic,
  photoSource,
  className,
}: {
  isSynthetic: boolean
  photoSource: PhotoSource | null
  className?: string
}) {
  if (!isSynthetic) return null

  const sourceLabel = photoSource ? SOURCE_LABELS[photoSource] : 'source unrecorded'

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border border-(--placeholder)/60 bg-(--placeholder)/20 px-2 py-0.5 text-xs font-semibold text-amber-200 ${className ?? ''}`}
      title="This is synthetic/demo data, not a real field submission."
    >
      <svg
        viewBox="0 0 20 20"
        fill="currentColor"
        className="h-3.5 w-3.5"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495ZM10 6a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 6Zm0 8a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"
          clipRule="evenodd"
        />
      </svg>
      SYNTHETIC — {sourceLabel}
    </span>
  )
}
