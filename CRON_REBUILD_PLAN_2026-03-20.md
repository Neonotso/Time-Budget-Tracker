# Cron Rebuild Plan — 2026-03-20

## Objective
Cleanly separate Sally-facing reminder jobs from Gus-owned background jobs, with explicit delivery behavior for each.

## Guiding rule
- **Sally/main jobs** = things meant to talk directly to Ryan as Sally in Sally's thread.
- **Gus jobs** = operational/background work.
- **No implicit announce delivery** for Gus jobs.
- If a Gus job needs to notify Ryan, it should do so via an explicitly designed path, not inherited cron announce behavior.

---

## Recommended ownership + delivery matrix

### Keep on Sally / main

#### 1) Regular email check
- **Job:** `1cc650ef-8022-4e45-8849-6fa86e6e91c0`
- **Owner:** Sally (`main`)
- **Session target:** `main`
- **Delivery:** main-session only
- **Reason:** This is explicitly Ryan-facing and belongs in Sally's conversational context.

#### 2) Morning money board
- **Job:** `b5afb83e-a86c-45b5-a993-a49b86ffea8d`
- **Owner:** Sally (`main`)
- **Session target:** `main`
- **Delivery:** main-session only
- **Reason:** This is a Ryan-facing planning/reporting task, not backend grunt work.

---

## Keep on Gus, internal-only by default

#### 3) Bible readers SMS reminder dispatcher
- **Job:** `3ac6a4e1-e96c-4247-aacd-3dcf67a0538e`
- **Owner:** Gus
- **Session target:** `isolated`
- **Delivery:** `none`
- **Reason:** Routine operational job. If no issues, Ryan does not need noise.
- **Future option:** failure-alert only.

#### 4) Email receipts to budget (Amazon)
- **Job:** `9e46aae7-126c-475d-8f2b-218d798a34d2`
- **Owner:** Gus
- **Session target:** `isolated`
- **Delivery:** `none`
- **Reason:** Usually silent bookkeeping. Only interesting when broken or materially changed.
- **Future option:** failure-alert only.

#### 5) Monthly PIER Report Report
- **Job:** `01102deb-3743-4426-81d2-e6fa8624edf1`
- **Owner:** Gus
- **Session target:** `isolated`
- **Delivery:** `none`
- **Reason:** Better as backend automation unless explicit reporting is wanted.
- **Future option:** send success/failure summary to a dedicated reporting channel.

---

## Keep on Gus, but likely needs explicit reporting path later

#### 6) Nightly Venmo to bank transfer
- **Job:** `3956d85f-f139-49af-9451-36466cf11a84`
- **Owner:** Gus
- **Session target:** `isolated`
- **Current delivery:** `none` (containment)
- **Recommended long-term:** explicit notification, but only through a deliberate path
- **Reason:** Financial transfers are important enough that Ryan may want a heads-up, but not via inherited ambiguous cron announce routing.
- **Best future pattern:** internal run + explicit message to Sally or an explicit target channel if transfer actually happened.

#### 7) After-lesson automation sweep
- **Job:** `bd393969-eaef-48a2-b7e5-39ce5c8d46bd`
- **Owner:** Gus
- **Session target:** `isolated`
- **Current delivery:** `none`
- **Current status:** disabled
- **Recommended long-term:** notify only on meaningful completed work or blocker
- **Reason:** This can matter to Ryan, but only when something was processed or blocked. Silent when no action.
- **Best future pattern:** internal run + explicit escalation only on work done / blocker.

---

## Rebuild strategy

### Phase A — already done
- Fixed config syntax issue in `~/.openclaw/openclaw.json`
- Contained migrated Gus jobs with `delivery.mode = none`

### Phase B — normalize jobs in place (safe short-term)
For Gus jobs, make sure:
- `sessionTarget = isolated`
- `delivery.mode = none`
- no stray channel/target assumptions remain

### Phase C — clean recreation (preferred)
Recreate Gus jobs fresh one by one with:
- intentional owner
- intentional session target
- intentional delivery mode
- optional failure alerts configured explicitly

### Phase D — explicit escalation design
For jobs that should sometimes reach Ryan:
- prefer explicit failure alerts or explicit post-run routing
- avoid ambiguous inherited announce behavior

---

## My recommendation for next implementation step
1. Leave Sally jobs alone.
2. Normalize Gus jobs to internal-only.
3. Add explicit failure alerts for the Gus jobs where silent failure would be bad.
4. Later, if needed, add deliberate success notifications for:
   - Venmo transfer
n   - After-lesson automation
