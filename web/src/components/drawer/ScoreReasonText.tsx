import { scoreHeadline, scoreReasonSentences } from '@/utils/scoreReason'
import type { AssetDetail } from '@/types/domain'

/** FR5.3's "plain-language reason", built only from data the asset actually carries — see utils/scoreReason.ts. */
export function ScoreReasonText({ asset }: { asset: AssetDetail }) {
  const sentences = scoreReasonSentences(asset)

  return (
    <section className="rounded-md bg-slate-50 p-3">
      <p className="text-sm font-medium text-slate-700">{scoreHeadline(asset)}</p>
      {sentences.length > 0 && (
        <ul className="mt-1.5 list-inside list-disc space-y-1 text-xs text-slate-500">
          {sentences.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
      )}
    </section>
  )
}
