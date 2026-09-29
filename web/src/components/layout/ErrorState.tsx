/**
 * The only way a failed fetch is allowed to render — CLAUDE.md: "never
 * fabricate a number." No component may swallow an error and show a zeroed
 * or guessed value instead of this.
 */
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-md border border-[var(--flag)]/40 bg-[var(--flag)]/10 p-4 text-sm text-red-300">
      <p className="font-medium text-red-200">Couldn&apos;t load this data.</p>
      <p className="text-red-300">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-1 rounded border border-[var(--flag)]/50 bg-[var(--surface)] px-3 py-1 text-xs font-medium text-red-200 hover:bg-[var(--flag)]/20"
        >
          Retry
        </button>
      )}
    </div>
  )
}
