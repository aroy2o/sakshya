export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 p-6 text-sm text-(--text-muted)">
      <span
        className="h-4 w-4 animate-spin rounded-full border-2 border-(--border-strong) border-t-(--accent)"
        aria-hidden="true"
      />
      <span>{label}</span>
    </div>
  )
}
