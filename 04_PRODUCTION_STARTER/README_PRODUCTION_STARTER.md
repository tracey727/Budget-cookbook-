# Production Starter — GitHub + Cloudflare + Neon

This folder is a **starter**, not a claim that production is already complete.

## What is included
- Cloudflare Worker TypeScript starter, with a recipe catalogue API
  (`GET /api/recipes`, `GET /api/recipes/:id`, `GET /api/catalogue`) --
  see `src/api/recipes.ts` and `src/api/catalogue.ts`.
- Static Assets binding.
- Hyperdrive placeholder.
- Neon/Postgres initial schema.
- full V1 recipe catalogue JSON seed source.
- production UI in `public/` (`index.html`, `app.js`, `engine.js`): `app.js`
  fetches `GET /api/catalogue` and `engine.js` (the former
  `engine.prototype.js`, unchanged) runs the same deterministic pantry/
  budget ranking against that live, launch-approved-only data.

## First repository steps
1. Verify/create the authoritative private GitHub repo.
2. Copy this folder to the repo root only after the repo identity is verified.
3. Run `npm install`.
4. Copy `wrangler.toml.example` to `wrangler.toml` **locally** and insert the real Hyperdrive ID; do not commit it if it contains environment-specific values.
5. Create Neon project/branch and review/apply `schema/001_initial_schema.sql`.
6. Build a seed importer from `data/recipe_catalog_v1.json`; reconcile exact counts after import.
7. Create Hyperdrive and verify `/api/health` before migrating recipe UI to database APIs.

## Prototype migration note
Phase 7 replaced the bundled `data.prototype.js` catalogue (all 800 recipes,
including the 415 still `HELD_FOR_KITCHEN_TEST`) with `app.js` fetching
`GET /api/catalogue`, which only ever returns the Phase 2.8 launch-approved
recipes. `engine.prototype.js` was renamed to `engine.js` with its content
byte-for-byte unchanged, so the deterministic pantry-coverage/affordability
ranking rules are identical to the prototype's -- only the data source
changed. Still outstanding for a later phase: authenticated household
persistence (pantry/prices currently stay in `localStorage`, as before).

## Secrets
Use Cloudflare secret storage for Stripe secrets and any other secret. Never put secret values in source, `wrangler.toml.example`, `.env.example` or browser JavaScript.

## V2 dietary-engine migration
After Phase 2 model review and before seeding production dietary classifications, apply:
1. `schema/001_initial_schema.sql`
2. `schema/002_dietary_requirements.sql`

Do not populate `recipe_requirement_assessments` with optimistic defaults. Public suitability must come from the Phase 2 classification audit; unknown/high-consequence values remain `UNVERIFIED`.
