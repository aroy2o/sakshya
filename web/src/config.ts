/**
 * App-level config that must never be hardcoded into components, per
 * CLAUDE.md: "Watershed choice is config, not code." If `VITE_DEMO_MWS_ID`
 * isn't set, `App.tsx` falls back to the first watershed `GET /mws`
 * returns — either way, no component branches on a specific MWS id.
 */
export const CONFIGURED_MWS_ID: string | undefined = import.meta.env.VITE_DEMO_MWS_ID
