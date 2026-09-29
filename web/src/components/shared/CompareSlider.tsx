/**
 * Generic before/after swipe divider. Renders `before` full-bleed
 * underneath and `after` clipped to the region right of the divider via
 * CSS `clip-path` — dragging the handle moves the divider. No extra
 * dependency: a pointer-event drag handler plus one clip-path is all a
 * swipe control needs.
 *
 * Reused by two different "before/after" UIs:
 *  - `SwipeControl.tsx` (FR5.4) wraps two synced MapLibre map instances
 *  - `SatelliteChips.tsx` (FR5.3) wraps two static precomputed images
 * Both just hand this component their `before`/`after` content.
 */
import { useCallback, useRef, type PointerEvent, type ReactNode } from 'react'

export function CompareSlider({
  before,
  after,
  position,
  onPositionChange,
  beforeLabel = 'Before',
  afterLabel = 'After',
  className,
}: {
  before: ReactNode
  after: ReactNode
  position: number // 0-100
  onPositionChange: (pos: number) => void
  beforeLabel?: string
  afterLabel?: string
  className?: string
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const draggingRef = useRef(false)

  const updateFromClientX = useCallback(
    (clientX: number) => {
      const el = containerRef.current
      if (!el) return
      const rect = el.getBoundingClientRect()
      const pct = ((clientX - rect.left) / rect.width) * 100
      onPositionChange(Math.min(100, Math.max(0, pct)))
    },
    [onPositionChange],
  )

  const handlePointerDown = (e: PointerEvent<HTMLDivElement>) => {
    draggingRef.current = true
    e.currentTarget.setPointerCapture(e.pointerId)
    updateFromClientX(e.clientX)
  }
  const handlePointerMove = (e: PointerEvent<HTMLDivElement>) => {
    if (!draggingRef.current) return
    updateFromClientX(e.clientX)
  }
  const handlePointerUp = (e: PointerEvent<HTMLDivElement>) => {
    draggingRef.current = false
    e.currentTarget.releasePointerCapture(e.pointerId)
  }

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden select-none ${className ?? ''}`}
      onPointerMove={handlePointerMove}
    >
      <div className="absolute inset-0">{before}</div>
      <div className="absolute inset-0" style={{ clipPath: `inset(0 0 0 ${position}%)` }}>
        {after}
      </div>

      <div className="pointer-events-none absolute left-2 top-2 rounded bg-black/60 px-2 py-0.5 text-xs text-white">
        {beforeLabel}
      </div>
      <div className="pointer-events-none absolute right-2 top-2 rounded bg-black/60 px-2 py-0.5 text-xs text-white">
        {afterLabel}
      </div>

      <div
        className="absolute inset-y-0 z-10 flex w-6 -translate-x-1/2 cursor-ew-resize items-center justify-center"
        style={{ left: `${position}%` }}
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        role="slider"
        aria-label="Before/after divider"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(position)}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'ArrowLeft') onPositionChange(Math.max(0, position - 2))
          if (e.key === 'ArrowRight') onPositionChange(Math.min(100, position + 2))
        }}
      >
        <div className="h-full w-0.5 bg-(--surface) shadow" />
        <div className="absolute flex h-7 w-7 items-center justify-center rounded-full border border-(--border-strong) bg-(--surface) shadow">
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 text-(--text-muted)" aria-hidden="true">
            <path d="M7 4.5 3 10l4 5.5V4.5Zm6 0v11L17 10l-4-5.5Z" />
          </svg>
        </div>
      </div>
    </div>
  )
}
