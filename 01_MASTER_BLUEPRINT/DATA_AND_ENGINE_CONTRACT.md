# Data + Decision Engine Contract

## Stable IDs
Recipe IDs in the V1 source baseline are immutable identifiers. Production migrations may add canonical ingredient IDs, but must not silently renumber recipes.

## Core entities
- `recipes`
- `ingredients`
- `recipe_ingredients`
- `swap_groups`
- `swap_options`
- `unit_conversions`
- `households`
- `pantry_items`
- `price_book_items`
- `meal_plans`
- `meal_plan_items`
- `shopping_lists`
- `shopping_list_items`
- `favourites`
- `subscriptions`
- `audit_events`

## Quantities
Three concepts must never be conflated:
1. **Recipe requirement** — amount needed to cook.
2. **Pantry on-hand** — amount already available.
3. **Retail purchase** — whole pack(s) bought.

Production must perform canonical-unit conversion before subtraction/comparison.

## Cost concepts
- `consumption_cost`: value of quantity actually used.
- `missing_ingredient_cost`: estimated cost of shortages using unit price.
- `basket_outlay`: actual amount spent buying whole packs.

The UI must label these distinctly.

## Pricing confidence states
- `UNPRICED` — required shortage exists without valid price.
- `PRICED_USER` — price supplied by user.
- `PRICED_VERIFIED_SOURCE` — future approved source.
- `STALE` — price older than configured threshold.

No affordability claim while any required shortage is `UNPRICED`.

## Scaling rules
Default:
`scaled_qty = base_qty × target_serves / base_serves`

Special handling:
- count/eggs: practical whole-number rule;
- cans/packs: separate cook quantity from shopping packs;
- salt/pepper/strong spice: taste-sensitive caps/prompts;
- pan oil: process quantity, not fully linear;
- raising agents: household-range scaling only unless recipe batch is tested.

## Ranking V1 compatibility
Keep the V1 ranking available as a deterministic baseline:
- pantry coverage = 60;
- affordability = 30;
- missing-line bonus = 10.

Production may add secondary signals (prep time, leftovers, use-soon, user favourites), but they must not erase the explanation of why a recipe is ranked.

## Data minimisation
Do not store raw payment card information. Do not collect health/medical details just to operate a cookbook. Dietary preferences should be treated as product preferences unless the product later explicitly enters regulated/medical territory.
