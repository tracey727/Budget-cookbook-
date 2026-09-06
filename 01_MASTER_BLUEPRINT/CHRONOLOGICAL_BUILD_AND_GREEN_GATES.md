# Chronological Build Plan + GREEN Gates

Build strictly in order. Do not call a phase complete until its GREEN gate passes.

## Phase 0 — Directive, Product & IP Freeze — GREEN
**Built in this pack.**
- Product name and purpose frozen.
- 800-recipe baseline recognised as GENEVIEVE Family Budget Cookbook™ content.
- Production stack frozen: GitHub + Cloudflare + Neon; Stripe payments; no Vercel.

**GREEN gate:** product directive exists, scope is explicit, stack is explicit, no conflicting second app is created.

## Phase 1 — Source Baseline & Integrity Freeze — GREEN
**Verified before pack sealing.**
- 800 recipe records.
- 3,840 ingredient lines.
- 187 ingredient/unit keys.
- 20 swap groups.
- working Household Decision Engine V1 present.
- original baseline artifacts preserved in `99_ARCHIVE_BASELINES`.

**GREEN gate:** counts match, IDs are stable, source files are checksummed, browser engine syntax passes.

## Phase 2 — Dietary Requirements Engine + Recipe/Content Production QA — NEXT
The dietary engine is now a prerequisite to reviewing the 800 recipes so the catalogue is audited once against the correct production model.

### Phase 2.1 — Freeze Dietary Taxonomy & Claim Boundaries — NEXT
- approve the taxonomy in `07_DIETARY_REQUIREMENTS_ENGINE/DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md`;
- approve the four suitability states: MEETS / ADAPTABLE / EXCLUDED / UNVERIFIED;
- separate hard safety requirements from preferences;
- preserve CUSTOM_EXCLUSION / CUSTOM_REQUIREMENT / CUSTOM_PREFERENCE;
- freeze certification and medical-claim language.

**GREEN gate:** no wording implies allergy, coeliac, medical, religious-certification or dysphagia safety without appropriate evidence.

### Phase 2.2 — Canonical Ingredient Dietary Attribute Model
Implement ingredient attributes for ethical/lifestyle, allergens, cereals/gluten, animal-source, alcohol and extension fields.

**GREEN gate:** locked requirement classes can be expressed without unsafe ingredient-name string matching alone.

### Phase 2.3 — Household Member Requirements
Implement member profiles, enforcement levels and source/provenance.

**GREEN gate:** one household can safely combine different requirements for different people.

### Phase 2.4 — Classify all 800 Recipes
Audit every recipe against applicable requirement families. High-consequence suitability is evidence-based; unresolved states remain UNVERIFIED.

**GREEN gate:** every launch recipe has a versioned classification record for enabled requirement families or remains visibly unverified.

### Phase 2.5 — Substitution Safety + Adapted Cost
Map substitutions and prevent any substitute from violating another member’s hard exclusions. Recalculate ingredient quantities and cost using the chosen substitute.

**GREEN gate:** every adaptation changes both the displayed ingredient list and affordability maths.

### Phase 2.6 — Medical / Professional-Plan Boundaries
Support supplied dietary targets without diagnosing or inventing therapeutic targets.

**GREEN gate:** professional-plan modes require explicit configuration and cannot be activated from inferred health conditions.

### Phase 2.7 — Texture / IDDSI Boundary
If IDDSI support is enabled, use clinician/care-plan supplied levels and require preparation verification before suitability claims.

**GREEN gate:** no recipe is called IDDSI compliant from description alone.

### Phase 2.8 — Full Recipe/Content Production QA
1. Audit duplicate/near-duplicate recipe names and families.
2. Validate cooking methods and timings category-by-category.
3. Review recipe quantities for realistic household use.
4. Review high-risk scaling cases: eggs, raising agents, strong spices, pan oil, cans/packs.
5. Freeze allergen/adaptation disclaimers in product UX.
6. Mark any recipe requiring real kitchen testing before public launch.
7. Exclude unresolved launch recipes rather than guessing.

**GREEN gate:** no unsafe or misleading dietary claims; every launch recipe has a reviewed ingredient/method record and dietary classification; unresolved recipes remain unverified or excluded from launch.

## Phase 3 — Authoritative GitHub Production Repository & Protection
1. Create or verify one authoritative private repository.
2. Import `04_PRODUCTION_STARTER` only after verifying the repository identity.
3. Default branch `main`.
4. Protect `main`; changes through pull requests.
5. Add `.gitignore`; confirm no secrets, customer data or Stripe keys are present.
6. Record repository URL, ID, owner and visibility.

**GREEN gate:** one authoritative private repo; protected main; no competing repo; no secrets committed.

## Phase 4 — Canonical Ingredient, Unit & Pack Model
1. Assign canonical ingredient IDs.
2. Define canonical quantity dimensions: mass, volume, count, pack/serve special cases.
3. Define unit conversion table.
4. Separate recipe quantity from retail pack quantity.
5. Define pack rounding rule: exact cooking need versus whole packs to buy.
6. Map every one of the 187 V1 ingredient/unit keys.

**GREEN gate:** every launch ingredient converts deterministically or is explicitly marked manual-only; no incompatible units are silently compared.

## Phase 5 — Neon Database Foundation
1. Create production Neon project/branch.
2. Apply migrations from `04_PRODUCTION_STARTER/schema` after review.
3. Seed canonical recipe catalogue from `recipe_catalog_v1.json`.
4. Add indexes and constraints.
5. Create least-privilege application DB role.
6. Verify backup/recovery policy.

**GREEN gate:** migrations reproducible from zero; 800 recipes and 3,840 ingredient lines reconcile after seed; least-privilege role works.

