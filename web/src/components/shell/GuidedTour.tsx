import { useEffect, useRef } from 'react'
import { BEATS } from './beats'

/**
 * "Guided tour" — REAL_DATA_PLAN.md §7: "steps through the seven beats and
 * resets cleanly." Manual Next/Prev (no auto-advance timer) so a presenter
 * controls pacing during the 3-minute story; Esc/Skip exits and returns to
 * whichever beat the tour was on, cleanly closing the overlay without
 * leaving any tour-only state behind.
 */
export function GuidedTour({
  activeBeat,
  onGoTo,
  onExit,
}: {
  activeBeat: number
  onGoTo: (id: number) => void
  onExit: () => void
}) {
  const closeRef = useRef<HTMLButtonElement>(null)
  // BEATS is a fixed, non-empty, module-level constant (see ./beats.ts) — the
  // non-null assertion reflects that invariant, not an unchecked runtime risk.
  const beat = BEATS.find((b) => b.id === activeBeat) ?? BEATS[0]!

  useEffect(() => {
    closeRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onExit()
      if (e.key === 'ArrowRight' && activeBeat < BEATS.length) onGoTo(activeBeat + 1)
      if (e.key === 'ArrowLeft' && activeBeat > 1) onGoTo(activeBeat - 1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [activeBeat, onGoTo, onExit])

  return (
    <div
      role="dialog"
      aria-label="Guided tour"
      aria-live="polite"
      className="no-print fixed inset-x-0 bottom-4 z-50 mx-auto w-[calc(100%-2rem)] max-w-lg rounded-xl border border-(--accent)/40 bg-(--surface-2) p-4 shadow-2xl shadow-black/50"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-(--accent)">
            Beat {beat.id} of {BEATS.length} · {beat.title}
          </p>
          <p className="mt-1 text-sm text-(--text)">{beat.tourCaption}</p>
        </div>
        <button
          ref={closeRef}
          type="button"
          onClick={onExit}
          className="shrink-0 rounded p-1 text-(--text-faint) hover:bg-(--surface-3) hover:text-(--text)"
          aria-label="Exit guided tour"
        >
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden="true">
            <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
          </svg>
        </button>
      </div>

      <div className="mt-3 flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => onGoTo(activeBeat - 1)}
          disabled={activeBeat <= 1}
          className="rounded-md border border-(--border-strong) px-3 py-1.5 text-xs font-medium text-(--text-muted) hover:bg-(--surface-3) disabled:cursor-not-allowed disabled:opacity-30"
        >
          ← Prev
        </button>
        <div className="flex gap-1" aria-hidden="true">
          {BEATS.map((b) => (
            <span
              key={b.id}
              className={`h-1.5 w-1.5 rounded-full ${b.id === activeBeat ? 'bg-(--accent)' : 'bg-(--border-strong)'}`}
            />
          ))}
        </div>
        {activeBeat < BEATS.length ? (
          <button
            type="button"
            onClick={() => onGoTo(activeBeat + 1)}
            className="rounded-md bg-(--accent) px-3 py-1.5 text-xs font-semibold text-(--bg) hover:brightness-110"
          >
            Next →
          </button>
        ) : (
          <button
            type="button"
            onClick={onExit}
            className="rounded-md bg-(--accent) px-3 py-1.5 text-xs font-semibold text-(--bg) hover:brightness-110"
          >
            Finish
          </button>
        )}
      </div>
    </div>
  )
}
