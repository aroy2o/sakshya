/**
 * Single entry point every hook imports from. Mode is picked once, here, by
 * `VITE_API_MODE` (default `'mock'`) — nothing else in the app branches on
 * mock-vs-live. Flip the env var (or set `VITE_API_MODE=live` +
 * `VITE_API_BASE_URL` in `.env`) at Sync Point 1 and every hook/component
 * starts hitting the real FastAPI app with no code change, per the plan.
 */
import { liveApi } from './endpoints'
import { mockApi } from './mockAdapter'
import type { Api } from './types'

const mode = import.meta.env.VITE_API_MODE ?? 'mock'

export const api: Api = mode === 'live' ? liveApi : mockApi

export { ApiError } from './client'
export type { Api } from './types'
