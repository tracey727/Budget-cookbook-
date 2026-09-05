# Phase 2.4 — Recipe Classification of all 800 Recipes

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 2.4.
Builds on the frozen taxonomy (2.1), ingredient attribute model (2.2, plus a
small v1.1 addendum made here), and household combination engine (2.3).

**GREEN gate (as written):** every launch recipe has a versioned
classification record for enabled requirement families or remains explicitly
`UNVERIFIED`.

## What this is

`build_recipe_requirement_assessments.py` audits all 800 recipes against
every taxonomy requirement code, using only the Phase 2.2 ingredient
attribute evidence — never a recipe's name, category, or meal type. Output
is `recipe_requirement_assessments_v1.json`: 800 recipes × 42 requirement
codes = **33,600 rows**, matching the shape of
`recipe_requirement_assessments` in `schema/002_dietary_requirements.sql`.

## Scope: which of the taxonomy's ~95 codes get a real row

The taxonomy (`DIETARY_TAXONOMY.json` v1.1) has 95 codes across 11 classes.
"Audit against each **applicable** requirement family" (the gate's own
wording) means deciding, honestly, which families an ingredient-level audit
can actually speak to:

- **42 codes get a real, computed per-recipe row**: all 3 ingredient-derivable
  ethical/lifestyle codes (`VEGETARIAN`, `VEGAN`, `PESCATARIAN`), all 23
  allergen codes, 6 gluten/cereal codes, 6 intolerance codes, and all 4
  religious/cultural codes. See `classified_requirement_codes` in the output
  file.
- **50 codes are blanket `UNVERIFIED`, out of scope for this phase** —
  documented once each in `blanket_unverified_requirement_codes` with a
  reason, *not* expanded into 800 identical rows:
  - `FLEXITARIAN_PREFERENCE`, `PLANT_FORWARD_PREFERENCE` — preference-level,
    no binary ingredient fact to classify against.
  - `PURE_OAT_CLINICIAN_PLAN` — needs a clinician-verified certified product.
  - `LOW_FODMAP_PROFESSIONAL_PLAN` — the master blueprint explicitly requires
    this to be a professional-plan mode, not a generic ingredient blacklist.
  - `LOW_SPICE` — a quantity/heat judgement, not an ingredient-presence fact.
  - All 10 `clinician_directed` targets (sodium, carbohydrate, energy, etc.) —
    this recipe bank has no nutrition data; none may be invented.
  - All 12 `texture_swallowing` codes (including the two added in Phase 2.1:
    `SAUCE_GRAVY_REQUIRED`, `MOISTURE_REQUIRED`) — texture/swallowing safety
    depends on preparation and serving conditions, not an ingredient list.
    That's Phase 2.7's gate, explicitly, not this one.
  - All 5 `life_stage` codes — needs an authoritative-guidance review this
    pack hasn't done yet (`MASTER_PRODUCT_BLUEPRINT.md` section H).
  - All 7 `sensory_preference` codes — preferences, not safety exclusions.
  - All 11 `practical` codes — logistical filters; freezer/lunchbox/one-pot
    are already direct fields on the V1 recipe records and handled by the
    existing prototype engine, not this table.
- **3 codes (`CUSTOM_EXCLUSION`/`CUSTOM_REQUIREMENT`/`CUSTOM_PREFERENCE`) are
  not applicable at all**, not even as a blanket row: they're open-ended
  per-household labels with no single fixed meaning, resolved at query time
  against a specific rule's `canonical_ingredient_id` — that's engine-runtime
  logic (closer to Phase 2.5), not a precomputed classification.

42 + 50 + 3 = 95, the full taxonomy. Nothing was silently dropped.

## Why `ADAPTABLE` is never assigned here

Every row is `MEETS`, `EXCLUDED`, or `UNVERIFIED` — never `ADAPTABLE`.
`ADAPTABLE` requires "one or more approved substitutions" per
`RECIPE_SUITABILITY_STATE_CONTRACT.md`, and substitution approval is Phase
2.5's job, not built yet. A recipe with wheat pasta that *could* become
`ADAPTABLE` via a gluten-free pasta swap is classified `EXCLUDED` for now —
accurate to what the system can currently back up — and Phase 2.5 is where
some of today's `EXCLUDED` rows should get promoted to `ADAPTABLE` once a
specific substitution is checked against every other selected household
member's hard exclusions (per the master blueprint's substitution rule).

## Notable modelling decisions

- **Vegetarian/vegan/pescatarian use a "flesh fallback", not just specific
  meat codes.** `"leftover roast meat"` and `"stock"` carry `ANIMAL_DERIVED`
  but no specific `MEAT_BEEF`/`POULTRY`/`FISH` code (the meat type isn't
  stated). Checking only the specific codes would have missed them entirely
  for a vegetarian audit. The evaluator falls back to `ANIMAL_DERIVED=true`
  whenever an ingredient carries no dairy/egg/honey (the animal-derived
  things vegetarians *do* eat) — so an unspecified roast or stock still
  correctly excludes a recipe from `VEGETARIAN`/`PESCATARIAN`, without
  needing a specific (and unknown) meat-type code.
