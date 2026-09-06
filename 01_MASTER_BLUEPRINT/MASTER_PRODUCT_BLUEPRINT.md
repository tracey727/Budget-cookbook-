# GENEVIEVE Family Budget Cookbook™ — Master Product Blueprint

## 1. Product proposition
A household budget-and-food decision product that transforms a large recipe catalogue into an adaptive daily tool. It is not merely a cookbook. The value comes from matching meals to the household's **people, pantry, budget, preferences, and constraints**.

## 2. Core user questions
- What food do I already have?
- What meal can I make without shopping?
- If I must shop, what is the cheapest practical gap?
- How much do I need for the number of people I am feeding?
- What can I swap if an ingredient is unavailable, unsuitable or expensive?
- How do I turn selected meals into a weekly plan and shopping list?

## 3. Verified V1 content baseline
- 800 recipe records.
- 3,840 ingredient lines.
- 187 ingredient/unit keys.
- 20 substitution groups.
- Categories: Breakfast, Lunch, Dinner/Tea, Snack, Dessert, Baking/Side.
- Recipe metadata includes household scaling base, meal type, preparation/cook times, budget tier, and adaptability/use tags.

## 4. Built V1 decision engine
### Inputs
- household size;
- maximum spend for one meal;
- pantry quantity by ingredient + recipe unit;
- price per recipe unit;
- meal/diet/use filters.

### Ingredient logic
`scale_factor = household_size / base_serves`

For each required ingredient:
`required_qty = base_qty × scale_factor`

`shortage_qty = MAX(0, required_qty - pantry_qty)`

`missing_cost = shortage_qty × price_per_recipe_unit`

Optional lines do not penalise pantry coverage or force a purchase.

### Recipe logic
`pantry_coverage = covered_required_lines / required_lines`

`estimated_missing_cost = SUM(missing_cost)`

A recipe must not be labelled affordable until all missing required ingredient lines have valid pricing.

### Ranking V1
- Pantry coverage: 60 points.
- Affordability: 30 points.
- Low missing-line bonus: 10 points.
- Required filters are hard gates before ranking.

## 5. Production product surfaces
### Home / Decision screen
- People to feed.
- Budget available.
- Meal type.
- Household dietary/use preferences.
- “What have I got?” pantry shortcut.
- Ranked recipe recommendations.

### Recipe detail
- scaled ingredient quantities;
- on-hand quantity;
- shortage quantity;
- price gap;
- substitution options;
- method;
- save/favourite;
- add to planner;
- add missing items to shopping list.

### Pantry
- canonical ingredient;
- quantity + canonical unit;
- optional expiry/date later;
- quick increment/decrement;
- “use soon” later.

### Price book / Shopping prices
- store/source;
- pack price;
- pack quantity;
- unit;
- calculated unit price;
- last checked;
- user-entered or future verified source.

### Weekly planner
- breakfast/lunch/dinner/snacks/dessert slots;
- household size override per meal;
- weekly budget ceiling;
- running planned spend;
- batch-cook / leftovers link.

### Shopping list
- combine shortages across planned meals;
- subtract pantry stock once, not repeatedly;
- convert recipe quantities to purchasable packs;
- round packs up correctly;
- show estimated basket total;
- permit manual bought/price override.

## 6. Product rules that must remain locked
1. Never invent missing food prices.
2. Never mark a recipe “within budget” if a required shortage is unpriced.
3. Pantry is consumed before shopping-cost calculation.
4. Household scaling must use the recipe base-serves denominator.
5. Unit conversion must occur before comparing pantry, recipe and retail pack quantities.
6. Optional toppings do not force purchases.
7. Strong spices, pan oil and raising agents require special scaling rules rather than blind multiplication.
8. GF/DF adaptable means the **structure can be adapted**, not that every listed packaged product is allergen-safe.
9. Users must be able to override quantities, swaps and prices.
10. The original recipe IDs must remain stable through production migration.

## 7. Monetisation boundary
Production may support Free and Premium entitlements. Exact pricing is a commercial decision, not hard-coded into recipe logic. Stripe is payment authority; Neon stores only the minimum subscription/entitlement state needed by the app, never raw card details.

## 8. Non-goals for first production release
- autonomous medical/nutrition diagnosis;
- calorie/medical-diet claims unless separately researched and governed;
- guaranteed allergen safety;
- invented supermarket prices;
- live supermarket scraping without a lawful, reliable source contract;
- complex AI meal generation before deterministic recipe matching is stable.


## Dietary Requirements & Restrictions Engine — V2 Locked Extension
Dietary requirements are now a first-class recommendation input. The engine must support multiple household members with different hard exclusions, verified requirements and preferences. Canonical result states are **MEETS / ADAPTABLE / EXCLUDED / UNVERIFIED**. Adapted recipes must recalculate both ingredients and cost. High-consequence claims remain unverified unless evidence supports them. Full contract: `07_DIETARY_REQUIREMENTS_ENGINE/DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md`.
