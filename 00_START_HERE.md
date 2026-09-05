# GENEVIEVE Family Budget Cookbook™ — COMPLETE BUILD PACK V1

**Prepared:** 5 September 2026 — Australia/Brisbane  
**Purpose:** One authoritative package containing the recipe library, working household decision engine, production blueprint, starter Cloudflare/Neon code, testing gates, and deployment runbook.

## CANONICAL CURRENT STATE

### Built and verified source baselines
- **800 recipes** in the V1 recipe bank.
- **3,840 ingredient lines**.
- **187 ingredient + recipe-unit pantry/price keys**.
- **20 swap groups**.
- Working browser prototype: **Household Decision Engine V1**.
- Prototype functions: household scaling, pantry quantities, price book, missing-ingredient calculation, affordability state, filters, ranking, recipe detail, swap suggestions, and browser `localStorage` persistence.
- Browser engine JavaScript syntax verified before this pack was sealed.

### Not yet production-complete
Do **not** call the product production-ready merely because the prototype works. These gates remain to be completed in order:
- culinary/content QA and dietary-claim review;
- canonical units + retail pack-size conversion;
- authoritative GitHub production repository + protected `main`;
- Neon production schema and migrations;
- Cloudflare Worker/API + Hyperdrive;
- authenticated household persistence;
- shopping-list/pack rounding and weekly budget planner;
- Stripe checkout, webhook and entitlement verification;
- security/privacy testing, UAT and production deployment.

## LOCKED PRODUCTION STACK
- **GitHub** — authoritative source control, protected `main`, pull requests, CI.
- **Cloudflare** — Worker + Static Assets; Hyperdrive to Neon; Turnstile where needed.
- **Neon PostgreSQL** — authoritative production relational data.
- **Stripe** — payment processing/checkout and subscription state. Stripe keys must never be committed.
- **NO VERCEL**.

## PRODUCT PURPOSE
Help a household answer, in one flow:
1. **What have I got?**
2. **What can I afford?**
3. **How many people am I feeding?**
4. **What can I cook now or with the smallest affordable shop?**

The engine must scale recipes to household size, consume pantry stock first, price only shortages, avoid inventing prices, propose substitutions, and rank suitable recipes by pantry coverage + affordability + missing-item burden.

## READ ORDER
1. `00_START_HERE.md`
2. `01_MASTER_BLUEPRINT/MASTER_PRODUCT_BLUEPRINT.md`
3. `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md`
4. `01_MASTER_BLUEPRINT/DATA_AND_ENGINE_CONTRACT.md`
5. `04_PRODUCTION_STARTER/README_PRODUCTION_STARTER.md`
6. `05_TESTING_AND_DEPLOYMENT/DEPLOYMENT_RUNBOOK.md`

## EXACT NEXT CHRONOLOGICAL ACTION
Start **Phase 2 — Recipe/content production QA and dietary-claim boundary** from the build plan. Phase 0 and Phase 1 source-baseline gates are already documented as GREEN in this pack. Do not skip directly to payments or production deployment.

## NEW CHAT CONTINUATION PROMPT
Use this exact prompt with this ZIP attached:

> Continue GENEVIEVE Family Budget Cookbook™ from the attached COMPLETE BUILD PACK V1. Read `00_START_HERE.md` first. Preserve the verified 800-recipe / 3,840-ingredient-line / 187-key / 20-swap-group baseline and the working Household Decision Engine V1. Do not use Vercel. Production stack is GitHub + Cloudflare + Neon, with Stripe for payments. Resume the exact next chronological gate: Phase 2 — Recipe/content production QA and dietary-claim boundary. Build in order and require a GREEN gate after every phase.