- **Kosher and halal are modelled as genuinely different rules, not the same
  rule with a different label.** `GEN-RCP-0301` (Tomato Herb Chicken Pasta,
  chicken + cheese) comes out `KOSHER_COMPATIBLE: EXCLUDED` (meat-and-dairy
  in the same dish is a real, bedrock kosher rule this model can check
  directly) but `HALAL_COMPATIBLE: UNVERIFIED` (chicken itself isn't
  prohibited in Islam; what's unverifiable from generic ingredient text is
  the slaughter method, so the honest answer is "can't confirm", not
  "excluded"). Getting this distinction right — not treating "religious
  dietary rule" as one interchangeable bucket — was the point of building
  two separate evaluators instead of one.
  - Halal deliberately does **not** treat shellfish specially (most schools
    of Islamic jurisprudence permit it; there's a genuine, contested
    difference of opinion this model shouldn't silently resolve either way),
    while kosher does (shellfish is unambiguously excluded there).
- **Two v1.1 additions were needed to Phase 2.2's model to do this properly**:
  `CAFFEINE_FREE`/`ONION_FREE`/`GARLIC_FREE` had no ingredient attribute to
  read at all until this phase added `CAFFEINE_CONTENT`/`ONION_CONTENT`/
  `GARLIC_CONTENT` (see `PHASE_2_2_INGREDIENT_ATTRIBUTE_MODEL_REPORT.md`'s
  v1.1 addendum and `INGREDIENT_ATTRIBUTE_CODES.md`). Building Phase 2.4
  surfaced a real Phase 2.2 gap rather than working around it with a
  one-off string match at classification time.

## The Launch Rule, actually enforced

`DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md`: *"No dietary flag becomes a
public 'MEETS' claim ... until the Phase 2 dietary QA gate has reviewed the
relevant ingredient/recipe mapping. Unreviewed recipes remain UNVERIFIED for
that requirement."*

Every row from this automated pass is written with `reviewed: false` and
`review_source: "automated_ingredient_attribute_audit_v1 (Phase 2.4,
unreviewed)"`. Each row carries both:

- `suitability_state` — the raw computed candidate, for a human reviewer to
  work from.
- `public_suitability_state` — what the product may actually show: computed
  `EXCLUDED`/`UNVERIFIED` pass through unchanged (surfacing a real exclusion
  is never the "optimistic" claim the Launch Rule guards against), but a
  computed `MEETS` is downgraded to `UNVERIFIED` until a reviewer sets
  `reviewed: true`.

Aggregate result of applying that gate to this pass:

| | computed `suitability_state` | `public_suitability_state` |
|---|---:|---:|
| MEETS | 26,861 | 0 |
| EXCLUDED | 4,023 | 4,023 |
| UNVERIFIED | 2,716 | 29,577 |

Nothing is publicly claimed `MEETS` yet — by design, until Phase 2.4's
output gets a human review pass (tracked as follow-up work, not part of this
gate's own completion criteria, which only requires the classification
record to exist).

## Spot-checked examples

- `GEN-RCP-0001` (Banana Cinnamon Overnight Oats: oats, milk, banana,
  cinnamon, chia seeds) — `VEGETARIAN: MEETS`, `VEGAN: EXCLUDED` (milk),
  `ALLERGY_MILK: EXCLUDED`, `ALLERGY_EGG: MEETS`. Correct.
- `GEN-RCP-0301` (Tomato Herb Chicken Pasta: chicken, cheese, pasta, mixed
  vegetables, tomato herb sauce) — `VEGETARIAN`/`VEGAN`/`PESCATARIAN:
  EXCLUDED` (chicken), `ALLERGY_WHEAT`/`COELIAC_STRICT_GF: EXCLUDED` (pasta),
  `KOSHER_COMPATIBLE: EXCLUDED` (chicken+cheese), `HALAL_COMPATIBLE:
  UNVERIFIED` (slaughter method unverifiable), `PORK_FREE`/`BEEF_FREE:
  MEETS`. Correct and appropriately differentiated.
- `GEN-RCP-0551` (Banana Mini Muffins, using the swap-flexible `"self-raising
  flour or oats"` line) — `WHEAT_FREE`/`OAT_EXCLUDE`/`COELIAC_STRICT_GF: all
  UNVERIFIED`, explanation naming the swap-flexible ingredient rather than
  guessing which alternative was used. Correct.

## Gate status

**GREEN.** All 800 recipes have a versioned classification record
(`review_source` names this exact automated pass) for every requirement
family an ingredient-level audit can speak to, and every code this phase
cannot respons­ibly derive is either a documented blanket `UNVERIFIED` or an
explicitly-out-of-scope custom code — none silently missing. No unsafe or
misleading `MEETS` claim reaches the public state without a review step that
doesn't exist yet, which is the correct, conservative default.

Next: Phase 2.5 — Substitution Safety & Cost Recalculation (map approved
substitutions by function/dietary attribute, check them against every
selected household member's hard exclusions from Phase 2.3, and promote
today's `EXCLUDED` rows to `ADAPTABLE` where a safe substitution exists).
