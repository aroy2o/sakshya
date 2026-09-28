/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** FastAPI base URL. Only used when VITE_API_MODE=live. See .env.example. */
  readonly VITE_API_BASE_URL?: string
  /** 'mock' (default, no backend needed) | 'live' (real API, see AGENTS.md Sync Point 1). */
  readonly VITE_API_MODE?: 'mock' | 'live'
  /** Optional: pin the dashboard to one watershed id. Unset = use the first `GET /mws` result. Config, not code — see PRD §14. */
  readonly VITE_DEMO_MWS_ID?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
