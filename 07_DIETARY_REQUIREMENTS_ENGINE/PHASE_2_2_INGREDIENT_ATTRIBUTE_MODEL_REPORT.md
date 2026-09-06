# Phase 2.2 — Canonical Ingredient Dietary Attribute Model

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 2.2.
Builds on the frozen taxonomy from Phase 2.1
(`PHASE_2_1_TAXONOMY_AND_LANGUAGE_FREEZE.md`).

## What this is

`build_ingredient_dietary_attributes.py` classifies every one of the **151
distinct ingredient names** used across the 800-recipe V1 baseline's 3,840
ingredient lines, producing `ingredient_dietary_attributes_v1.json`: one
record per ingredient, each with a list of `{attribute_code, attribute_value,
evidence_state, notes, source_reference}` entries. The attribute vocabulary
is defined in `INGREDIENT_ATTRIBUTE_CODES.md`.

This is a **reviewed, offline classification**, not a runtime string
matcher. The GREEN gate for this phase requires the model to express every
locked requirement class "without relying only on ingredient-name string
matching" — the matching happens once, here, with a human-reviewed rule set
and explicit uncertainty where the ingredient name genuinely isn't enough
evidence. The production engine and Phase 2.4 recipe classification are
meant to read `attribute_code`/`evidence_state` pairs from this table, not
re-derive them from ingredient text at request time.

## Results

- 151 ingredients, 268 attribute records: 189 `VERIFIED_PRESENT`/`VERIFIED_ABSENT`, 78 `CONDITIONAL`, 1 `UNVERIFIED`.
- Every ingredient has an explicit `ANIMAL_DERIVED` determination (enforced
  by an assertion in the build script — see below for why that needed
  enforcing).
- 25 ingredient lines are "X or Y" swap-flexible text (e.g. `"butter or
  oil"`, `"honey or syrup"`, `"peanut or seed butter"`) rather than a single
  ingredient. Where the two alternatives disagree on an attribute, the
  record is `CONDITIONAL` with both alternatives' values spelled out in
  `notes` — the household's actual choice decides the outcome, and this
  model refuses to silently pick one side.

## Defects found and fixed during this build

Building this model surfaced real bugs in the classifier itself, not just in
the data — worth recording because they're the exact failure mode Phase 2.2
exists to prevent:

1. **Missing `ANIMAL_DERIVED` on several ingredients.** The first pass only
   emitted a default "no animal-derived component" row for ingredients with
   *no* explicit rule; any ingredient with *some* rule (e.g. `"peanut"` had
   an `ALLERGEN_PEANUT` rule) got no `ANIMAL_DERIVED` opinion at all unless
   one was written by hand. This silently broke `"butter or oil"`,
   `"oil or butter"`, `"oil or melted butter"`, and several sauce/condiment
   entries — all resolved to a false "no animal-derived ingredient" default
   because *neither side* of the merge had an `ANIMAL_DERIVED` value to
   disagree on, even though butter plainly is dairy. Fixed by giving every
   sub-term used inside a compound (`butter`, `melted butter`, `plant
   spread`, `oil`, `syrup`, `water`, `brown sugar`, `seed butter`, `oats`)
   its own explicit rule, backfilling `ANIMAL_DERIVED` on every other
   `EXACT_RULES` entry that lacked one, and adding a build-time assertion
   that fails the build if any ingredient rule is added in future without
   an `ANIMAL_DERIVED` value.
2. **`coconut milk` naive string-match risk.** Named "milk" but is plant-derived.
   Handled with an explicit exact-match rule ahead of any generic "contains
   milk" pattern, specifically called out in the code comment so a future
   editor doesn't undo it by generalising the milk rule.
3. **`couscous` is not a plain grain.** It's made from wheat semolina —
   flagged `ALLERGEN_WHEAT`/`GLUTEN_CEREAL_WHEAT` `VERIFIED_PRESENT` rather
   than left unflagged like rice.
4. **Misused attribute code for an unknown meat type.** `"leftover roast
   meat"` initially coded `MEAT_BEEF: unspecified/UNVERIFIED`, which
   misuses a specific-meat code to express general uncertainty. Fixed to
   leave `MEAT_BEEF`/`MEAT_PORK`/`POULTRY` unset (not falsely populated) and
   carry the uncertainty as a note on `ANIMAL_DERIVED` instead.

## Hidden-source flags worth highlighting

These are ingredients whose plain recipe-bank name doesn't reveal a common
real-world allergen/animal source — the kind of gap Phase 2.4's
per-recipe classification needs to inherit rather than re-discover:

- `hummus` → sesame (tahini), not named.
- `pesto veg sauce` → dairy (parmesan) and pine nuts, not named.
- `mild curry powder or paste` / `mild curry sauce` → some commercial pastes
  contain shrimp paste.
