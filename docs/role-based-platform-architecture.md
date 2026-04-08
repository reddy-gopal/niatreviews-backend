# Role-Based Platform Architecture

## Scope

This document captures:

1. What is currently implemented across backend and frontend.
2. What we want to implement based on the updated product architecture.
3. A practical phased plan to move from current state to target state.

---

## Current Implementation (As-Is)

### Role model

- Role handling is currently centered on `User.role` in `accounts`.
- Existing role logic in code is mixed/hardcoded in multiple places.
- Current active roles in backend code have included `student`, `senior`, `founding_editor`, `admin`, `moderator` (legacy values still exist in codepaths).

### Article writing and publishing

- Article create endpoint is authenticated and available broadly to logged-in users.
- Publish flow already uses moderation/review in parts of the system, but role-based author unlock is not fully enforced end-to-end.
- Frontend write access is mostly gated by login/onboarding checks and backend fallback errors (not a single explicit role-policy gate everywhere).

### Onboarding/profile structure

- Founding editor profile flow exists and has dedicated profile data handling.
- No fully separated onboarding pipeline for:
  - Intermediate student
  - NIAT student
- NIAT verification artifacts (ID card/ID number/campus proof) are not yet modeled as a dedicated complete role-specific onboarding + approval pipeline.

### Verification to role-upgrade

- Verification exists in the platform, but automatic role transition:
  - `niat_student` -> `founding_editor`
  is not yet standardized as a single backend workflow with notification guarantees.

---

## Target Implementation (To-Be)

## Canonical roles (from now onward)

Only these roles should exist and be used in authorization logic:

- `intermediate_student`
- `niat_student`
- `founding_editor`
- `moderator`
- `admin`

Legacy role values should be migrated and removed from policy checks.

### Role progression rules

- A newly onboarded NIAT user starts as `niat_student`.
- When moderator/admin verifies NIAT profile, user is automatically upgraded to `founding_editor`.
- On upgrade:
  - Founding editor badge is shown in profile.
  - Email is sent: write access unlocked.

### Onboarding UX and data collection

During onboarding, user must choose:

1. Intermediate student
2. NIAT student

If **Intermediate student**:
- Show intermediate student details form (profile fields defined by product).

If **NIAT student**:
- Collect:
  - student ID card (file upload)
  - student ID number
  - campus name
  - additional required details
- Mark profile as pending review.
- Allow moderator/admin review workflow for approve/reject.

### Article authoring policy

- Students can submit articles.
- Student-submitted articles go through review/moderation before going live.
- Moderator/admin approves/rejects publication.
- Founding editors can write with unlocked privileges per policy.

### Data model separation

Use separate tables for role-specific profiles:

- `IntermediateStudentProfile`
- `NiatStudentProfile`
- `FoundingEditorProfile`
- `ModeratorProfile`
- `AdminProfile`

Notes:
- Keep `User` as identity/auth table.
- Role-specific table has one-to-one relation with user.
- Shared fields can stay in user; role-specific fields should live in profile tables.

---

## Gap Summary (Current vs Target)

1. **Role set mismatch**
   - Current code still references legacy roles.
   - Need canonical five-role model.

2. **No complete NIAT -> Founding Editor auto-upgrade pipeline**
   - Need workflow + audit trail + notification.

3. **Onboarding split not fully implemented**
   - Need explicit role choice and conditional multi-form onboarding.

4. **Review-gated article lifecycle not uniformly enforced for all student flows**
   - Need one policy matrix and backend enforcement.

5. **Separate profile tables not fully implemented for all roles**
   - Need schema + migration + API + admin tooling.

---

## Proposed Implementation Plan

### Phase 1: Role normalization (backend-first)

- Finalize role enum to 5 canonical roles.
- Add migration for existing users (map legacy roles safely).
- Refactor permission checks to use centralized role helpers/constants.

### Phase 2: Profile table architecture

- Create role-specific profile models/tables.
- Add one-to-one relationships and constraints.
- Add serializers and endpoints for each profile type.

### Phase 3: Onboarding split

- Frontend onboarding role selector.
- Conditional forms:
  - Intermediate student form
  - NIAT student verification form
- Backend endpoints to store drafts/submissions and status.

### Phase 4: Verification and auto-upgrade workflow

- Moderator/admin review actions for NIAT submissions.
- On approval:
  - set user role to `founding_editor`
  - create/update founding editor profile
  - attach badge metadata
  - send unlock email event

### Phase 5: Article permissions and moderation policy

- Central permission matrix for create/edit/publish.
- Enforce in backend APIs first.
- Align frontend UI visibility with backend policy (write button, pages, messaging).
- Ensure student-origin articles are review-gated before publish.

### Phase 6: Observability and audit

- Add audit logs for:
  - role changes
  - verification decisions
  - article moderation actions
- Add notification history and retry-safe email dispatch.

---

## Suggested Permission Matrix (initial draft)

- `intermediate_student`
  - Can create draft/submit article
  - Cannot publish directly
- `niat_student`
  - Can create draft/submit article
  - Cannot publish directly
- `founding_editor`
  - Can write with unlocked access (publish policy to be finalized: direct publish vs fast-track review)
- `moderator`
  - Can review/approve/reject articles
  - Can verify NIAT profiles
- `admin`
  - Full override permissions

---

## Open Product Decisions (Need final sign-off)

1. Should founding editors publish directly, or still require moderation?
2. Should intermediate/niat students be allowed to edit after submission while pending review?
3. What exact fields are mandatory in each onboarding form?
4. Badge taxonomy:
   - only founding editor badge, or role badges for all roles?
5. Rejection loop:
   - how users resubmit NIAT verification after rejection?

---

## Definition of Done

Architecture is complete when:

- Only canonical five roles are used in production authorization.
- Onboarding role split is live with conditional forms.
- NIAT verification approval automatically upgrades role to founding editor.
- Unlock email is sent reliably on approval.
- Profile badge updates automatically post-upgrade.
- Student-authored articles follow enforced review-before-live workflow.
- Separate role-specific profile tables are active and used by APIs/UI.
