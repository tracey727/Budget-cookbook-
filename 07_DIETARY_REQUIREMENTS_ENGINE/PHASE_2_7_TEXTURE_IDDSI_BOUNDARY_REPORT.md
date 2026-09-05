# Phase 2.7 — Texture / IDDSI Boundary

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 2.7.

**GREEN gate (as written):** no recipe is called IDDSI compliant from
description alone.

## What this is

`04_PRODUCTION_STARTER/src/dietary/textureVerification.ts` implements the
`texture_swallowing` taxonomy class (`REGULAR_TEXTURE`, `EASY_TO_CHEW`,
`SAUCE_GRAVY_REQUIRED`, `MOISTURE_REQUIRED`, `IDDSI_LEVEL_0`–`7`) around the
same shape of guarantee as Phase 2.6, aimed at a different failure mode:
Phase 2.6 stops a numeric target from activating without an explicit
source; this phase stops a texture/IDDSI *claim* from existing without an
explicit, tested verification.

`classifyTextureSuitability(recipeId, requirementCode, verifications)` is
deliberately **not given the recipe's name, ingredients, or method text at
all** — only an id to look up against a list of verification records. There
is nothing in its signature to infer from even if the implementation tried,
which is a stronger guarantee than "the code happens not to look at the
name": the name isn't reachable from this function. Verified directly in
`textureVerification.test.ts` by passing a recipe id deliberately named to
sound IDDSI-compliant (`"GEN-RCP-PUREED-SMOOTH-SOUP"`) and confirming the
result is still `UNVERIFIED` absent a real record.

## The only way to reach MEETS/ADAPTABLE/EXCLUDED

`createRecipeTextureVerification` is the sole constructor for a
`RecipeTextureVerification`, and it refuses:
- a `suitability_state` of anything but `MEETS`/`ADAPTABLE`/`EXCLUDED` —
  there is no verified-`UNVERIFIED` state, because a verification record
  only exists when someone has concluded something concrete; "nothing known
  yet" is represented by the record's absence, not a record saying so.
- a `verified_by_source` other than `CLINICIAN_PLAN`/`CARE_PLAN`/
  `TESTED_PREPARATION` — matching `REFERENCE_SOURCES.md`'s framing that
  IDDSI suitability depends on "testing under serving conditions" or a
  clinician/care-plan determination, not an opinion.
- a `method_notes` under 20 characters — long enough to force an actual
  description of what was tested (e.g. "blended smooth, passed IDDSI flow
  test") rather than a placeholder like `"looks soft"`, which the test
  suite specifically tries and confirms gets rejected.

A verification record is also scoped exactly to its `(recipe_id,
requirement_code)` pair — verifying a recipe MEETS `IDDSI_LEVEL_4` says
nothing about `IDDSI_LEVEL_6` on the same recipe, or about a different
recipe entirely. Verified directly in the test suite.

## Requirement-source boundary, mirroring Phase 2.6

`validateTextureRequirementSource` rejects a household member requirement
for a high-consequence texture code (any `IDDSI_LEVEL_*`, plus
`SAUCE_GRAVY_REQUIRED`/`MOISTURE_REQUIRED` — the two dysphagia-relevant
codes added during the Phase 2.1 taxonomy freeze) unless its `source_type`
is `CLINICIAN_PLAN` or `CARE_PLAN`, per
`DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md` section G's explicit framing
("selected by an appropriate clinician or care plan"). `REGULAR_TEXTURE`/
`EASY_TO_CHEW` are treated as ordinary comfort preferences the blueprint
never frames that way, so a plain `USER` source is accepted for those —
the same "don't overreach into ordinary preferences" boundary Phase 2.6
drew for clinician-directed nutrition codes.

## Relationship to Phase 2.4

Phase 2.4 already marked all 12 `texture_swallowing` codes blanket
`UNVERIFIED` for every one of the 800 recipes, explicitly deferring to this
phase rather than guessing. This phase doesn't change any of those rows —
it builds the mechanism that would be the *only* legitimate way to move one
of them off `UNVERIFIED`: a real `RecipeTextureVerification` record, which
requires an actual test or clinical assessment of a specific prepared dish,
not a re-read of its ingredient list. No such verification exists yet for
any of the 800 recipes (consistent with `05_TESTING_AND_DEPLOYMENT`'s
kitchen-testing gates not having run), so every recipe's IDDSI/texture
state remains honestly `UNVERIFIED` until that testing happens.

## Gate status

**GREEN.** 13 checks pass (`npm run test:texture`), including the literal
"named to sound compliant" test that targets the gate's own wording. No
recipe can be called IDDSI compliant from its description because the
classification function is never given the description to begin with.

Next: Phase 2.8 — Full Recipe/Content Production QA (the original Phase 2's
culinary/kitchen-testing scope, now informed by everything 2.1–2.7 built).
