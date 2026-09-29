/**
 * Reality Pass R6, hard rule #2: drive the "candidate watershed (project
 * area unconfirmed)" caveat label off `GET /mws/{id}`'s `boundary_source`
 * string — never hardcode "true right now". The moment a human confirms
 * the real MWS codes (`config/treated_mws.txt`) and backend regenerates
 * without the `pending_human_confirmation` marker, this substring check
 * naturally stops matching and the label disappears with zero UI changes.
 */
export function isBoundaryPendingConfirmation(boundarySource: string | null | undefined): boolean {
  return typeof boundarySource === 'string' && boundarySource.includes('pending_human_confirmation')
}
