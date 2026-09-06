# Phase 4 — Canonical Ingredient, Unit & Pack Model

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 4.

**GREEN gate (as written):** every launch ingredient converts
deterministically or is explicitly marked manual-only; no incompatible
units are silently compared.

## 1. Canonical ingredient IDs

`build_canonical_ingredients.py` assigns every one of the 151 distinct V1
ingredients a stable `ingredient_id` — a UUIDv5 derived from a fixed
namespace and the ingredient's `ingredient_key` (the same key Phase 2.2's
`ingredient_dietary_attributes_v1.json` and Phase 2.4/2.5's tables use).
Re-running the script reproduces identical IDs. **This is the canonical
ingredient ID** every interim `ingredient_key`-keyed table from Phase 2
should be re-keyed onto — see `canonical_ingredients_v1.json`'s `keying`
field and each Phase 2 report's own "interim keying" note.

## 2. Canonical quantity dimensions

Every ingredient is classified by the units its recipe lines actually use:

- **MASS** (`g`, `kg`) — canonical unit `g`.
- **VOLUME** (`cup`, `tbsp`, `tsp`) — canonical unit `mL`.
- **COUNT** (`each`, `large`) — canonical unit `each`.
- **MANUAL** — the ingredient's recipe lines mix units across dimensions, or
  use a context-dependent unit (`serve`, `cup cooked`, `cup dry`) that has no
  fixed universal conversion. **31 of the 151 ingredients are MANUAL** —
  documented explicitly in `canonical_ingredients_v1.json`, not silently
  defaulted to whichever unit happened to be picked. Examples: `egg` (`cup`,
  `each`, `g` all appear across different recipes), `potato` (`cup`, `cup
  cooked`, `g`, `kg`, `large`), `rice` (`cup`, `cup cooked`, `cup dry`).

This directly satisfies "no incompatible units are silently compared":
`potato` in cup form and `potato` in kg form are never treated as the same
number just because they share an ingredient name.

## 3. Unit conversion table

`unit_conversions_v1.json` has two kinds of row, and the difference is load-bearing:

- **Universal, `verified: true`** (8 rows): `kg↔g`, `cup↔mL`, `tbsp↔mL`,
  `tsp↔mL`. These are true by definition of the units — 1 Australian
  tablespoon is 20 mL regardless of what's in it (**not** the US 15 mL
  tablespoon; this product is AU-scoped per `REFERENCE_SOURCES.md`).
- **Ingredient-specific, `verified: false`** (6 rows): a density/yield
  reference average (e.g. chopped broccoli ≈ 90 g/cup; 1 cup dry rice ≈ 3
  cups cooked) that varies by real product and preparation. Always paired
  with a note saying so. Provided only where the reference value is
  well-established culinary knowledge (produce cup weights, dry:cooked
  grain/pasta yields) — deliberately **not** provided for protein/produce
  items whose "cup" weight depends heavily on preparation state (raw/
  cooked/canned/diced/whole: `beans`, `chicken`, `beef mince`, `chickpeas`,
  `lentils`, `tuna`). Those stay `MANUAL` rather than getting a
  confident-looking number this model can't actually back up — the same
  "don't invent it" discipline the dietary engine applies to prices and
  therapeutic targets, applied here to physical conversions.

`verified: false` is not a defect — a reference average is legitimately
useful for a shopping-list estimate — but the field means the production
engine (Phase 10) must never present it with the same certainty as a
`verified: true` metric-definition conversion, and a future content review
can replace it with a lab/label-sourced value without changing the schema.

## 4. Recipe quantity vs. retail pack quantity

A recipe's ingredient line (e.g. "2 cup rolled oats") and the pack a
household actually buys (e.g. a 1 kg bag) are different quantities in
different units, and the blueprint requires keeping them distinct rather
than conflating "how much the recipe needs" with "how much you can buy."
This model provides the **conversion machinery** (unit dimensions +
conversion table above) that a pack-quantity calculation needs, but
deliberately does **not** assign real-world retail pack sizes/prices to
ingredients in this phase — the same boundary
`MASTER_PRODUCT_BLUEPRINT.md` rule 1 draws for prices ("never invent
missing food prices") applies to pack sizes too: a "1 kg bag" default for
every flour-like ingredient would be a guess dressed up as a fact. Assigning
real pack options is Phase 10's content task (retail pack conversion & real
shopping math), building on this phase's conversion table.

## 5. Pack rounding rule

Defined once, for Phase 10 to use: **a household can only buy whole packs.**
Given a shortage quantity in canonical units and a specific pack's size in
the same canonical units, the number of packs to buy is
`ceil(shortage_qty / pack_qty)` — round up, never down, never a fraction.
Implemented as a pure function in
`04_PRODUCTION_STARTER/src/canonical/units.ts` (`packsNeeded`), with tests
confirming it never under-rounds (a shortage of exactly one pack needs 1
pack, not 0.99) and never returns a fractional pack count.

## 6. Mapping the 187 ingredient/unit pantry/price keys

Every one of the V1 prototype's 187 `ingredientUnitPairs` (the pantry/price
entry keys, e.g. `"milk|cup"`) decomposes into an `ingredient_key` already
present in `canonical_ingredients_v1.json` and a `unit` already covered by
either a universal conversion or an explicit `MANUAL` designation — there is
no orphaned key. Verified by `verify_ingredient_unit_pair_coverage.py`.

## Gate status

**GREEN.** Every one of the 151 launch ingredients has an explicit,
recorded quantity dimension: 120 convert deterministically within that
dimension (5 MASS, 114 VOLUME, 1 COUNT), and the other 31 are explicitly
`MANUAL` rather than guessed into a false canonical unit. No unit
comparison in this model is silent — every conversion or its absence is a
recorded, inspectable fact.

Next: Phase 5 — Neon Database Foundation (needs a real Neon project —
this is an infrastructure decision for the repository owner, not something
to provision unilaterally).
