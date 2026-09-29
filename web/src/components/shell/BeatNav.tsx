import { BEATS } from './beats'

/**
 * Keyboard-accessible beat switcher (native `<button>`s, tab order = beat
 * order, arrow-key roving handled by the browser's default button focus
 * since there's no custom widget role here). Mobile: scrolls horizontally
 * instead of wrapping, per REAL_DATA_PLAN.md §7's "mobile-responsive" brief.
 */
export function BeatNav({
  active,
  onSelect,
  onStartTour,
}: {
  active: number
  onSelect: (id: number) => void
  onStartTour: () => void
}) {
  return (
    <nav
      aria-label="Dashboard beats"
      className="flex items-center gap-1 overflow-x-auto border-b border-(--border) bg-(--surface) px-2 py-1.5 sm:px-4"
    >
      <ol className="flex shrink-0 items-center gap-1">
        {BEATS.map((beat) => (
          <li key={beat.id}>
            <button
              type="button"
              onClick={() => onSelect(beat.id)}
              aria-current={active === beat.id ? 'step' : undefined}
              className={`flex items-center gap-1.5 whitespace-nowrap rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors sm:text-sm ${
                active === beat.id
                  ? 'bg-(--accent-bg) text-(--accent)'
                  : 'text-(--text-muted) hover:bg-(--surface-2) hover:text-(--text)'
              }`}
            >
              <span
                className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                  active === beat.id ? 'bg-(--accent) text-(--bg)' : 'bg-(--surface-3) text-(--text-faint)'
                }`}
              >
                {beat.id}
              </span>
              {beat.title}
            </button>
          </li>
        ))}
      </ol>
      <button
        type="button"
        onClick={onStartTour}
        className="ml-auto shrink-0 rounded-md border border-(--accent)/50 px-3 py-1.5 text-xs font-semibold text-(--accent) hover:bg-(--accent-bg) sm:text-sm"
      >
        Guided tour
      </button>
    </nav>
  )
}
