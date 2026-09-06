# Phase 2.5 — Substitution Safety & Cost Recalculation

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 2.5.
Builds on the frozen taxonomy (2.1), ingredient attribute model (2.2),
household combination engine (2.3), and recipe classification (2.4).

**GREEN gate (as written):** every displayed adaptation changes both the
ingredient list and the affordability calculation.

## What this is

`04_PRODUCTION_STARTER/src/dietary/substitution.ts` implements the
blueprint's substitution rule end to end:

1. **`substitutionCatalogue.ts`** maps every V1 prototype swap group (the
   "function" a substitution must serve — `Milk`, `Cooking Fat`, `Flour`,
   `Dinner Protein`, etc., taken as-is from `03_WORKING_PROTOTYPE/data.js`'s
   own `swapMap`, not reinvented) to dietary attributes for each of its 117
   substitute options — 66 aliased onto the Phase 2.2 ingredient table where
   the option is the same generic ingredient already reviewed, 51 classified
   fresh where it's a genuinely new product (GF flour/pasta/bread, plant
   milks, nut-free butters, `Certified GF oats`, etc.).
2. **`evaluateSubstitute`/`findSafeSubstitute`** check a candidate substitute
   against every `HARD_EXCLUDE` entry in a household's *combined* requirement
   set from Phase 2.3 — not one member at a time — and only call a candidate
   safe if it clears every one of them. A `CONDITIONAL`/`UNVERIFIED` violation
   still disqualifies a candidate from being called "safe" (the same
   UNVERIFIED-outranks-optimism principle as every other phase).
3. **`recalculateAdaptedCost`** prices the substitute's own required quantity,
   never the original ingredient's price.
4. **`adaptRecipeIngredient`** ties it together into one `Adaptation` object
   that always carries both `ingredientChange` (from → to) and `costChange`
   (original priced line → adapted priced line) — the GREEN gate's
   requirement is enforced by the return type itself, not left to a caller
   to remember to show both.

## The two-constraint case this whole phase exists for

DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md's household example (Member A:
vegetarian + lactose avoidance; Member C: peanut allergy) only gets
interesting once you ask: *what happens when the swap that fixes one
member's requirement introduces a new violation for another member?*
Verified directly in `substitution.test.ts`:

- A household with both `DAIRY_FREE` and a soy allergy correctly **skips
  "Soy milk"** (the obvious dairy-free swap) and still finds a different
  safe plant milk — proving the search checks a candidate against the whole
  combined hard-exclusion set, not just the one requirement being adapted
  for.
- A peanut-only allergy (no other allergy) is **not** over-broadened into
  rejecting every nut/seed butter — it correctly accepts "Sunflower seed
  butter" as safe rather than treating "nut allergy" as a single undifferentiated
  bucket.
- A household excluding dairy, soy, almond, *and* oats still finds
  **"Coconut drink"** as the one clean option left in the `Milk` group —
  the search doesn't give up just because most of a swap group is unsafe;
  it keeps looking.
- When *no* clean option exists, `findSafeSubstitute` returns `safe: null`
  with the blocking candidates listed (split into definitely-unsafe vs.
  uncertain) rather than silently picking the least-bad option — and
  `adaptRecipeIngredient` turns that into an explicit `EXCLUDED`/`UNVERIFIED`
  result, never silence.

## Resolving Phase 2.4's `UNVERIFIED` oats cases

Phase 2.4 correctly left every oats-containing recipe `UNVERIFIED` for
`COELIAC_STRICT_GF` (per the Australian gluten-free-oats claim boundary —
plain oats are never assumed coeliac-safe). This phase is where that
actually gets resolved: `"Certified GF oats"` carries a new
`OAT_GF_CERTIFIED` attribute, and `coeliacStyleViolation()` treats an
oats-containing ingredient as clear *only* when that specific certified
product is used — plain `"Rolled oats"`/`"Quick oats"` still correctly fail.
Verified in the test suite: a coeliac-strict household asking for an
`Oats/Breakfast Grain` substitute gets `"Certified GF oats"` specifically,
not the first oat option in the list.

## A gap this phase's own alias-integrity check caught

