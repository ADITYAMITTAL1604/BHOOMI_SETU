# BhoomiSetu Frontend — GitHub Sync & Integration Guide

> **Purpose:** This document provides a safe, repeatable workflow for syncing your local frontend work with the team's GitHub repository every day without losing local progress or breaking backend integration.

---

## 1. Daily Sync Workflow (Step-by-Step)

### Before You Start Each Day

```bash
# 1. SAVE YOUR WORK — Commit everything locally first
cd d:\BHOOMI_SETU-main
git add -A
git commit -m "wip: save local frontend progress before sync"

# 2. FETCH remote changes (does NOT modify your files)
git fetch origin

# 3. SEE what changed on the remote
git log --oneline HEAD..origin/develop --stat
# or if your integration branch is 'main':
git log --oneline HEAD..origin/main --stat

# 4. COMPARE diff to understand what backend teammates changed
git diff HEAD..origin/develop -- backend/
git diff HEAD..origin/develop -- docker-compose.yml
git diff HEAD..origin/develop -- data/
git diff HEAD..origin/develop -- ml/
```

### Merge Strategy

```bash
# 5. REBASE your work on top of the latest remote
#    (This keeps YOUR commits on top and applies backend changes underneath)
git rebase origin/develop

# If there are conflicts:
#   a) Open conflicted files — YOUR changes are marked <<<<<<< HEAD
#   b) Resolve by keeping BOTH sides where possible
#   c) git add <resolved-file>
#   d) git rebase --continue

# If rebase gets messy, abort and use merge instead:
# git rebase --abort
# git merge origin/develop
```

### After Sync

```bash
# 6. VERIFY nothing broke
cd frontend
npm install        # in case package.json changed
npm run dev        # test that frontend still compiles

# 7. CHECK for new backend API endpoints or schema changes
git diff HEAD~1..HEAD -- backend/app/routers/
git diff HEAD~1..HEAD -- backend/app/schemas/
git diff HEAD~1..HEAD -- backend/app/models/
```

---

## 2. What to Watch For in Backend Changes

### Critical Files to Monitor

| File/Directory | Why It Matters |
|---|---|
| `backend/app/routers/*.py` | New or changed API endpoints — update `frontend/src/api/` accordingly |
| `backend/app/schemas/*.py` | Pydantic schemas = API contracts — update `frontend/src/types/` |
| `backend/app/models/*.py` | Database model changes — may affect field names in API responses |
| `docker-compose.yml` | Port or service config changes — update `.env` / proxy config |
| `backend/requirements.txt` | New deps may require Docker rebuild |
| `data/boundaries/*.geojson` | New GIS data available for map rendering |
| `data/synthetic/*.csv` | New seed data — dashboard/charts may show different numbers |
| `ml/models/*.joblib` | ML model updates — analytics page predictions may change |

### How to Detect API Contract Changes

```bash
# Quick check: did any router or schema file change?
git diff HEAD~1..HEAD --name-only -- backend/app/routers/ backend/app/schemas/

# Detailed: what exactly changed in a specific router?
git diff HEAD~1..HEAD -- backend/app/routers/projects.py
```

### Integration Checklist After Sync

- [ ] New API endpoints? → Add corresponding functions in `frontend/src/api/`
- [ ] Schema field changes? → Update TypeScript types in `frontend/src/types/`
- [ ] New env variables? → Add to `frontend/.env` and `.env.example`
- [ ] Docker changes? → May need `docker-compose down && docker-compose up --build`
- [ ] New seed data? → May need to re-seed: `docker exec bhoomisetu-backend python db/seed.py`
- [ ] New GIS boundaries? → Verify map renders correctly

---

## 3. File Ownership — Safe Zones

These files are **yours** (FE team). Backend won't touch them:

```
frontend/src/pages/          # All page components
frontend/src/components/     # All UI components
frontend/src/hooks/          # Custom React hooks
frontend/src/store/          # Zustand stores
frontend/src/styles/         # All CSS/styling
frontend/src/utils/          # Utility functions
```

These files are **shared** — edit carefully:

```
frontend/src/types/          # Shared with backend contract
frontend/src/api/            # Must match backend endpoints
frontend/package.json        # Both FE devs may add deps
frontend/src/App.tsx         # FE-1 owns routing, FE-2 adds routes
```

These files are **backend-owned** — don't edit, only read:

```
backend/                     # Entirely backend-owned
docker-compose.yml           # BE-1 owns, request changes via message
data/                        # RS team generates
ml/                          # RS-2 + BE-2 own
```

---

## 4. Handling Common Scenarios

### Scenario A: Backend Added a New API Endpoint

1. Check `backend/app/routers/` for the new file/function
2. Check `backend/app/schemas/` for the request/response shape
3. Create matching TypeScript types in `frontend/src/types/`
4. Create API function in `frontend/src/api/`
5. Update mock data if still using mocks

### Scenario B: Backend Changed an Existing API Response

1. Identify which fields changed via `git diff`
2. Update the TypeScript interface in `frontend/src/types/`
3. Search your components for usages: `grep -r "old_field_name" frontend/src/`
4. Update all component references
5. Test the affected pages

### Scenario C: Docker Config Changed

```bash
# Rebuild everything
docker-compose down
docker-compose up --build -d

# Check services are healthy
docker-compose ps
```

### Scenario D: Merge Conflict in a Shared File

```bash
# If conflict is in package.json:
#   - Keep BOTH sets of dependencies
#   - Run `npm install` after resolution

# If conflict is in types/api.ts:
#   - Keep ALL type definitions from both sides
#   - Remove duplicates

# If conflict is in App.tsx routing:
#   - Keep ALL route entries from both sides
```

---

## 5. Quick Reference Commands

```bash
# See all changes since your last sync
git log --oneline --graph --all -20

# See only backend changes
git diff origin/develop -- backend/

# See if any API contracts changed
git diff origin/develop -- backend/app/schemas/ backend/app/routers/

# Stash your work temporarily (if you need a clean slate)
git stash push -m "frontend-wip"
# ... do whatever ...
git stash pop

# Create a safety branch before risky merge
git branch backup/frontend-$(date +%Y%m%d)
```

---

## 6. Emergency Recovery

If something goes catastrophically wrong after a sync:

```bash
# Option 1: Go back to your last commit
git reset --hard HEAD~1

# Option 2: Go back to your backup branch
git checkout backup/frontend-YYYYMMDD

# Option 3: If you stashed
git stash pop
```

> **Golden Rule:** Always `git commit` your local work BEFORE pulling/rebasing. Your commits are your safety net.
