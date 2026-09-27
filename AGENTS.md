# AGENTS.md — SAKSHYA's multi-agent workflow

This is the map for running SAKSHYA's build as four parallel Claude Code subagents instead of one sequential thread. `/docs/PRD.md` still says *what* to build and `/docs/CLAUDE.md` still says *how* — this file says *who* and *when*.

The actual subagent definitions live in `.claude/agents/`:
- `.claude/agents/backend-engineer.md`
- `.claude/agents/geospatial-engineer.md`
- `.claude/agents/vision-ai-engineer.md`
- `.claude/agents/frontend-engineer.md`

Claude Code reads those automatically once they're in place; this file is the human-readable explanation of how they fit together.

## Why this splits cleanly

PRD.md §8 (schema) and §9 (API contract) are frozen up front. That's what makes parallel work safe here: every agent can build against the *documented* shape of data instead of waiting for another agent to actually implement it first. The usual risk of parallel work — four people guessing four different shapes — is closed by having one document all four are required to read before writing anything.

## Roster

| Agent | Owns (PRD phases) | Can start | Needs before it's "real" |
|---|---|---|---|
| `backend-engineer` | 1, 4, 6 (backend half), 7 (backend half) | Immediately | — |
| `geospatial-engineer` | 3 | Immediately (own test points if seed data isn't ready) | A watershed boundary — even a placeholder |
| `vision-ai-engineer` | 2 | Immediately | An image-generation tool (default: Pollinations.ai) |
| `frontend-engineer` | 5, 6 (frontend half), 7 (frontend half) | Immediately, against mocks | `backend-engineer`'s live endpoints, to swap mocks for real calls |

## Rounds

**Round 1 — fully parallel, no cross-dependencies:**
`backend-engineer` → Phase 1 · `geospatial-engineer` → Phase 3 · `vision-ai-engineer` → Phase 2 · `frontend-engineer` → Phase 5 (against mocked JSON matching PRD §9)

**Sync point 1** (human reviews and merges all four):
- `frontend-engineer` swaps mocks for `backend-engineer`'s live endpoints.
- `backend-engineer` wires `geospatial-engineer`'s precomputed output into `GET /mws/{id}/thematic/{layer}` and `POST /assets/{id}/satellite`.
- `backend-engineer` wires `vision-ai-engineer`'s classifier into `POST /assets/{id}/classify`.

**Round 2:**
`backend-engineer` → Phase 4 (now has real sub-scores from Round 1's other three agents to test against, not dummies).

**Sync point 2:** `frontend-engineer`'s asset drawer gets real evidence scores to render.

**Round 3 — joint:**
`backend-engineer` + `frontend-engineer` → Phase 6 (review queue, reports).

**Round 4 — joint:**
All four → Phase 7 (deploy, demo freeze).

## Running Round 1 in parallel

Dispatch all four subagents in the same turn so they run concurrently rather than one after another. Each should produce a **plan only** first — no code — so the human reviews four plans together at one sync point instead of being interrupted four separate times.

## Ground rules every agent shares (defined once in CLAUDE.md, not repeated per-agent)
- Human reviews every diff before it's applied.
- Precompute over live calls, always.
- `is_synthetic` + `photo_source` on every non-real record, no exceptions.
- PRD.md's schema and API contract are authoritative — an agent that wants to deviate from them flags it to the human instead of just doing it.

## Autonomous run mode (no one present to approve mid-session)

Use this only when explicitly invoked — normal operation still pauses for human approval at each sync point (see Rounds above). In autonomous mode:
- Don't wait for a chat reply between rounds — proceed through Round 1 → Sync Point 1 → Round 2 → Sync Point 2 → Round 3 in one continuous session.
- Commit after each agent's slice of each round, with a clear conventional-commit message, so the history stays reviewable even without a live approval gate.
- Maintain `PROGRESS.md` at the repo root — append after every round: what was built, every assumption/default picked on an open question (name the PRD section it relates to), and test results (pytest pass/fail counts).
- On genuine ambiguity (a PRD gap, a tool choice with no confirmed default): pick the most conservative documented default, note it under a `## Needs your attention` section in PROGRESS.md, and keep going — don't halt the whole session over one open question.
- Use the leading watershed candidate from PRD §14 (currently Marigaon, HYBAS_ID 4120883730) without waiting for confirmation — it's designed to be swapped later at zero code cost.
- Stop after Phase 6. Do not attempt Phase 7 (deploy) — it needs live accounts (Vercel/Render/Supabase) only the human has.
- If a required credential is missing entirely (DATABASE_URL, GEE service account, vision API key) and something genuinely can't be tested without it, write that to PROGRESS.md's "Needs your attention" section and keep working on everything else that doesn't need it, rather than stalling the whole session.          