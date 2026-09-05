# Ingredient Dietary Attribute Codes (Phase 2.2)

Defines the `attribute_code`/`attribute_value`/`evidence_state` vocabulary
stored per ingredient in `ingredient_dietary_attributes`
(`04_PRODUCTION_STARTER/schema/002_dietary_requirements.sql`). The column is
free text in the schema (no fixed enum), so this file — not a database
constraint — is the source of truth for which codes exist and what they mean.
That open-ended design is also what satisfies the "custom attribute
extension" requirement from `DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md`
Phase 2.2: a new code can be added here and used immediately without a schema
migration.

## Evidence states (reused from `DIETARY_TAXONOMY.json`)

- `VERIFIED_PRESENT` — the attribute is true, and true independent of brand
  (a generic pantry ingredient's structural identity, e.g. "chicken" is
  poultry, or a directly-named allergen source, e.g. "milk" declares the milk
  allergen).
- `VERIFIED_ABSENT` — the attribute is confidently false for the same reason.
- `CONDITIONAL` — the true/false answer depends on something this record
  can't resolve alone: which side of an "X or Y" recipe alternative the
  household picks, or which specific branded product they use for an
  ingredient whose generic form commonly (but not always) carries the
  attribute. `attribute_value` is `"depends_on_choice"` for the first case and
  the conventional/likely value for the second; `notes` always explains which.
- `UNVERIFIED` — not enough evidence to say either way (e.g. "stock" with no
  stated type). Per `RECIPE_SUITABILITY_STATE_CONTRACT.md`, UNVERIFIED
  outranks a reassuring guess.

**None of `VERIFIED_PRESENT`/`VERIFIED_ABSENT` here certify a specific
packaged product.** They certify what is true about the generic ingredient
*as named in this recipe bank* (plain "milk", plain "chicken" — no brands).
A household substituting a specific branded product still needs to check
that product's label — this table doesn't and can't do that for them. See
`PHASE_2_1_TAXONOMY_AND_LANGUAGE_FREEZE.md` for the frozen wording that
keeps this distinction visible in the product.

## Structural / compositional attribute codes