- `bbq sauce` / `bbq tomato sauce` → some commercial versions contain
  Worcestershire sauce (anchovy).
- `soy garlic sauce` / `honey soy sauce` / `teriyaki sauce` → traditional soy
  sauce is wheat-brewed (tamari is the wheat-free alternative).
- `chocolate` / `choc chip` → milk chocolate is common; soy lecithin is a
  common emulsifier.
- `caramel` → traditionally butter/cream-based.
- `vanilla` → extract is conventionally alcohol-based.
- `sultana` / `sultana oat` → dried fruit is commonly sulphured (220).
- `stock` → chicken/beef/vegetable not specified by the recipe; the only
  ingredient left `UNVERIFIED` rather than a best-guess `CONDITIONAL`,
  because there's no default worth guessing for a vegetarian/vegan check.
- The bread family (`bread`, `bread rolls`, `english muffins`, `pita bread`,
  `wraps`) → commercial versions commonly contain milk powder or an egg
  glaze not implied by the plain name.

None of these are claims that the ingredient *is* unsafe — they're the
`CONDITIONAL`/`UNVERIFIED` signal this model exists to produce instead of a
false-confident guess, per the "UNVERIFIED outranks optimism" rule in
`RECIPE_SUITABILITY_STATE_CONTRACT.md`.

## What this model does not cover (by design, not oversight)

- **Cross-contact / "may contain" precautionary statements.** These are
  facility- and batch-specific, not derivable from an ingredient's generic
  identity. A recipe using "milk" gets `ALLERGEN_MILK: VERIFIED_PRESENT`
  (the milk itself), never a claim about cross-contact for another allergen.
- **Specific branded products.** Every ingredient in this recipe bank is
  written generically ("milk", "chicken", "plain flour") — there is no
  product/brand attached, so `VERIFIED_PRESENT`/`VERIFIED_ABSENT` describe
  the generic ingredient as named, not any specific SKU a household might
  actually buy. See `INGREDIENT_ATTRIBUTE_CODES.md`'s evidence-state
  definitions for this boundary.
- **Tree nuts, lupin, molluscs/crustaceans, most clinician-directed
  attributes.** Zero data rows because none of these appear in the V1
  recipe bank at all — the attribute codes exist and are ready in
  `INGREDIENT_ATTRIBUTE_CODES.md`, they simply have nothing to attach to
  yet. Confirmed by grepping the full distinct-ingredient list, not assumed.

## Interim keying (carries forward into Phase 4/5)

Records are keyed by `ingredient_key` (normalised ingredient text), not a
canonical UUID — canonical ingredient IDs aren't assigned until Phase 4.
Phase 4/5 must re-key this file's records onto `ingredients.ingredient_id`
(schema/001_initial_schema.sql) and load them into
`ingredient_dietary_attributes` (schema/002_dietary_requirements.sql); the
attribute_code/value/evidence_state/notes shape already matches that table's
columns, so this is a re-keying exercise, not a re-classification.

## v1.1 addendum (added during Phase 2.4)

Phase 2.4 (recipe classification) needed `CAFFEINE_FREE`/`ONION_FREE`/
`GARLIC_FREE` derived from real ingredient evidence rather than skipped, so
this model gained three attribute codes: `CAFFEINE_CONTENT` (coffee;
chocolate/choc chip/cocoa oat as `CONDITIONAL`), `ONION_CONTENT` and
`GARLIC_CONTENT` (direct matches like `onion`, `creamy garlic sauce`, `soy
garlic sauce`, plus a generic `CONDITIONAL` flag applied to any ingredient in
the `sauce` recipe group or `Herbs/Spices` swap group that lacked an explicit
verdict — see `PHASE_2_4_RECIPE_CLASSIFICATION_REPORT.md` and
`INGREDIENT_ATTRIBUTE_CODES.md`). 71 new attribute records; the build-time
`ANIMAL_DERIVED` completeness assertion still passes.

## Gate status

**GREEN** for the model itself: every locked requirement class (ethical,
allergen, gluten/cereal, intolerance, religious/cultural, alcohol) can now be
expressed for at least one real ingredient in this catalogue via
`attribute_code`/`evidence_state` pairs, not string matching, and the
classification underneath those pairs has been reviewed and had its own
defects fixed (not merely generated once and trusted). Phase 2.2 does not
require every ingredient to have full allergen coverage — it requires the
*model* to be able to express it, which it now demonstrably does (peanut,
egg, milk, wheat, oats, fish, sesame, sulphites, and soy are all represented
with real data; tree nuts/lupin/shellfish have the codes ready with no data
because none occur in this recipe bank).

Next: Phase 2.3 — Household Member Requirement Model (the schema already
exists in `002_dietary_requirements.sql`; this phase is about the product/
API surface for creating and combining member profiles), followed by Phase
2.4 — classify all 800 recipes against this attribute table.
