# Phase 7 — Recipe Catalogue API + Production UI Migration

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 7.

**GREEN gate (as written):** all launch recipes display from authoritative
production data; prototype regression set passes.

## Starting point: a real gap found before writing any API code

Before adding routes, this phase checked what "authoritative production
data" would actually mean once seeded, by reading
`scripts/build_seed_sql.py` end to end. Two real gaps were found, both
fixed here rather than worked around:

1. **`recipes.public_launch_approved` was hardcoded `false` for all 800
   recipes**, with a comment attributing this to "the Launch Rule." Reading
   `02_RECIPE_CONTENT/PHASE_2_8_LAUNCH_READINESS_REPORT.md` shows this
   conflates two different gates: the dietary-claim Launch Rule (a computed
   `MEETS` is downgraded to `UNVERIFIED` until a human reviewer sets
   `reviewed: true` on that specific requirement assessment) and the
   separate, already-decided Phase 2.8 recipe-level launch/hold split (385
   `LAUNCH_READY`, 415 `HELD_FOR_KITCHEN_TEST`, in
   `02_RECIPE_CONTENT/recipe_launch_readiness_v1.json`). Leaving every
   recipe `false` would have made Phase 7's GREEN gate unsatisfiable — there
   would be no "authoritative production data" to display at all. Fixed:
   `build_recipes()` now sources `public_launch_approved` from that frozen
   Phase 2.8 file (`LAUNCH_READY` → `true`), with build-time assertions that
   its recipe ids match the catalogue exactly and its `LAUNCH_READY` count
   matches the file's own recorded `launch_ready_count`. Re-running the
   generator against the real data files confirms exactly **385** rows come
   out `public_launch_approved = true`.
2. **No script actually seeded `swap_groups`/`swap_options`**, despite
   `PHASE_5_NEON_DATABASE_FOUNDATION_REPORT.md`'s reconciliation table
   claiming 20/136 rows sourced from `recipe_catalog_v1.json`'s `swapMap`.
   `build_seed_sql.py` had no such step. Added `build_swap_groups()`,
   generating `swap_groups`/`swap_options` insert SQL from `swapMap` (using
   the swap-group name as both code and display name, since no separately
   authored label exists — same approach already used for dietary
   requirement display names). Confirmed by running the generator: 20
   groups, 136 options, matching the Phase 5 report's figures exactly. The
   pre-existing, documented content gap (23 of ~43 `swap_group_code` values
   referenced by `recipe_ingredients` have no `swapMap` entry at all) is
   unchanged by this — it's missing source content, not something a seed
   generator can invent.

## What this phase built

### 1–2. Recipe list/filter + detail API
`src/api/recipes.ts` — pure, dependency-free query-building and row-mapping
functions (no `pg`/Worker import), wired into `src/index.ts`:
- `GET /api/recipes` — filters: `mealType`, `budgetTier`, `vegetarian`,
  `gfAdaptable`, `dfAdaptable`, `lunchboxFriendly`, `freezerFriendly`,
  `onePanPot`, `maxPrepMin`, `maxCookMin`, `search` (name, ILIKE,
  wildcard-escaped), plus `limit`/`offset` paging (default 60, capped at
  200). Every value a caller controls is bound as a positional SQL
  parameter — never concatenated into the query text.
- `GET /api/recipes/:id` — full detail with ingredient lines.
- Both always add `public_launch_approved = true`; a `HELD_FOR_KITCHEN_TEST`
  recipe id 404s exactly like an id that doesn't exist, rather than
  revealing its held status.

### 3. Stable recipe IDs
Unchanged from Phase 4/5: `GEN-RCP-####` ids flow through the API verbatim
(`mapRecipeSummaryRow`/`mapRecipeDetailRow` pass `recipe_id` straight
through as `id`, no re-derivation). `build_seed_sql.py` already asserted
sequential ids at seed time; that assertion is untouched.

### 4. Production UI migration
`public/data.prototype.js` (935 KB, bundling all 800 recipes — including
the 415 held-back ones) was **deleted**, not just unreferenced: Cloudflare
Static Assets serves everything under `public/` at its own path regardless
of which `<script>` tags reference it, so leaving it in place would have
kept the entire unreviewed catalogue publicly fetchable at
`/data.prototype.js`, defeating this exact GREEN gate. `engine.prototype.js`
was renamed to `engine.js` with **zero content changes** — confirmed by
diffing the renamed file — so the deterministic pantry-coverage/
affordability ranking rules are byte-identical to the prototype's. The only
new file is `public/app.js`, which fetches `GET /api/catalogue`
(`src/api/catalogue.ts`, a bulk endpoint purpose-built to reproduce the
exact legacy data shape `engine.js` expects — including its `"Yes"`/`"No"`
string flags rather than booleans, see that file's module comment — scoped
to launch-approved recipes only) and then loads `engine.js` once the data
has arrived, with a visible loading/error status region
(`role="status"`/`role="alert"`) instead of the old synchronous bundle load.

