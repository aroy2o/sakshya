# CLAUDE.md

Operating instructions for Claude Code in this repo. **Read `/docs/PRD.md` before writing any code** — it's the spec of record for schema, API contract, phase scope, and the scoring formula. This file is *how* to work, not *what* to build; when in doubt, PRD.md wins.

## Project

**SAKSHYA** — Smart India Hackathon 2026, Problem Statement 26015 (DoLR / Ministry of Rural Development). An analytics layer on SRISHTI–DRISHTI: fuses geo-tagged field photos with 30 m satellite evidence to score whether watershed works were built and whether they're working. Full context: `/docs/PLAYBOOK.md`, full spec: `/docs/PRD.md`.

## We build phase by phase — this is not optional

Each phase in PRD.md §10 is a bounded, reviewable unit of work. **Only implement the current phase's listed FRs in a session, even if a later phase's work seems obvious or convenient to bundle in.** If something outside the current phase's scope looks necessary to do the current phase properly, stop and say so instead of just doing it — the human decides whether to expand scope.

At the start of every session: state which phase you're working on and which FR IDs you're implementing, before writing code. At the end: propose an update to the checklist below (don't edit it yourself unless asked to).

### Phase status
- [ ] Phase 1 — Foundation (schema, ingestion API, geo-integrity validator)
- [ ] Phase 2 — AI Image Interpreter
- [ ] Phase 3 — Satellite Intelligence (GEE precompute, DiD, watershed characterization)
- [ ] Phase 4 — Evidence Scoring Engine
- [ ] Phase 5 — Map Dashboard (frontend)
- [ ] Phase 6 — Reports & Review Queue
- [ ] Phase 7 — Deploy & Demo Prep

## Tech stack (locked — don't swap without asking first)

- **Backend:** FastAPI (Python 3.11+), SQLAlchemy + GeoAlchemy2, Pydantic models for every request/response
- **DB:** PostgreSQL + PostGIS (Supabase)
- **Satellite processing:** Google Earth Engine Python API + `geemap`, run **offline** via `scripts/`, results written to Postgres/static files. The live API and frontend must never make a live GEE call — see Non-negotiables below.
- **Frontend:** React + Vite + TypeScript + Tailwind, MapLibre GL JS, Recharts
- **Photo processing:** Pillow/exifread (EXIF), `imagehash` (pHash), `opencv-python` (blur check)
- **Vision AI:** provider TBD in Phase 2 — strict enum-only JSON schema output, low confidence routes to human review, never lets the model guess
- **Reports:** WeasyPrint (HTML→PDF) or frontend jsPDF
- **Deploy:** Vercel (frontend) + Render/Railway (API) + Supabase (DB)

## Repo structure (propose on first session, then keep stable)

```
/api        FastAPI app — routers, services, models, migrations, tests
/web        React + Vite frontend
/scripts    Offline GEE precompute scripts, seed data loaders
/docs       PRD.md, CLAUDE.md, PLAYBOOK.md, reference material
```

## Tooling

- **Graphify** (already installed) — once the repo scaffold exists (end of Phase 1), run `/graphify` to map the codebase into a queryable knowledge graph. Prefer querying it over reading many files to understand structure in later phases — faster and cheaper on tokens.
- **agent-skills** (https://skills.addy.ie, `npx skills add addyosmani/agent-skills`) — optional add-on: 24 engineering-discipline skills (spec-driven dev, incremental implementation, TDD, code review gates). These govern *how well* a phase gets built; this file and PRD.md still govern *what* gets built and *when* — a skill's own workflow never expands a phase's scope on its own.
- **ponytail** (https://ponytail.dev, `/plugin marketplace add DietrichGebert/ponytail` then `/plugin install ponytail@ponytail`) — pushes the agent toward the shortest code that works (stdlib/native/already-installed dependency before anything new). Run it at **`/ponytail lite`**, not `full`/`ultra` — the more aggressive modes push back on requirements to cut scope, which fights this file's phase-by-phase FR discipline. `lite` just names a leaner alternative in one line and leaves the call to the human.

## Conventions

- **Python:** black + ruff, type hints everywhere, Pydantic for all I/O boundaries
- **TypeScript:** strict mode, no `any`
- **Commits:** conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **Tests:** pytest for backend logic, *especially* the geo-integrity validator and scoring engine — these need to be provably correct against the rules in PRD.md §12, not approximately right

## Domain rules (must match PRD.md §12 exactly — that section is authoritative; if these two ever disagree, PRD.md wins and this file is stale and needs fixing)

- GPS accuracy threshold: ≤10 m is the Drishti-manual standard for a good fix. Score bands: 8 pts (≤10m) / 4 pts (10–25m) / 0 pts (>25m or missing).
- Geo-integrity max 30, visual match max 30, satellite response max 30, temporal consistency max 10 → `evidence_score` out of 100.
- Bands: **≥70 verified**, **40–69 review**, **<40 flag**.
- Visual match score answers "is this photo evidence of the declared activity" — it does NOT judge whether the intervention worked. That question belongs entirely to the satellite score. Don't let these two blend together in code or in the UI copy.
- Activity category codes are fixed: AM, VM, SM, PT, NC, BN, LS, LH, OM (PRD.md §15.1 has the full table). Don't invent new categories.

## Non-negotiables

- **Human reviews every diff before it's applied.** Don't assume approval, don't auto-commit, don't auto-push. Propose a plan first for anything beyond a trivial fix; wait for a go-ahead on anything that touches the schema or the scoring formula.
- **Precompute over live calls, always, wherever the demo depends on it.** If you find yourself wiring a live GEE or vision-API call into a request path that's supposed to serve the dashboard, stop — that's a bug against this rule, not a feature.
- **`is_synthetic` is never optional.** Any record that isn't real field data gets `is_synthetic = true` at insert time, no exceptions, and the frontend (Phase 5+) must badge it visibly. This is a hackathon integrity requirement, not polish to skip if short on time.
- **`photo_source` goes with it.** Whenever `is_synthetic = true`, also set `photo_source` (`ai_generated` / `stock_cc` / `unknown`) so the team — and the judges, if asked — always know exactly how a given photo was produced.
- **Never fabricate a number.** If real data isn't available for something, use a clearly-labeled placeholder or synthetic value — don't silently invent a plausible-looking one.
- **Watershed choice is config, not code.** The demo watershed (currently pending — see PRD.md §14) must be swappable via a config value or file path, never hardcoded into schema, seed scripts, or GEE scripts.
- Where a feature maps to one of the PS's expected-solution points (a–g), say which one in a comment or PR description — this is how we keep the PPT's feature-to-requirement table honest.

## Environment

`.env.example` is created in Phase 1 and must stay current. At minimum expect: `DATABASE_URL` (Phase 1), a GEE service-account key path + project ID (Phase 3), a vision-API key (Phase 2).

## How to run

To be filled in during Phase 1 once the scaffold exists (dev server commands, migration commands, test commands). Keep this section current — a stale "how to run" is worse than none.

## Reference material in this repo

- `/docs/PRD.md` — full spec: schema, API contract, phase-by-phase requirements, scoring formula. Read before implementing anything.
- `/docs/PLAYBOOK.md` — deep-dive research doc: why this architecture, GEE code snippets, demo script, PPT structure, judge Q&A prep. Read for context and rationale, not for exact requirements (PRD.md is stricter and wins on any conflict).