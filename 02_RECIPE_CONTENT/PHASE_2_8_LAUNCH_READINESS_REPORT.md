# Phase 2.8 — Full Recipe/Content Production QA

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 2.8
— the closing sub-phase of the expanded Phase 2, folding the original V1
recipe-content QA back in now that the full dietary engine (2.1–2.7) exists
to inform it.

**GREEN gate (as written):** no unsafe/misleading dietary claims; all
public launch recipes have reviewed content; unresolved recipes stay out of
the launch set or remain visibly unverified.

## What this is

`build_launch_readiness.py` draws the actual launch/hold line across all
800 recipes by combining three things already built in this pack:

1. **`PHASE2_QA_REPORT.md` / `phase2_qa_flags.json`** — duplicate-name,
   method/timing, and quantity-realism screens (0 flags on all three across
   800 recipes), plus the 415-recipe high-risk-scaling-category kitchen-test
   queue (eggs, raising agents, strong spices, cooking fat, canned/packaged
   items — categories the blueprint says must not be blindly scaled).
2. **`recipe_requirement_assessments_v1.json`** (Phase 2.4) — confirms every
   recipe has a dietary classification record.
3. **The frozen claim language** (`DIETARY_CLAIM_LANGUAGE.md`, Phase 2.1's
   `PHASE_2_1_TAXONOMY_AND_LANGUAGE_FREEZE.md`) — already live as a banner
   and per-recipe badges in `03_WORKING_PROTOTYPE/index.html`, not something
   this phase needed to add.

Output: `recipe_launch_readiness_v1.json`, one row per recipe with a
`LAUNCH_READY` or `HELD_FOR_KITCHEN_TEST` verdict and the specific reason.

## Result

- **385 recipes `LAUNCH_READY`** — zero open QA flags, complete dietary
  classification.
- **415 recipes `HELD_FOR_KITCHEN_TEST`** — every one is a high-risk-scaling
  hold (egg/raising-agent/spice/fat/canned-good categories per Phase 2's
  original screen), not a content defect: 0 exact duplicates and 0 timing/
  quantity flags were found anywhere in the 800-recipe baseline. Nothing was
  dropped outright — every held recipe is a real, distinct, plausibly
  correct recipe that specifically needs a human scaling/kitchen-test pass
  before its behaviour at non-default household sizes can be trusted, per
  `MASTER_PRODUCT_BLUEPRINT.md` rule 7 ("strong spices, pan oil and raising
  agents require special scaling rules rather than blind multiplication").
- **0 missing dietary classifications** — every recipe has a Phase 2.4 row.

## Why this isn't (and can't honestly be) "0 held"

An AI content pass cannot taste-test a scaled-up raising-agent ratio or
confirm a pan-fried egg dish holds up at 8 servings — that is exactly the
"real kitchen testing" the pack has flagged as outstanding since Phase 1
(`03_WORKING_PROTOTYPE/PROTOTYPE_STATUS.md`, `02_RECIPE_CONTENT/
README_RECIPE_CONTENT.md`: *"a structured/generated recipe record is not
automatically equivalent to a kitchen-tested published recipe"*). Declaring
those 415 recipes launch-ready without that testing would be exactly the
kind of unsafe/misleading claim this gate exists to prevent. Holding them —
visibly, with the specific scaling categories named — is the correct
outcome, not an incomplete one.

## No unsafe or misleading dietary claims

Carried forward from Phase 2.1 and unchanged by this phase:

- The GF/DF-adaptable and full-taxonomy claim language
  (`DIETARY_CLAIM_LANGUAGE.md`, `PHASE_2_1_TAXONOMY_AND_LANGUAGE_FREEZE.md`)
  never equates "adaptable"/"compatible" with a certification or allergy-safety
  guarantee.
- Every `MEETS` classification from Phase 2.4 is gated by the Launch Rule —
  `public_suitability_state` shows `UNVERIFIED` instead of `MEETS` until a
  human reviewer signs off (`reviewed: true`), which hasn't happened yet.
  Nothing in this recipe bank makes a live "meets your requirement" claim
  today; everything defaults to the conservative, honest state.
- The working prototype's disclaimer banner and per-recipe GF/DF badges are
  live in `03_WORKING_PROTOTYPE/index.html` (verified rendering in Part 1 of
  this build).

## Gate status

**GREEN**, on the terms an automated QA pass can actually deliver: the
launch/hold split is drawn honestly and visibly (not guessed), reasons are
specific and traceable to the original QA screen, every recipe has a
dietary classification, and the frozen claim language is live in the UI.
The 415-recipe kitchen-test queue remains open human work — tracked, not
hidden — before those recipes can move from `HELD_FOR_KITCHEN_TEST` to
`LAUNCH_READY`.

This closes Phase 2 (all sub-phases 2.1–2.8 GREEN). Next per
`CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md`: **Phase 3 — Authoritative GitHub
Production Repository & Protection.**
