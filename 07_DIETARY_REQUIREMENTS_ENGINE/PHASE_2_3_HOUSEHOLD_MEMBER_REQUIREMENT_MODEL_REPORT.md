# Phase 2.3 — Household Member Requirement Model

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 2.3.
Builds on the frozen taxonomy (Phase 2.1) and ingredient attribute model
(Phase 2.2).

**GREEN gate (as written):** different members can carry conflicting
requirements without one profile overwriting another.

## What this is

`04_PRODUCTION_STARTER/src/dietary/household.ts` implements the household
member / member-requirement / custom-rule types and a
`combineHouseholdRequirements()` function that resolves, for a meal shared by
a selected subset of a household's members, which requirements apply and at
what severity — steps 1–2 of the "Recipe evaluation order" in
`DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md` ("Resolve selected household
members for the meal" and "Combine hard exclusions first"). Field shapes
match `HOUSEHOLD_MEMBER_PROFILE_CONTRACT.md` and the
`household_members`/`member_dietary_requirements`/`custom_dietary_rules`
tables in `schema/002_dietary_requirements.sql`.

This phase stops there deliberately. Turning the combined requirement set
into a per-recipe `MEETS`/`ADAPTABLE`/`EXCLUDED`/`UNVERIFIED` verdict needs
recipe classification (Phase 2.4) and substitution mapping (Phase 2.5),
neither of which exist yet — building that logic now would mean guessing at
interfaces Phase 2.4/2.5 haven't defined. No API endpoint was added to
`src/index.ts` either: an endpoint would need household persistence (Phase 9)
and authentication (Phase 13), both later gates. Wiring this module into the
Worker before then would expose an endpoint with nothing real behind it.

## How "no overwriting" is actually enforced, not just asserted

Two design choices make the GREEN gate a property of the code, not a
convention someone could accidentally break:

1. **`perMember` is append-only per requirement key.** When two members
   carry the same `requirement_code` (e.g. both have `LACTOSE_FREE`),
   `combineHouseholdRequirements` pushes both members' individual
   `{member_id, enforcement_level, source_type, notes}` records into the same
   entry's `perMember` array — it never replaces one member's record with
   another's. The group-level `effectiveEnforcement` (used to decide whether
   the *meal* must treat the requirement as a hard exclusion) is a derived
   maximum computed alongside that array, not a value that lives instead of
   the per-member detail.
2. **Requirements outside their active window, inactive members, and unknown
   member ids all throw or are excluded explicitly** — `isActiveOn()` checks
   `starts_at`/`ends_at` against the `asOf` date, `active: false` members are
   rejected if selected for a meal, and an unrecognised member id throws
   rather than being silently dropped. Silent exclusion would be its own
   kind of "overwriting" (a member's requirement disappearing without
   anyone deciding that).

## Verification

`household.test.ts` reproduces the exact "Core household use case" from
`DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md` (Member A: vegetarian + soft
lactose avoidance; Member B: no restriction; Member C: peanut allergy;
Member D: sensory preference), plus edge cases the gate wording implies but
the base example doesn't cover: two members sharing a requirement code at
different severities, a meal that excludes the stricter member, an inactive
member, an expired clinician-plan requirement, and an unknown member id.

No test runner is wired into `04_PRODUCTION_STARTER/package.json` yet (only
`tsc`/`wrangler` are devDependencies), so this isn't a framework-based suite
— it's a standalone assertion script, run via the new `npm run test:dietary`
script (`tsc --ignoreConfig ... && node dist/dietary-test/household.test.js`,
compiling outside the project's own `tsconfig.json` since Cloudflare Workers
types aren't relevant to this pure-logic module). All 12 checks pass:

```
PASS vegetarian hard exclusion present from Member A
PASS peanut allergy hard exclusion present from Member C
PASS Member B (no restrictions) does not remove A's or C's hard exclusions
PASS Member D's sensory preference is preserved as a preference, not dropped or promoted to a hard exclusion
PASS Member A's own VEGETARIAN record is still individually attributable to A, not merged away
PASS group-level LACTOSE_FREE escalates to HARD_EXCLUDE because Member E requires it, even though Member A only prefers it
PASS Member A's own PREFER-level record is NOT overwritten by Member E's HARD_EXCLUDE -- both are visible in perMember
PASS excluding Member E from the meal means the group constraint reverts to A's own PREFER level
PASS selecting an inactive member for a meal is rejected, not silently honoured
PASS a requirement past its ends_at date does not apply to today's meal
PASS the same requirement DOES apply when asOf falls inside its starts_at/ends_at window
PASS selecting an unknown member id throws rather than silently proceeding
```

`household.ts` also typechecks clean under `--strict` (verified standalone,
since the project's own `tsc --noEmit` needs `@cloudflare/workers-types`
installed via `npm install`, which this sandbox didn't run — the module
itself has no Workers-specific dependency, so this doesn't affect it).

## Privacy/minimisation carried through from the contract

`MemberDietaryRequirement.professional_plan_reference` exists on the type
(per `HOUSEHOLD_MEMBER_PROFILE_CONTRACT.md`: "never expose unnecessarily")
but is never read by `combineHouseholdRequirements` or surfaced in
`CombinedRequirementEntry` — only `requirement_code`, `enforcement_level`,
`source_type`, and `notes` cross into the combined/explanation output.

## Custom rules are first-class, not an afterthought

`custom_dietary_rules` entries are folded into the same combination pass as
taxonomy-coded requirements (keyed as `CUSTOM:<rule_label>` since they don't
have a fixed taxonomy code), with the same per-member provenance and
enforcement-precedence logic — matching the "extensibility requirement" in
`DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md` that custom rules must be
first-class records the recommendation engine actually reads, not free text
it ignores.

## Gate status

**GREEN.** Verified by a passing test suite that specifically targets the
gate's wording ("without one profile overwriting another"), not just a
plausible-looking implementation. Next: Phase 2.4 — classify all 800 recipes
against the Phase 2.2 ingredient attribute table (producing
`recipe_requirement_assessments` rows), which is also the phase that will
start actually consuming this module's combined-requirement output.
