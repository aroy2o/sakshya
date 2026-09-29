import type { DistrictCoverage } from '@/types/domain'

/**
 * Accompanies the map — every coverage row lands here, whether or not it
 * matched a boundary polygon (`unmatched` gets a visible note instead of
 * being silently dropped from the page, per `districtJoin.ts`'s contract).
 */
export function DistrictTable({
  rows,
  unmatchedDistricts,
}: {
  rows: DistrictCoverage[]
  unmatchedDistricts: readonly string[]
}) {
  const sorted = [...rows].sort((a, b) => b.geotag_coverage_pct - a.geotag_coverage_pct)

  return (
    <div className="mt-3">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-(--border) text-xs uppercase tracking-wide text-(--text-faint)">
            <th className="py-1 pr-2">District</th>
            <th className="py-1 pr-2">State</th>
            <th className="py-1 pr-2 text-right">Geotagged</th>
            <th className="py-1 text-right">Coverage</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr key={`${row.state}-${row.district}`} className="border-b border-(--border)">
              <td className="py-1 pr-2 text-(--text)">
                {row.district}
                {unmatchedDistricts.includes(row.district) && (
                  <span
                    className="ml-1 text-amber-300"
                    title="No matching boundary polygon found — shown here, not on the map"
                  >
                    ⚠️
                  </span>
                )}
              </td>
              <td className="py-1 pr-2 text-(--text-muted)">{row.state}</td>
              <td className="py-1 pr-2 text-right font-mono text-(--text-muted)">
                {row.geotagged_works}/{row.total_works}
              </td>
              <td className="py-1 text-right font-mono text-(--text)">{row.geotag_coverage_pct.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      {unmatchedDistricts.length > 0 && (
        <p className="mt-2 text-xs text-amber-300">
          {unmatchedDistricts.length} district{unmatchedDistricts.length === 1 ? '' : 's'} couldn&apos;t be matched
          to a boundary polygon (name mismatch) — marked ⚠️ above, still shown in this table.
        </p>
      )}
    </div>
  )
}
