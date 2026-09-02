# BhoomiSetu — Claude Code Subagents

Drop this `.claude/agents/` folder at the root of your BhoomiSetu repo (alongside
`docker-compose.yml`) and commit it — project-scoped subagents in `.claude/agents/` are
meant to be checked into version control so the whole team gets the same specialists.

## Agents in this folder

| Agent | Use for |
|---|---|
| `backend-engineer.md` | FastAPI routes, SQLAlchemy/GeoAlchemy2 models, RBAC/scope services, ML serving, Alembic migrations |
| `frontend-engineer.md` | React/TS pages & components, GIS map, dashboards, Zustand/React Query wiring |
| `e2e-test-engineer.md` | Playwright suites across all 6 demo roles — workflows, GIS, uploads, role boundaries |
| `security-auditor.md` | OWASP API Top 10 red-teaming, RBAC/scope verification, GIS & file-upload security, audit-log integrity |

## How Claude picks an agent

Claude Code delegates automatically based on each agent's `description` field and what
you're asking for. You can also invoke one explicitly:

```
Use the backend-engineer agent to add the /parcels/{id}/risk endpoint
Use the security-auditor agent to red-team the document upload flow
@e2e-test-engineer write tests for the compensation workflow
```

## Recommended flow against the 5-Day Implementation Plan

- **Day 1–3 (Foundation → Intelligence):** `backend-engineer` and `frontend-engineer` do
  the build, in the same division of labor as the plan's BE-1/BE-2/FE-1/FE-2 tracks.
- **Day 4 (Full Testing / Red Team):** run `e2e-test-engineer` and `security-auditor`
  together. Feed the plan's Day-4 testing checklist to both — they're each written to map
  directly onto it (functional/role tests → e2e-test-engineer; security/OWASP tests →
  security-auditor).
- **Day 5 (Polish):** re-run both testing agents against fixes before freezing the demo.

## Keeping agents in sync with the spec

All four agents are written to treat `docs/TRD.md`, `docs/Security.md` (or the original
`02_TRD_BhoomiSetu` / `03_Security_Access_Control` docs), and the Frontend Specification as
source of truth. If those documents change — a new role, a new endpoint, a changed
permission — update the relevant agent file's summary tables so it doesn't drift from the
real spec. Each agent is instructed to flag Access-Control-Matrix changes so the other
agents stay consistent.

## Notes on scope

Each agent's `tools:` list is intentionally narrow:
- `backend-engineer` / `frontend-engineer` can read, write, edit, and run shell commands
  (tests, dev servers, migrations) but nothing beyond the repo.
- `e2e-test-engineer` can read/write/edit test files and run Playwright via bash, but isn't
  meant to modify application source — if a test reveals a bug, it reports it rather than
  patching app code itself.
- `security-auditor` is read-mostly (`Read, Grep, Glob, Bash, WebSearch, WebFetch`) by
  design — it's meant to find and report, not silently fix, so findings go through the
  same Critical/High/Low triage the team already uses on Day 4.
