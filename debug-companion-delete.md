# Debug Session: Companion Delete Button

**Session ID:** `companion-delete`

**Status:** `[OPEN]`

**Problem:** The delete button for companions is not working - the companion is not being deleted from frontend and/or backend.

---

## Hypotheses

1. **H1:** The deleteCompanion function in store.ts is not being called at all (UI event handler issue)
2. **H2:** The deleteCompanion function is being called but the state update is not persisting
3. **H3:** The backend API call is failing (authorization or endpoint issue)
4. **H4:** The maybeAbandonScenario cleanup function is re-adding the deleted companion
5. **H5:** The Zustand persist middleware is restoring old state after deletion

---

## Instrumentation Points

### Frontend (store.ts)
- Line 520: Entry point of `deleteCompanion`
- Line 524: Before `set()` call (state update)
- Line 536: After `set()` call
- Line 544: Backend API call
- Line 927: Entry point of `maybeAbandonScenario`
- Line 930: Check if companion exists

### Frontend (Chat.tsx)
- Line 412: Delete button onClick handler
- Line 414: Before `deleteCompanion` call
- Line 416: After `deleteCompanion` call, before `navigate`

### Backend (chat_routes.py)
- Line 709: Entry point of DELETE /companion/{companion_id}
- Line 721: After resolve_backend_id
- Line 744: Before return statement

---

## Test Steps

1. Start backend server and frontend dev server
2. Open browser at http://localhost:5174
3. Log in with test account
4. Add a companion if none exists
5. Open browser DevTools (F12) → Console tab
6. Navigate to chat with a companion
7. Click "More" → "Delete Companion"
8. Confirm deletion
9. Observe console logs and network tab
10. Check if companion is removed from dashboard

---

## Expected Behavior

1. Console should show: `[deleteCompanion] called with companionId: c1`
2. Console should show: `[deleteCompanion] Updating state: {...}`
3. Console should show: `[deleteCompanion] backend response status: 200`
4. Console should show: `Navigated to /app`
5. Dashboard should no longer show the deleted companion
6. localStorage should be updated (companion removed from myCompanions)

---

## Current Observations

[To be filled during testing]

---

## Fix Applied

[To be filled after root cause is identified]

---

## Verification

[To be filled after fix is tested]
