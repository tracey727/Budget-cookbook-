# Phase 2 Recipe/Content QA Report — V1 800-recipe baseline

Automated screen only. Produces the review queue this gate needs; it does not replace culinary/kitchen-tested sign-off. See `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 2 for the full gate.

Recipes scanned: **800**

## 1. Duplicate / near-duplicate names

No exact duplicate recipe names found.

Families with more than 12 recipes (review for repetitive/near-duplicate variants within the family): 25
- Dinner/Tea / "pasta dinners" — 50 recipes
- Dinner/Tea / "curries & rice" — 50 recipes
- Dinner/Tea / "stir-fries & noodles" — 50 recipes
- Dinner/Tea / "tray bakes" — 50 recipes
- Dinner/Tea / "casseroles & bakes" — 50 recipes
- Breakfast / "overnight oats" — 30 recipes
- Breakfast / "pancakes" — 30 recipes
- Breakfast / "egg breakfasts" — 30 recipes
- Breakfast / "breakfast breads" — 30 recipes
- Breakfast / "breakfast baking" — 30 recipes
- Lunch / "wraps & sandwiches" — 30 recipes
- Lunch / "lunch bowls" — 30 recipes
- Lunch / "soups" — 30 recipes
- Lunch / "loaded potatoes" — 30 recipes
- Lunch / "salads & pasta salads" — 30 recipes
- Dessert / "fruit crumbles" — 30 recipes
- Dessert / "puddings" — 30 recipes
- Dessert / "slices & brownies" — 30 recipes
- Dessert / "cakes & cupcakes" — 30 recipes
- Snack / "snack baking" — 25 recipes
- Snack / "fruit snacks" — 25 recipes
- Snack / "bars & bites" — 25 recipes
- Snack / "savoury snacks" — 25 recipes
- Baking/Side / "breads & scones" — 15 recipes
- Baking/Side / "vegetable sides" — 15 recipes

Spot-check (`build_recipe_bank.py` generates these families by combining a flavour/sauce variant with a protein, e.g. "Tomato Herb Chicken Pasta", "Creamy Garlic Chicken Pasta") confirms these are deliberate templated variants, not accidental duplicates. They still need a human read for whether every flavour × protein combination is actually a distinct, sensible dish (Phase 2 item 1) — the generator pattern alone doesn't prove that.

## 2. Method / timing sanity

Flags: 0

## 3. Quantity realism screen (per-serve, base-serves=4 baseline)

Flags: 0

## 4. High-risk scaling categories (eggs, raising agents, strong spices, pan oil/fat, cans/packs)

415 of 800 recipes contain at least one ingredient in a category the blueprint says must not be scaled by blind multiplication (MASTER_PRODUCT_BLUEPRINT.md rule 7). These need an explicit non-linear scaling rule in Phase 8 (engine productionisation), not necessarily a content rewrite now.

- Cooking Fat: 335 recipes
- Egg: 205 recipes
- Herbs/Spices: 115 recipes
- Raising Agent: 30 recipes
- Cans/packs: 10 recipes

## 5. GF/DF adaptable vs allergen-safe language — FROZEN

See `DIETARY_CLAIM_LANGUAGE.md` in this folder for the frozen wording. Summary: `gfAdaptable`/`dfAdaptable: Yes` means the recipe **structure** can be made GF/DF by swapping the flagged ingredient(s); it is never an allergen-safety, cross-contamination or certified-free claim.

## 6. Allergen/adaptation disclaimer in product UX

Added to the working prototype (`03_WORKING_PROTOTYPE/index.html`) as a persistent banner, and repeated on every recipe detail view next to the GF/DF badges.

## 7. Recipes requiring real kitchen testing before public launch

415 recipes are queued for human kitchen-testing / culinary review before launch, because they hit a high-risk scaling category, a method/timing flag, or a quantity-realism flag above. This list is a screening aid, not a completed review — an AI text pass cannot certify a recipe as kitchen-tested.

Full ID list is in `phase2_qa_flags.json` (`kitchen_test_queue`) to keep this report readable.

## Gate status

**NOT GREEN.** The automatable parts of Phase 2 (duplicate screen, timing/quantity screen, high-risk scaling inventory, frozen dietary-claim language, UX disclaimer) are done. Items 3 and 7 of the phase — realistic-quantity judgement calls and kitchen-testing sign-off — need a human reviewer with the flagged queue above before this phase can be marked GREEN and Phase 3 (production repository) proceeds with launch-ready content.
