# Dietary-Claim Language — FROZEN (Phase 2, item 5)

This wording is locked for the V1 launch. Do not change the meaning of
`gfAdaptable` / `dfAdaptable` without a new versioned decision recorded here.

## What the badges mean

**"GF adaptable" / "DF adaptable" (`gfAdaptable`/`dfAdaptable: Yes`)**
means: the recipe's core structure can be made gluten-free or dairy-free by
swapping one or more flagged ingredients for a suitable alternative (per the
swap groups in `swapMap`).

It does **not** mean:
- the recipe as written, with its default ingredients, is gluten-free or
  dairy-free;
- any specific packaged product referenced or substituted is free of gluten
  or dairy;
- the dish is safe for coeliac disease, a diagnosed allergy, or any other
  medical condition;
- the kitchen, pantry, or any packaged ingredient is free of
  cross-contamination.

**"GF adaptable" / "DF adaptable: No"** means no reasonable single-swap
adaptation was identified for this recipe in V1 — not that no adaptation is
theoretically possible.

## Required user-facing disclaimer text

Shown once as a persistent banner on the main app screen, and again next to
every GF/DF badge on a recipe detail view:

> **Adaptable, not allergen-safe.** GF/DF badges mean this recipe's
> structure can usually be adapted with an ingredient swap — they are not a
> guarantee that any specific product is gluten-free, dairy-free, or safe
> for a diagnosed allergy or coeliac disease. Always check packaged product
> labels yourself.

## Rationale

This matches `MASTER_PRODUCT_BLUEPRINT.md` rule 8 ("GF/DF adaptable means
the structure can be adapted, not that every listed packaged product is
allergen-safe") and the non-goal in section 8 ("guaranteed allergen
safety"). It keeps the product in the "adaptation suggestion" space rather
than making a food-safety claim the recipe bank has not been reviewed
against.