| Code | Meaning |
|---|---|
| `ANIMAL_DERIVED` | Contains any animal-derived component (meat, fish, dairy, egg, honey). Primary signal for VEGAN/VEGETARIAN/PESCATARIAN. Required on every ingredient record — see "Completeness rule" below. |
| `MEAT_BEEF` | Contains beef. |
| `MEAT_PORK` | Contains pork. |
| `POULTRY` | Contains poultry (chicken, etc.). |
| `FISH` | Contains fish. |
| `SHELLFISH_CRUSTACEAN` | Contains crustacean shellfish. |
| `SHELLFISH_MOLLUSC` | Contains molluscan shellfish. |
| `DAIRY_MILK` | Contains milk/dairy. |
| `EGG` | Contains egg. |
| `HONEY_BEE_DERIVED` | Contains honey or another bee-derived ingredient (relevant to VEGAN, not VEGETARIAN). |
| `ALCOHOL_CONTENT` | Contains alcohol (e.g. vanilla extract). |
| `GLUTEN_CEREAL_WHEAT` / `GLUTEN_CEREAL_BARLEY` / `GLUTEN_CEREAL_RYE` | Contains that gluten-containing cereal. |
| `GLUTEN_CEREAL_OATS` | Contains oats. Kept separate from the other cereals per the Australian claim boundary in `REFERENCE_SOURCES.md` — presence of oats never implies a gluten-free claim on its own. |
| `HIDDEN_SOURCE_RISK` | General-purpose flag for a specific hidden-allergen pattern not covered by a more specific code above; always `CONDITIONAL`/`UNVERIFIED` with an explanatory note (this catalogue mostly uses the specific allergen code instead, e.g. `ALLERGEN_SESAME` on `hummus`, and reserves this generic code for cases that don't fit an existing allergen). |
| `CAFFEINE_CONTENT` | Contains caffeine (coffee, or cocoa/chocolate's caffeine+theobromine). Added in v1.1 (Phase 2.4 addendum) to support `CAFFEINE_FREE`. |
| `ONION_CONTENT` / `GARLIC_CONTENT` | Contains onion / garlic. Added in v1.1 (Phase 2.4 addendum) to support `ONION_FREE`/`GARLIC_FREE`. Applied both as exact-match facts (e.g. `onion`, `creamy garlic sauce`) and as a generic `CONDITIONAL` flag on any ingredient in the `sauce` recipe group or the `Herbs/Spices` swap group that doesn't already have an explicit verdict -- bottled sauces and seasoning blends are a well-known common carrier of onion/garlic powder even when not named. |

## Allergen-declaration attribute codes

One per Australian allergen requirement in `DIETARY_TAXONOMY.json`'s
`allergen` class, so a Phase 2.4 recipe classification can join directly on
the suffix: `ALLERGEN_WHEAT`, `ALLERGEN_FISH`, `ALLERGEN_CRUSTACEAN`,
`ALLERGEN_MOLLUSC`, `ALLERGEN_EGG`, `ALLERGEN_MILK`, `ALLERGEN_LUPIN`,
`ALLERGEN_PEANUT`, `ALLERGEN_SOY`, `ALLERGEN_SESAME`, `ALLERGEN_ALMOND`,
`ALLERGEN_BRAZIL_NUT`, `ALLERGEN_CASHEW`, `ALLERGEN_HAZELNUT`,
`ALLERGEN_MACADAMIA`, `ALLERGEN_PECAN`, `ALLERGEN_PISTACHIO`,
`ALLERGEN_PINE_NUT`, `ALLERGEN_WALNUT`, `ALLERGEN_BARLEY`, `ALLERGEN_OATS`,
`ALLERGEN_RYE`, `ALLERGEN_SULPHITES`.

A row is only written when a code is identified as present or a plausible
hidden source for a given ingredient — **absence of a row is not a claim of
absence**. Only `ANIMAL_DERIVED` (and a small number of specific codes noted
inline, e.g. `DAIRY_MILK`/`ALLERGEN_MILK` on plain "milk") get an explicit
`VERIFIED_ABSENT` row, because those are the cross-cutting facts every
ethical/allergen check needs. This catalogue's tree-nut allergen codes
(almond, cashew, walnut, etc.) have zero data rows because no tree nut
appears anywhere in the 800-recipe V1 baseline — that is a fact about the
recipe bank, not a gap in the model; the codes exist and are ready the
moment a recipe introduces one. Coconut is explicitly noted as plant-derived
and is **not** a declared tree-nut allergen under FSANZ rules, so it
deliberately carries no `ALLERGEN_*` row.

## Completeness rule

Every ingredient record in `ingredient_dietary_attributes_v1.json` carries an
explicit `ANIMAL_DERIVED` row — `build_ingredient_dietary_attributes.py`
asserts this at build time and fails loudly if a new ingredient rule omits
it. This exists because the first draft of this model silently *didn't*
guarantee that (several ingredients, especially inside "butter or oil"-style
swap-flexible lines, had no `ANIMAL_DERIVED` opinion at all), which is
exactly the kind of gap Phase 2.2's own GREEN gate — expressing every locked
requirement class "without relying only on ingredient-name string matching"
— exists to catch. Caught and fixed during this build; kept as a standing
assertion so it can't silently regress.

## Interim keying

Records are keyed by `ingredient_key` (normalised ingredient text, e.g.
`"beef mince"`), not `ingredients.ingredient_id`, because canonical
ingredient IDs aren't assigned until Phase 4
(`01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md`). When Phase 4
assigns canonical IDs, re-key this file's records onto
`ingredients.ingredient_id` and load them into the
`ingredient_dietary_attributes` table as-is — the attribute_code/value/
evidence_state/notes shape already matches that table's columns.
