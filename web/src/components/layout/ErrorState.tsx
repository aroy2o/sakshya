/**
 * The only way a failed fetch is allowed to render — CLAUDE.md: "never
 * fabricate a number." No component may swallow an error and show a zeroed
 * or guessed value instead of this.
 */
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      <p className="font-medium">Couldn&apos;t load this data.</p>
      <p className="text-red-600">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-1 rounded border border-red-300 bg-white px-3 py-1 text-xs font-medium text-red-700 hover:bg-red-100"
        >
          Retry
        </button>
      )}
    </div>
  )
}
