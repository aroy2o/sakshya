import type { GeoFlag } from '@/types/domain'

const RULE_LABELS: Record<GeoFlag['rule'], string> = {
  gps_accuracy: 'GPS accuracy (≤10 m standard)',
  inside_boundary: 'Inside watershed boundary',
  exif_consistency: 'EXIF GPS + timestamp consistent',
  duplicate_photo: 'Not a near-duplicate photo',
  timestamp_sane: 'Timestamp within project window',
}

/** FR5.3 — geo-integrity checklist, one row per PRD §12.1 rule, read directly from `geo_flags`. */
export function GeoIntegrityChecklist({ flags, geoScore }: { flags: GeoFlag[] | null; geoScore: number | null }) {
  return (
    <section>
      <div className="mb-1.5 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-(--text)">Geo-integrity checklist</h3>
        <span className="text-xs font-medium text-(--text-muted)">
          {geoScore === null ? 'Pending' : `${geoScore}/30`}
        </span>
      </div>
      {flags === null ? (
        <p className="text-sm text-(--text-faint)">Not yet checked.</p>
      ) : (
        <ul className="space-y-1">
          {flags.map((flag) => (
            <li key={flag.rule} className="flex items-start gap-2 text-sm">
              <span aria-hidden="true">{flag.passed ? '✅' : '❌'}</span>
              <span className="flex-1">
                <span className="text-(--text)">{RULE_LABELS[flag.rule]}</span>{' '}
                <span className="text-(--text-faint)">
                  ({flag.points}/{flag.max})
                </span>
                <br />
                <span className="text-xs text-(--text-faint)">{flag.detail}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