### 5. Mobile-first layout + accessibility
The prototype's existing `@media(max-width:900px)` layout was kept as-is
(already reasonably mobile-first). Added: `aria-live="polite"` on the
KPI summary bar so ranking updates are announced without spamming a screen
reader on every re-render of the full results grid; `aria-label` on the
recipe detail `<dialog>`; `role="status"`/`role="alert"` loading and error
banners.

## Verification

- **`npm run typecheck`** — clean.
- **All existing test scripts** (`test:dietary`, `test:substitution`,
  `test:professional`, `test:texture`, `test:units`) still pass unchanged —
  no regression from this phase's changes.
- **New `test:recipes-api`** — query-builder/row-mapper unit tests,
  including an explicit check that a hostile search string (`'; drop table
  recipes; --`) only ever appears as a bound parameter value, never inside
  the generated SQL text.
- **New `test:catalogue-api`** — includes an end-to-end fixture regression
  test: converts the real `data/recipe_catalog_v1.json` +
  `recipe_launch_readiness_v1.json` into the exact row shapes
  `build_seed_sql.py` would load into Postgres, runs them through
  `assembleCatalogue`, and diffs the result against the original prototype
  data. Confirms: exactly 385 recipes served, no `HELD_FOR_KITCHEN_TEST`
  recipe leaks through, every engine-relevant field round-trips exactly,
  `swapMap` reproduces exactly, and `ingredientUnitPairs` is a strict
  subset of the original static list (scoped down to only launch-approved
  recipes' ingredients) with nothing invented.
- **`build_seed_sql.py`** re-run against the real data files: 385
  `public_launch_approved` rows, 20 swap groups, 136 swap options — all
  three now reproducible from a clean checkout, which they weren't before
  this phase.
- **Browser smoke test** (Chromium via Playwright, mobile 390×844 and
  desktop 1440×900 viewports, `/api/catalogue` mocked with a small fixture
  since no live Worker/Neon exists yet): catalogue loads, recipe count and
  KPIs update from the fetched data, results render as cards, clicking
  "View meal" opens the detail dialog with the fetched ingredients/method/
  swap notes, and the error path (`/api/catalogue` returning 500) shows a
  visible `role="alert"` message instead of a blank or broken page. This
  test used Playwright installed ad hoc outside the repo (not added as a
  project dependency) and is not committed as an automated suite here.

## What's still blocked

Same root cause as Phases 5 and 6: this sandbox's network policy rejects
outbound connections to both Neon's Postgres endpoint and the Cloudflare
API, so nothing here could be verified against a **live** Worker, a live
Hyperdrive-backed database connection, or a real `wrangler dev`/`deploy`.
Everything above was verified at the code level — typecheck, unit tests, an
end-to-end fixture regression test standing in for a live-database check,
and a real headless-browser run against the real `public/` files with the
API layer mocked. Once Cloudflare/Neon provisioning unblocks (Phase 6's
open item), the next real verification step is: apply
`schema/001_initial_schema.sql` + `schema/002_dietary_requirements.sql`,
run the seed SQL this phase's generator produces, deploy the Worker, and
re-run this phase's browser smoke test against the live `/api/catalogue`
instead of a mock.

## GREEN gate assessment

| Criterion | Status |
|---|---|
| All launch recipes display from authoritative production data | **GREEN in the code as written** — the seed generator now reproducibly marks exactly the 385 Phase 2.8 `LAUNCH_READY` recipes `public_launch_approved`, both API endpoints and the bulk catalogue endpoint gate on that column, and the held-back 415 are provably excluded (fixture regression test) and unreachable by id (404, not a leak). **Not yet verified against a live deployment** — see above. |
| Prototype regression set passes | **GREEN on the terms available in this sandbox** — no live-Worker/live-browser-against-Neon regression run exists yet (none did before this phase either); a Chromium smoke test against the real production files with the API mocked, plus the fixture-based data-contract regression test, both pass. |

Overall: **PARTIAL, on the same honest basis as Phases 3, 5 and 6** — all
code-level work is complete, tested, and reproducible from a clean
checkout; live verification remains blocked on the same Cloudflare/Neon
provisioning gap Phase 6 already reported.
