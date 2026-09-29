import { useState } from 'react'
import type { AiResult, ClassifierBenchmark } from '@/types/domain'

const MATCH_LABELS: Record<AiResult['matches_declared'], string> = {
  yes: 'Matches declared activity',
  no: 'Does not match declared activity',
  uncertain: 'Uncertain — routed to human review',
}

/**
 * FR5.3 — AI classifier result, framed as an **advisory signal a reviewer
 * weighs**, not an authoritative verdict (Reality Pass R6 hard rule #3).
 * PRD §12.2: this card answers *"is this photo evidence of the declared
 * activity"* only — never anything about whether the work is functioning
 * (that's SatelliteChips' job).
 *
 * The model-reliability line reads `accuracy_status` verbatim from
 * `GET /classifier/benchmark` (`'measured' | 'not_established'`, computed
 * server-side) — never re-judged or re-labelled client-side. Both models
 * currently report `'not_established'`; this shows that honestly rather
 * than inventing a percentage.
 */
export function AiClassifierCard({
  result,
  visualScore,
  benchmark,
}: {
  result: AiResult | null
  visualScore: number | null
  benchmark?: ClassifierBenchmark
}) {
  const [noteOpen, setNoteOpen] = useState(false)
  const modelEntry = result && benchmark ? benchmark.models.find((m) => m.model === result.model) : undefined

  return (
    <section>
      <div className="mb-0.5 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-(--text)">AI photo check — is this evidence of the declared work?</h3>
        <span className="text-xs font-medium text-(--text-muted)">
          {visualScore === null ? 'Pending' : `${visualScore}/30`}
        </span>
      </div>
      <p className="mb-1.5 text-[11px] italic text-(--text-faint)">
        Advisory signal for a human reviewer to weigh — not an authoritative verdict.
      </p>
      {result === null ? (
        <p className="text-sm text-(--text-faint)">Not yet classified.</p>
      ) : (
        <div className="space-y-1 text-sm text-(--text)">
          {result.needs_review && (
            <p className="inline-flex items-center gap-1 rounded-full bg-(--placeholder)/20 px-2 py-0.5 text-xs font-semibold text-amber-200">
              ⚠️ Needs human review
            </p>
          )}
          <p className="font-medium">{MATCH_LABELS[result.matches_declared]}</p>
          <p className="text-(--text-muted)">
            Predicted: {result.predicted_activity} ({result.predicted_category}) — stage:{' '}
            {result.construction_stage.replace(/_/g, ' ')}, confidence {Math.round(result.confidence * 100)}%
          </p>
          {result.flags.length > 0 && <p className="text-xs text-amber-300">Flags: {result.flags.join(', ')}</p>}
          <p className="text-xs text-(--text-faint)">{result.evidence}</p>
          <p className="text-[11px] text-(--text-faint)">
            {result.provider}
            {result.model ? ` / ${result.model}` : ''} · classified {new Date(result.classified_at).toLocaleString()}
          </p>

          {modelEntry && (
            <div className="mt-1.5 rounded-md border border-(--border) bg-(--surface-2) p-2">
              <button
                type="button"
                onClick={() => setNoteOpen((v) => !v)}
                className="flex w-full items-center justify-between text-left text-xs font-medium text-(--text-muted)"
              >
                <span>
                  Model reliability ({modelEntry.model}):{' '}
                  <span className={modelEntry.accuracy_status === 'measured' ? 'text-(--verified)' : 'text-amber-300'}>
                    {modelEntry.accuracy_status === 'measured' ? 'measured' : 'not established'}
                  </span>
                </span>
                <span aria-hidden="true">{noteOpen ? '−' : '+'}</span>
              </button>
              {noteOpen && <p className="mt-1 text-[11px] text-(--text-faint)">{modelEntry.note}</p>}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
