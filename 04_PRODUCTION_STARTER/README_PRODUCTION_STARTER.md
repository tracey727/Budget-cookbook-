# Production Starter — GitHub + Cloudflare + Neon

This folder is a **starter**, not a claim that production is already complete.

## What is included
- Cloudflare Worker TypeScript starter.
- Static Assets binding.
- Hyperdrive placeholder.
- Neon/Postgres initial schema.
- full V1 recipe catalogue JSON seed source.
- current prototype UI copied into `public/` as a migration/reference baseline.

## First repository steps
1. Verify/create the authoritative private GitHub repo.
2. Copy this folder to the repo root only after the repo identity is verified.
3. Run `npm install`.
4. Copy `wrangler.toml.example` to `wrangler.toml` **locally** and insert the real Hyperdrive ID; do not commit it if it contains environment-specific values.
5. Create Neon project/branch and review/apply `schema/001_initial_schema.sql`.
6. Build a seed importer from `data/recipe_catalog_v1.json`; reconcile exact counts after import.
7. Create Hyperdrive and verify `/api/health` before migrating recipe UI to database APIs.

## Prototype migration note
`public/engine.prototype.js` and `public/data.prototype.js` are preserved to prevent behavioural regression. Production should replace bundled catalogue data with API-backed data and authenticated household persistence while keeping the deterministic calculation rules.

## Secrets
Use Cloudflare secret storage for Stripe secrets and any other secret. Never put secret values in source, `wrangler.toml.example`, `.env.example` or browser JavaScript.

## V2 dietary-engine migration
After Phase 2 model review and before seeding production dietary classifications, apply:
1. `schema/001_initial_schema.sql`
2. `schema/002_dietary_requirements.sql`

Do not populate `recipe_requirement_assessments` with optimistic defaults. Public suitability must come from the Phase 2 classification audit; unknown/high-consequence values remain `UNVERIFIED`.
