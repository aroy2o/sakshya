export const CHOROPLETH_RAMP: [number, string][] = [
  [0, '#eff6ff'],
  [25, '#93c5fd'],
  [50, '#3b82f6'],
  [75, '#1d4ed8'],
  [100, '#1e3a8a'],
]

export function ChoroplethLegend() {
  return (
    <div className="absolute bottom-3 left-3 z-10 rounded-lg border border-(--border) bg-(--surface)/95 p-3 text-xs shadow-sm backdrop-blur">
      <p className="mb-1.5 font-semibold uppercase tracking-wide text-(--text-muted)">Geotag coverage</p>
      <div
        className="h-2.5 w-40 rounded-sm"
        style={{
          background: `linear-gradient(to right, ${CHOROPLETH_RAMP.map(([, color]) => color).join(', ')})`,
        }}
      />
      <div className="mt-0.5 flex justify-between text-(--text-muted)">
        <span>0%</span>
        <span>100%</span>
      </div>
      <p className="mt-2 text-(--text-faint)">Grey = no coverage data for this district</p>
    </div>
  )
}
