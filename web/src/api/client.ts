/**
 * Thin fetch wrapper for live mode. Base URL comes from
 * `VITE_API_BASE_URL` (see `.env.example`) — nothing here ever hardcodes a
 * host, per CLAUDE.md's "watershed choice is config, not code" spirit
 * applied to the API location too.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function apiGet(path: string): Promise<unknown> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) {
    throw new ApiError(res.status, `GET ${path} failed: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<unknown>
}

export async function apiPost(path: string, body?: unknown): Promise<unknown> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    throw new ApiError(res.status, `POST ${path} failed: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<unknown>
}
