import { BEATS } from './beats'

/**
 * Left rail navigation, replacing the old top horizontal `BeatNav` strip —
 * the human referenced the Hotstar/Disney+ pattern: a fixed-width column,
 * items stacked vertically, current item picked out with the accent
 * colour. Fixed at a narrow 224px rather than a wide rail or a
 * hover-to-expand icon state — beats 2 and 3 are full-bleed maps that need
 * the horizontal space, so the tradeoff is resolved in the map's favour: a
 * width that comfortably fits "icon + label" on one line and nothing more.
 */
export function Sidebar({
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
      className="no-print flex h-full w-56 shrink-0 flex-col border-r border-(--border) bg-(--surface)"
    >
      <div className="px-4 py-4">
        <p className="text-sm font-semibold tracking-tight text-(--text)">SAKSHYA</p>
        <p className="text-[11px] text-(--text-faint)">Watershed evidence</p>
      </div>

      <ol className="flex-1 space-y-0.5 overflow-y-auto px-2">
        {BEATS.map((beat) => {
          const isActive = active === beat.id
          return (
            <li key={beat.id}>
              <button
                type="button"
                onClick={() => onSelect(beat.id)}
                aria-current={isActive ? 'step' : undefined}
                className={`flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-sm transition-colors ${
                  isActive ? 'bg-(--accent-bg) text-(--accent)' : 'text-(--text-muted) hover:bg-(--surface-2) hover:text-(--text)'
                }`}
              >
                <span
                  className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                    isActive ? 'bg-(--accent) text-(--bg)' : 'bg-(--surface-3) text-(--text-faint)'
                  }`}
                >
                  {beat.id}
                </span>
                <span className="truncate">{beat.title}</span>
              </button>
            </li>
          )
        })}
      </ol>

      <div className="border-t border-(--border) p-3">
        <button
          type="button"
          onClick={onStartTour}
          className="flex w-full items-center justify-center gap-1.5 rounded-md border border-(--accent)/50 px-3 py-2 text-xs font-semibold text-(--accent) hover:bg-(--accent-bg)"
        >
          Guided tour
        </button>
      </div>
    </nav>
  )
}
