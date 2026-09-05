# GENEVIEVE Family Budget Cookbook™ — Household Decision Engine

This package is a working browser prototype built around the 800-recipe V1 recipe bank.

## What it does
- scales every recipe to the number of people being fed;
- records pantry quantities by ingredient + recipe unit;
- records local prices without inventing prices;
- calculates shortages and estimated missing-ingredient cost;
- filters by meal type, vegetarian, GF-adaptable, DF-adaptable, lunchbox, freezer and one-pan/pot requirements;
- ranks all 800 recipes using pantry coverage (60 points), affordability (30), and low missing-item count (10);
- shows `Cook now`, `Need prices`, `Within budget`, or `Over budget` actions;
- opens each recipe with scaled ingredient requirements, pantry quantities, shortages, cost gaps, methods and swap suggestions;
- stores pantry and price data locally in the browser using localStorage.

## Run it
Open `index.html` in a browser. No server is required because the recipe data is bundled in `data.js`.

## Production boundary
This is the decision-engine prototype, not yet the final production data architecture. For the production GENEVIEVE app, move pantry, household, price-book, favourites and planner state into authenticated Cloudflare/Neon-backed user data. Retail pack-size/unit conversion is the next pricing layer before live supermarket-price automation.

## Important food note
GF/DF flags mean the recipe structure is adaptable. They are not allergen guarantees. Ingredient labels and cross-contamination requirements still need to be checked by the user.