## Phase 6 — Cloudflare Worker + Hyperdrive Foundation
1. Create Worker.
2. Bind Static Assets.
3. Create Hyperdrive configuration to Neon.
4. Set `nodejs_compat` only as required by DB driver.
5. Deploy `/api/health` first.
6. Add structured error handling and request IDs.

**GREEN gate:** Cloudflare Worker reaches Neon through the approved path; no DB credentials are exposed to browser code.

## Phase 7 — Recipe Catalogue API + Production UI Migration
1. Serve recipe list/filter API.
2. Serve recipe detail API.
3. Preserve all stable recipe IDs.
4. Migrate working prototype UI into production build without changing engine behaviour silently.
5. Test mobile-first layout and accessibility.

**GREEN gate:** all launch recipes display from authoritative production data; prototype regression set passes.

## Phase 8 — Household Decision Engine Productionisation
1. Move scale/shortage/coverage logic into shared tested engine code.
2. Define deterministic rounding per unit class.
3. Preserve “Need prices” state.
4. Add explanation payload for every recommendation.
5. Add cheap-swap candidate calculation.

**GREEN gate:** same controlled inputs produce the same recommendation results in test and production builds.

## Phase 9 — Pantry + Price Book Persistence
1. Add authenticated household state.
2. Persist pantry by canonical ingredient/unit.
3. Persist user/store price book.
4. Add change timestamps.
5. Prevent one household from reading another household's data.

**GREEN gate:** tenant/user isolation tests pass; pantry and prices survive sign-out/sign-in as intended.

## Phase 10 — Retail Pack Conversion & Real Shopping Math
1. Add pack quantity, pack unit and pack price.
2. Convert recipe shortage to purchasable packs.
3. Round up pack count safely.
4. Calculate actual basket outlay separately from ingredient consumption cost.
5. Compare alternative pack sizes when available.

**GREEN gate:** shopping quantities are purchasable and mathematically correct; no fractional tins/packs are presented as purchase instructions.

## Phase 11 — Weekly Planner + Combined Shopping List
1. Add meal plan table and UI.
2. Support per-meal serving override.
3. Aggregate ingredient demand across meals.
4. Subtract pantry once across the plan.
5. Generate combined pack-rounded shopping list.
6. Maintain weekly budget estimate.

**GREEN gate:** no double-counting of pantry stock or shopping requirements across planned meals.

## Phase 12 — Leftovers, Batch Cooking & Waste Reduction
1. Allow cooked yield/leftover servings.
2. Carry planned leftovers into later meal slots.
3. Reduce later shopping need when leftovers are allocated.
4. Add “use what I have” and “use soon” ranking signals.

**GREEN gate:** leftovers reduce future demand without creating negative stock or duplicate servings.

## Phase 13 — Authentication, Privacy & Account Controls
1. Choose and document secure account/session mechanism compatible with locked stack.
2. Minimise collected personal data.
3. Add account deletion/export path where applicable.
4. Add CSRF/session protection, rate limits and Turnstile where appropriate.
5. Document privacy notice and retention.

**GREEN gate:** independent security/privacy review of account controls passes; no public deployment with insecure homemade authentication.

## Phase 14 — Stripe Monetisation & Entitlements
1. Create Stripe products/prices outside source code.
2. Add Checkout/payment link flow.
3. Add verified webhook endpoint.
4. Store Stripe customer/subscription IDs and minimum entitlement state only.
5. Verify signature on every webhook.
6. Make webhook processing idempotent.
7. Define downgrade/cancel/grace behaviour.

**GREEN gate:** test payments update entitlement correctly; forged/replayed webhook tests fail safely; no secret key reaches the browser.

## Phase 15 — Accessibility, PWA/Offline & Resilience
1. WCAG-oriented keyboard/focus/labels/contrast review.
2. Decide offline scope.
3. Cache public recipe catalogue safely if useful.
4. Never cache sensitive account responses in a way that leaks households.
5. Add graceful network/offline states.

**GREEN gate:** core browse/decision flow is usable on target mobile devices and failure states are explicit.

## Phase 16 — Security, Performance & Full Regression Audit
- dependency audit;
- secret scan;
- SQL injection/parameterisation tests;
- auth/tenant isolation tests;
- API rate-limit tests;
- performance tests over 800 recipes and realistic household data;
- engine golden tests;
- mobile/browser tests;
- Stripe test-mode regression.

**GREEN gate:** no critical/high unresolved defects; all locked core rules pass.

## Phase 17 — UAT & Commercial Release Candidate
1. Build RC from protected `main`.
2. Run user journeys: new user, pantry setup, budget search, recipe detail, planner, shopping, payment, cancellation.
3. Confirm legal pages and pricing presentation.
4. Confirm no test data/secrets in production bundle.

**GREEN gate:** signed UAT checklist; release candidate checksum recorded.

## Phase 18 — Cloudflare Production Deployment
1. Create production Worker/environment.
2. Configure Hyperdrive and secrets.
3. Apply production Neon migrations.
4. Deploy immutable build from protected `main`.
5. Configure custom domain/SSL.
6. Verify health, DB, static assets and Stripe webhooks.
7. Smoke test live checkout and entitlement using safe test/controlled method.

**GREEN gate:** production smoke test passes and rollback path is documented.

## Phase 19 — Launch Archive, Monitoring & Improvement
1. Seal deployed source + migration + manifest checksums.
2. Record version, commit and deployment IDs.
3. Monitor errors, webhook failures and DB health.
4. Add product analytics only with privacy controls.
5. Begin controlled recipe expansion beyond 800 only through versioned content releases.

**GREEN gate:** deployed version is reproducible and archived; monitoring and rollback ownership are clear.
