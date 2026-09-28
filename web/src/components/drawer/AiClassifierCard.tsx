import type { AiResult } from '@/types/domain'

const MATCH_LABELS: Record<AiResult['matches_declared'], string> = {
  yes: 'Matches declared activity',
  no: 'Does not match declared activity',
  uncertain: 'Uncertain — routed to human review',
}

/**
 * FR5.3 — AI classifier result. PRD §12.2: this card answers *"is this
 * photo evidence of the declared activity"* only. It must never claim
 * anything about whether the work is functioning — that's SatelliteChips'
 * job, kept in a separate card on purpose.
 */
export function AiClassifierCard({ result, visualScore }: { result: AiResult | null; visualScore: number | null }) {
  return (
    <section>
      <div className="mb-1.5 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">AI photo check — is this evidence of the declared work?</h3>
        <span className="text-xs font-medium text-slate-500">
          {visualScore === null ? 'Pending' : `${visualScore}/30`}
        </span>
      </div>
      {result === null ? (
        <p className="text-sm text-slate-400">Not yet classified.</p>
      ) : (
        <div className="space-y-1 text-sm text-slate-700">
          <p className="font-medium">{MATCH_LABELS[result.matches_declared]}</p>
          <p className="text-slate-500">
            Predicted: {result.predicted_activity} ({result.predicted_category}) — stage:{' '}
            {result.construction_stage.replace(/_/g, ' ')}, confidence {Math.round(result.confidence * 100)}%
          </p>
          <p className="text-xs text-slate-400">{result.evidence}</p>
        </div>
      )}
    </section>
  )
}