Wiring up the alias table (`INGREDIENT_KEY_ALIASES`) surfaced a real bug: two
swap options, `"Butter"` and `"Plant spread"`, were aliased to `"butter"`/
`"plant spread"` in `ingredient_dietary_attributes_v1.json` — but those keys
don't actually exist there. They're internal sub-terms
`build_ingredient_dietary_attributes.py` uses only to decompose "X or Y"
compound lines like `"butter or oil"`; they never got a standalone row in
the output JSON because no recipe ever lists `"butter"` by itself. Caught by
a script that checks every alias target actually resolves (67 → 66 aliases,
2 moved to direct entries) before it could silently return "no attributes
known" for a real, common swap option. Fixed by restating both directly in
`SUBSTITUTE_ONLY_ATTRIBUTES` with the exact values the Python script already
uses internally, and a second check confirmed all 117 substitute names
across all 20 swap groups now resolve to something.

## The `LACTOSE_CONTENT` fix this phase required in Phase 2.2

Building the `Milk` swap group surfaced the reason `LACTOSE_CONTENT` needed
to be its own attribute (not folded into `DAIRY_MILK`, as Phase 2.4
originally did): `"Lactose-free milk"` is a real, common substitute option
that is `DAIRY_MILK=true` (still carries the milk allergen) but
`LACTOSE_CONTENT=false`. Without the split, a `LACTOSE_FREE` household would
either wrongly reject a genuinely lactose-free product, or a `DAIRY_FREE`
household could wrongly accept a product that still isn't dairy-free. Made
as a small v1.2 addendum to `ingredient_dietary_attributes_v1.json`
(mirroring `DAIRY_MILK` on every existing dairy ingredient, since the base
recipe bank only ever names ordinary dairy) and Phase 2.4's `LACTOSE_FREE`
evaluator was repointed at it — re-running that script produced byte-identical
recipe classification counts, confirming the change only sharpens the model
for substitutes, without altering any of the 800 recipes' existing verdicts.

## What this phase does not cover

- **Custom rules** (`CUSTOM_EXCLUSION`/etc.) are not attribute-checkable —
  `evaluateSubstitute` explicitly skips any combined-requirement entry keyed
  `CUSTOM:...`, documented in code and exercised in the test suite (a
  household's "no coconut" custom rule does not block "Coconut drink" from
  being offered). Resolving these needs matching against a rule's
  `canonical_ingredient_id`, which requires the canonical ingredient IDs
  Phase 4 hasn't assigned yet — a real, stated limitation, not a silent one.
- **`HALAL_COMPATIBLE`/`KOSHER_COMPATIBLE`** are checked here only for their
  single-ingredient-derivable parts (pork/shellfish presence on the
  *substitute itself*) — the meat-and-dairy *combination* rule Phase 2.4
  applies is a whole-recipe property, not something one substitute
  ingredient can violate on its own, so it's intentionally out of scope here.
- **Pantry-first pricing**: a substitute is priced as a full shortage
  (`recalculateAdaptedCost` assumes zero pantry stock of it), matching that a
  household is unlikely to already stock an ingredient it wasn't previously
  using. A live engine tracking pantry-by-canonical-ingredient (Phase 9)
  would reduce this the same way it does for any other ingredient.
- **Promoting Phase 2.4's stored `EXCLUDED` rows to `ADAPTABLE`**: this
  module computes adaptations at query time (they depend on which household
  is asking), so `recipe_requirement_assessments_v1.json` is not rewritten —
  Phase 7's production API is where a live "adapted view" of a Phase 2.4 row
  would call this module and combine the two.

## Gate status

**GREEN.** `Adaptation` structurally cannot report a change without both an
ingredient-list change and a cost change; the substitution search verifiably
respects every selected household member's hard exclusions at once (not
whoever asked); and the AU oats claim boundary Phase 2.1 froze and Phase 2.4
left `UNVERIFIED` now has a real, checkable path to resolution via a specific
verified product. 29 checks pass in total: 12 from `test:dietary` (Phase
2.3, unchanged) plus 17 new ones in `test:substitution`
(`npm run test:substitution`).

Next: Phase 2.6 — Medical / Professional-Plan Boundaries.
