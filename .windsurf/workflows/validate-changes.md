---
description: Validate UI/API changes with Playwright before claiming completion
---

# Veritas Definition of Done — Validation Workflow

**Purpose:** Enforce validation before reporting any UI/API change as "done"

## Required Steps

### 1. Run Playwright Tests
```bash
cd frontend
npx playwright test
```

**Expected:** All tests pass (exit code 0)

### 2. Capture Fresh Screenshots
```bash
# Screenshots automatically saved to:
# frontend/tests/screenshots/success.png
```

### 3. Verify Screenshots
- Open `frontend/tests/screenshots/success.png`
- Confirm visual changes match expected behavior
- Verify backend changes are visible in UI (not just logs/API)

### 4. Check Test Output
```bash
# Look for:
# - "2 passed" (or expected count)
# - No failures
# - Screenshot artifacts generated
```

## Failure Rules

**If Playwright fails:**
- Task is NOT done
- Debug test failure
- Fix code
- Re-run validation

**If screenshots don't match expected:**
- Task is NOT done
- Investigate UI rendering
- Fix display logic
- Re-run validation

**If backend change not visible in UI:**
- Task is NOT done
- Check data flow: backend → API → frontend → UI
- Fix transformation/rendering
- Re-run validation

## Reporting Rules

**Never say "fixed" based only on:**
- Code changes
- API responses
- Backend logs
- Curl tests

**Only report "done" when:**
- Playwright tests pass
- Screenshots validate expected behavior
- UI proof exists and is consistent

**Include in completion report:**
- Test name: `[chromium] › tests/e2e.spec.ts:4:3 › Veritas End-to-End Integration`
- Route/flow tested: `localhost:5175 → synthesis → render`
- Screenshot result: `tests/screenshots/success.png shows [describe what's visible]`

## Automation

**Before claiming completion, run:**
```bash
cd /Users/justinharmon/Library/CloudStorage/Dropbox-HammerConsulting/Justin\ Harmon/AI_SYSTEMS/8825-modules/Veritas/frontend
npx playwright test && echo "✅ Validation passed - task complete" || echo "❌ Validation failed - task not done"
```

**Then verify screenshot manually or programmatically.**
