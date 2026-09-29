import { useState } from 'react'
import { BEATS } from './beats'

/**
 * Left rail navigation, replacing the old top horizontal `BeatNav` strip —
 * the human referenced the Hotstar/Disney+ pattern: a fixed-width column,
 * items stacked vertically, current item picked out with the accent
 * colour. Collapsible: expanded is 224px (comfortably fits a label on one
 * line, nothing more); collapsed is a 56px icon rail using each beat's
 * first letter as a compact identifier (no icon set in this project yet,
 * and none of the 7 titles collide on their first letter: C/A/P/I/E/M/R).
 * Beats 2 and 3 are full-bleed maps, so collapsing recovers real map width
 * rather than being pure decoration.
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
  const [collapsed, setCollapsed] = useState(false)

  return (
    <nav
      aria-label="Dashboard beats"
      className={`no-print flex h-full shrink-0 flex-col border-r border-(--border) bg-(--surface) transition-[width] duration-150 ${
        collapsed ? 'w-14' : 'w-56'
      }`}
    >
      <div className={`flex items-center border-b border-(--border) ${collapsed ? 'justify-center px-2 py-3' : 'justify-between px-4 py-4'}`}>
        {!collapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-tight text-(--text)">SAKSHYA</p>
            <p className="truncate text-[11px] text-(--text-faint)">Watershed evidence</p>
          </div>
        )}
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-expanded={!collapsed}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-(--text-faint) hover:bg-(--surface-2) hover:text-(--text)"
        >
          {collapsed ? '»' : '«'}
        </button>
      </div>

      <ol className="flex-1 space-y-0.5 overflow-y-auto px-2 py-2">
        {BEATS.map((beat) => {
          const isActive = active === beat.id
          return (
            <li key={beat.id}>
              <button
                type="button"
                onClick={() => onSelect(beat.id)}
                aria-current={isActive ? 'step' : undefined}
                title={collapsed ? beat.title : undefined}
                className={`flex w-full items-center rounded-md text-left text-sm transition-colors ${
                  collapsed ? 'justify-center px-0 py-2.5' : 'gap-2.5 px-2.5 py-2'
                } ${isActive ? 'bg-(--accent-bg) text-(--accent)' : 'text-(--text-muted) hover:bg-(--surface-2) hover:text-(--text)'}`}
              >
                {collapsed ? (
                  <span className="text-sm font-semibold">{beat.title.charAt(0)}</span>
                ) : (
                  <span className="truncate">{beat.title}</span>
                )}
              </button>
            </li>
          )
        })}
      </ol>

      <div className="border-t border-(--border) p-3">
        <button
          type="button"
          onClick={onStartTour}
          title={collapsed ? 'Guided tour' : undefined}
          className="flex w-full items-center justify-center gap-1.5 rounded-md border border-(--accent)/50 px-3 py-2 text-xs font-semibold text-(--accent) hover:bg-(--accent-bg)"
        >
          {collapsed ? '▸' : 'Guided tour'}
        </button>
      </div>
    </nav>
  )
}
