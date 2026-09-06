# GENEVIEVE Household Recipe Decision Engine — Contract

## Inputs
`household_size`, `meal_budget`, meal/diet/use filters, pantry quantities, and price-per-recipe-unit.

## Ingredient calculation
`scale_factor = household_size / base_serves`

For every required ingredient:
`required_qty = base_qty * scale_factor`
`shortage_qty = max(0, required_qty - pantry_qty)`
`missing_cost = shortage_qty * price_per_recipe_unit`

Optional ingredient lines do not reduce pantry coverage or force a purchase.

## Recipe calculation
`pantry_coverage = covered_required_lines / required_lines`
`estimated_missing_cost = sum(missing_cost)`
`pricing_complete = all missing required lines have a positive price`

A recipe is not labelled affordable until pricing is complete.

## Ranking
- Pantry coverage: 60 points
- Affordability: 30 points
- Missing-item bonus: 10 points
- Required user filters are hard gates before ranking.

## Next production layer
Add canonical ingredient IDs, pack sizes, unit conversion, current retail/source prices, shopping-basket rounding, household accounts and Neon persistence.
