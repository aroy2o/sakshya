export type AppTab = 'map' | 'coverage'

const TABS: { id: AppTab; label: string }[] = [
  { id: 'map', label: 'Watershed map' },
  { id: 'coverage', label: 'District coverage' },
]

export function TopNav({ active, onChange }: { active: AppTab; onChange: (tab: AppTab) => void }) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4">
      <div className="flex items-center gap-2">
        <span className="text-base font-bold text-slate-800">SAKSHYA</span>
        <span className="hidden text-xs text-slate-400 sm:inline">
          Watershed evidence dashboard — plugs into SRISHTI-DRISHTI, doesn&apos;t replace it
        </span>
      </div>
      <nav className="flex gap-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={`rounded px-3 py-1.5 text-sm font-medium ${
              active === tab.id ? 'bg-sky-600 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </header>
  )
}
