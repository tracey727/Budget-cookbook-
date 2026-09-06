# Phase 2.6 — Medical / Professional-Plan Boundaries

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 2.6.
Builds on the household combination engine (2.3).

**GREEN gate (as written):** medical modes cannot activate from an AI
inference about the user's health; they require explicit user/
professional-plan configuration.

## What this is

`04_PRODUCTION_STARTER/src/dietary/professionalTargets.ts` implements the
`clinician_directed` taxonomy class (`SODIUM_TARGET`, `CARBOHYDRATE_TARGET`,
`ENERGY_TARGET`, `PROTEIN_TARGET`, `POTASSIUM_LIMIT`, `PHOSPHATE_LIMIT`,
`FLUID_PLAN`, `FAT_TARGET`, `FIBRE_TARGET`, `PKU_PHENYLALANINE_PLAN`, plus
custom professional plans) matching `professional_nutrition_targets` in
`schema/002_dietary_requirements.sql`, built around one rule: **a
clinician-directed requirement flag does nothing on its own.** It only
becomes live once a specific, explicitly-supplied numeric target backs it
for that exact member.

## Why this needed to be a structural property, not a policy note

The gate text ("cannot activate from an AI inference") is a claim about
*code*, not about intentions, so this phase treats it as one:

1. **`createProfessionalNutritionTarget` is the only constructor.** It
   throws if `target_value` isn't a real finite number, if `target_unit` is
   empty, or if `source_type` isn't exactly `USER`/`CLINICIAN_PLAN`/
   `CARE_PLAN` — there is no fourth, system-generated source value anywhere
   in the type, so a target can never claim to be inferred rather than
   supplied. No other function in this module (or anywhere else in the
   dietary engine so far) produces a `ProfessionalNutritionTarget` — nothing
   derives a sodium limit from, say, another member's blood-pressure-sounding
   custom exclusion or a recipe's own content, because no such function
   exists to call.
2. **`checkClinicianDirectedActivation`** answers "is this requirement
   usable for this member right now?" by checking for a real, currently
   active (`starts_at`/`ends_at`-aware) target record — not by checking
   whether the requirement flag is merely set. A bare
   `member_dietary_requirements` row of `SODIUM_TARGET: REQUIRE_VERIFIED`
   with no backing target is inert.
3. **`applyProfessionalTargetGate`** wires this into the actual request
   pipeline: it post-processes Phase 2.3's `combineHouseholdRequirements()`
   output, stripping any clinician-directed contribution that lacks a
   backing target — per member, not per household, so one member's real
   target never covers another member's unbacked flag. An entry that loses
   every contributor this way disappears from the combined result entirely,
   exactly as if the flag had never been set. This is verified end-to-end in
   `professionalTargets.test.ts`, not just asserted in isolation: a household
   combination that shows `SODIUM_TARGET` as active (Phase 2.3 alone doesn't
   know targets exist) comes out of the Phase 2.6 gate with that entry gone
   when unbacked, and correctly present once a real target is attached.

## Custom professional plans without a fixed code list

The blueprint allows "other prescribed nutrient limit entered as a custom
professional plan" beyond the 10 named codes. Rather than hard-coding an
exhaustive list (which would need updating for every new plan type),
`isClinicianDirectedCode` treats *any* code as clinician-directed once a
`CLINICIAN_PLAN`- or `CARE_PLAN`-sourced target is attached to it — so the
same activation gate applies without this module needing to know the
custom label in advance. Deliberately narrower on the other side: an
arbitrary `USER`-sourced code does *not* get treated as clinician-directed,
so this gate doesn't overreach into gating ordinary user preferences that
happen to share the mechanism.

## What this phase does not do (correctly out of scope)

- **No nutrition matching.** Phase 2.4 already established, correctly, that
  the 800-recipe V1 baseline has no nutrition data (calories, sodium,
  macros) to check a target against, and that none may be invented. This
  phase does not change that — it only governs whether a clinician-directed
  *flag* is allowed to be live, not what a recipe's sodium content is
  (there isn't one to check yet). Recipe-side nutrition data, if ever added,
  is Phase 4/5 territory (canonical ingredient/unit model, production
  schema), and applying it is evaluation-order step 8 in
  `DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md` — genuinely not buildable until
  that data exists.
- **No diagnosis or prescription generation.** There is no function
  anywhere in this codebase that accepts a health condition, symptom, or
  diagnosis-shaped string and returns a target — the absence of such a
  function is itself the safeguard, not something this module could
  "turn off" if asked to. `createProfessionalNutritionTarget`'s only inputs
  are the exact fields a person would already have on paper.
- **Privacy/minimisation carried through from Phase 2.3**: `notes` is
  optional and free text is never required to activate a target — matching
  `HOUSEHOLD_MEMBER_PROFILE_CONTRACT.md`'s "prefer 'sodium limit supplied by
  user/care plan' over storing unnecessary clinical narrative."

## Verification

19 checks in `professionalTargets.test.ts` (`npm run test:professional`),
covering: constructor rejection of missing/NaN values, empty units, and
invalid source types; single- and cross-member activation correctness;
date-window expiry; the non-clinician-directed pass-through boundary; custom
professional-plan codes; and the full Phase 2.3 → Phase 2.6 pipeline,
including a two-member case where only the backed member's contribution
survives and the group's effective enforcement is correctly recomputed from
survivors only. `household.ts` gained one non-behavioural change
(`ENFORCEMENT_PRECEDENCE` exported instead of module-private) so this phase
could reuse it rather than duplicate it; `test:dietary`'s 12 checks still
pass unchanged.

## Gate status

**GREEN.** A clinician-directed mode cannot activate from an AI inference
because there is no function capable of producing one that way — the only
constructor demands explicit numeric fields and rejects anything else, and
the activation gate checks for a real record, not a flag. Next: Phase 2.7 —
Texture / IDDSI Boundary.
