# Food / Cookbook / Nutrition Product Family

## Canonical general household product
- `tracey727/Budget-cookbook-` — **GENEVIEVE Family Budget Cookbook™**. This is the authoritative general household budget, pantry, recipe, dietary-requirements and recipe-catalogue engine.

## Separate specialised sibling
- `tracey727/Irene-s-family-cookbook-` — **Irene's Family Sunday Cook-Up**. Bespoke four-week household planner / Sunday meal-prep app. Keep separate: its fixed household assumptions, presentation and prep schedule are specific to that household rather than the general 800-recipe product.

Reusable presentation or meal-prep ideas may be reimplemented deliberately in the Family Budget Cookbook, but do not copy the bespoke household data or clinician-related assumptions into the general product.

## Separate safety product — unique orphan
- **GENEVIEVE App™ Food Safety V15 No-Guess** is preserved in `tracey727/Genevieve-Business-Deployment` at:
  `02_ACTIVE_DEPLOYMENTS_NEXT/GENEVIEVE_APP_FOOD_SAFETY_V15_NO_GUESS_FULL_DEPLOY.zip`

The archive index confirms a complete standalone static/PWA product package with its own app, privacy, terms, safety page and build-verification material. It is not another Cookbook build and must not be absorbed into recipe-ranking logic.

**Status:** preserve / do not delete. It requires its own dedicated canonical repository before further development or deployment. Its archived Netlify/Vercel files are historical and must not be carried forward as active deployment configuration. Current platform direction is GitHub + Cloudflare.

## Animal nutrition is a different family
- `genevieve_animal_nutrition_feeding_allergy_v1.zip` in the Business Deployment archive belongs to the **Animal Sense** family and is already indexed by `tracey727/Genevieve-Animals-Dog-Parks-App`.
- Do not mix animal feeding/allergy data models into the human/family cookbook merely because both use the word nutrition.

## Historical Food & Grocery concept
The July 2026 master archive records an older **GENEVIEVE Food & Grocery** concept/version lineage. No separate current repository was found during this cleanup. Treat that record as historical provenance unless a verified source package is recovered later.

## Platform
Active product direction: **GitHub + Cloudflare + Neon** where persistence is required. No Vercel deployment dependency should be introduced.
