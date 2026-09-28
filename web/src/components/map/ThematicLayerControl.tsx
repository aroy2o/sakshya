import { useMapUi, type NdviVariant } from '@/state/mapUiStore'

const NDVI_OPTIONS: { value: NdviVariant | 'off'; label: string }[] = [
  { value: 'off', label: 'Off' },
  { value: 'ndvi_before', label: 'Before' },
  { value: 'ndvi_after', label: 'After' },
  { value: 'ndvi_change', label: 'Change' },
]

/** FR5.1 layer toggles + FR5.4 swipe-mode switch, all reading/writing MapUiContext. */
export function ThematicLayerControl() {
  const { independentLayers, toggleIndependentLayer, ndviVariant, setNdviVariant, swipeActive, setSwipeActive } =
    useMapUi()

  return (
    <div className="absolute left-3 top-3 z-10 w-56 rounded-lg border border-slate-200 bg-white/95 p-3 shadow-sm backdrop-blur">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Thematic layers</p>

      <div className="space-y-1.5">
        {(['drainage', 'lulc', 'water'] as const).map((key) => (
          <label key={key} className="flex items-center gap-2 text-sm capitalize text-slate-700">
            <input
              type="checkbox"
              checked={independentLayers[key]}
              onChange={() => toggleIndependentLayer(key)}
              className="h-3.5 w-3.5"
            />
            {key}
          </label>
        ))}
      </div>

      <p className="mt-3 mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">NDVI</p>
      <div className="grid grid-cols-4 gap-1">
        {NDVI_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setNdviVariant(opt.value)}
            disabled={swipeActive}
            className={`rounded px-1.5 py-1 text-xs font-medium ${
              ndviVariant === opt.value ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            } disabled:cursor-not-allowed disabled:opacity-40`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={() => setSwipeActive(!swipeActive)}
        className={`mt-3 w-full rounded px-2 py-1.5 text-xs font-semibold ${
          swipeActive ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
        }`}
      >
        {swipeActive ? 'Exit before/after swipe' : 'Before/after swipe (FR5.4)'}
      </button>
    </div>
  )
}
