# Phase 6 — Cloudflare Worker + Hyperdrive Foundation

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 6.

**GREEN gate (as written):** Cloudflare Worker reaches Neon through the
approved path; no DB credentials are exposed to browser code.

## What this phase found

Before writing any code, the account's existing Cloudflare resources were
checked the same way the three candidate Neon projects were checked in
Phase 5 — by inspection, not by name alone. The account holds 20 existing
Workers and 7 existing Hyperdrive configurations, several sharing the
"genevieve" name (`genevieve-app`, `genevieve-budget-app`,
`genevieve-clinician-command`, `genevieve-emergency-v103-*`,
`genevieve-grey-nomad(s)`, `genevieve-vip-edge-api`, …). Reading the bundled
source of the closest name match, `genevieve-budget-app`, showed it
self-identifies as `"Genevieve App — Budget App"` with no recipe, dietary,
ingredient, or meal-plan content anywhere in it — a generic personal
expense tracker, unrelated to this product, reusing the same brand name.
None of the 7 existing Hyperdrive configurations point at this project's
Neon endpoint (`ep-divine-mountain-a79gcke0-pooler.ap-southeast-2.aws.neon.tech`)
either. As in Phase 5, none of these existing resources were touched, and
none is a fit to extend — this product needs a new Worker and a new
Hyperdrive configuration.

## Blocked: creating the Worker, the Hyperdrive config, and deploying

Phase 6 items 1 ("Create Worker"), 3 ("Create Hyperdrive configuration to
Neon"), and 5 ("Deploy `/api/health` first") could not be completed from
this session, for a concrete, checked reason rather than an assumption:

- The Cloudflare tools available in this session can **list, get, edit,
  and delete** Workers and Hyperdrive configurations, but there is no tool
  to **create** either one. (`hyperdrive_configs_list` / `_get` / `_edit` /
  `_delete` exist; there is no `_create`. `workers_list` / `_get_worker` /
  `_get_worker_code` exist; there is no create-or-deploy equivalent.)
- The `wrangler` CLI is installed in this sandbox but has no stored
  Cloudflare credentials: `wrangler whoami` reports "You are not
  authenticated," and `wrangler login` requires an interactive browser
  OAuth flow this sandbox cannot run. No `CLOUDFLARE_API_TOKEN` or
  `CLOUDFLARE_ACCOUNT_ID` is set in the environment for a non-interactive
  login either.

This is the same category of stopping point as Phase 3's repository
visibility/branch-protection settings: a real action against a live
account that this session's tools cannot perform, not a decision this
session should guess at or fake progress on.

## What this phase did complete

Everything that doesn't require creating a live Cloudflare resource was
finished and verified:

1. **Structured error handling + request IDs** (Phase 6 item 6, the one
   item that was genuinely still open in the code). `src/index.ts` now:
   - Generates one `crypto.randomUUID()` request ID per incoming request,
     before routing.
   - Returns it as an `x-request-id` response header on **every** response
     — success, expected 4xx/5xx, and static-asset responses alike — so a
     user or log line can always be correlated back to a specific request.
   - Distinguishes expected failures (`ApiError`, e.g. `recipe_not_found`)
     from genuine unhandled exceptions: an `ApiError` is turned into its
     declared status code with its own error code in the body; anything
     else is logged server-side with `console.error("unhandled_error",
     requestId, error)` (so the real detail is never lost) but the client
     only ever sees `{ error: "internal_error", requestId }` — the
     internal error detail is never leaked to a caller.
   - Verified with `npm run typecheck` (clean) against the real
     `@cloudflare/workers-types` ambient types (`Request`, `Response`,
     `Fetcher`, `crypto.randomUUID()`), not just by eye.
2. **Two real defects fixed in the starter pack**, found while getting the
   above to actually build and test, not invented for this report:
   - `package.json` pinned `@cloudflare/workers-types` to `^4.20260901.0`,
     a version that does not exist on the npm registry (the package
     renumbered to a `5.x` major with date-stamped minor/patch versions
     some time before this build). `npm install` failed outright. Fixed to
     `^5.20260901.1`, the real release matching the same date the pack
     intended.
   - All five `test:*` npm scripts (`test:dietary`, `test:substitution`,
     `test:professional`, `test:texture`, `test:units`) invoked
     `tsc --ignoreConfig`, which is not a real TypeScript CLI flag (`tsc
     --version` reports 5.9.3; `--ignoreConfig` has never existed). Every
     one of these scripts was failing with `error TS5023: Unknown compiler
     option '--ignoreConfig'.` before this fix — meaning none of the
     Phase 2/4 test suites this build pack relies on as its GREEN-gate
     evidence could actually run as scripted. Passing the same file list
     to plain `tsc --outDir …` (no extra flag) compiles cleanly on its own
     — TypeScript does not consult `tsconfig.json` when file arguments are
     given on the command line, so the flag was never needed. Removed it
     from all five scripts; re-ran all five end-to-end after the fix and
     confirmed the same pass/fail output already recorded in the Phase 2
     and Phase 4 reports (12/12, 3/3 shown, 3/3 shown, 3/3 shown, 3/3 shown
     checks passing respectively — full output unchanged from what those
     reports already describe, now actually reproducible via `npm run
     test:*` rather than only via a hand-typed `tsc` invocation).
3. **Confirmed already correct from the starter pack**, not re-done: static
   assets binding (`[assets]` → `./public`, binding `ASSETS`) and
   `compatibility_flags = ["nodejs_compat"]` are both already present in
   `wrangler.toml.example` (items 2 and 4 of this phase's checklist).

`wrangler.toml` itself (the real, non-`.example` file `wrangler dev` and
`wrangler deploy` read) is intentionally not created by this phase: it is
already `.gitignore`d because it will carry a real Hyperdrive binding ID
once one exists, and creating it now with a placeholder would invite it
being deployed against a non-existent resource.

## Credential path attempted and ruled out

The product owner provided a scoped Cloudflare API token to unblock this.
Verifying it (`curl https://api.cloudflare.com/client/v4/user/tokens/verify`)
failed before the token was ever checked: this sandbox's outbound network
policy rejects the connection to `api.cloudflare.com` itself with a 403 at
the egress gateway (`connect_rejected`, logged as an explicit organization
policy denial, not a timeout or DNS failure). The same proxy blocked direct
Postgres access to Neon in Phase 5 for the identical reason. Per this
environment's own operating guidance, a policy denial (403/407) is to be
reported, not retried or routed around — so `wrangler` and direct Cloudflare
API calls are unusable from this sandbox regardless of how the token is
scoped, and the token was revoked by the product owner rather than left
live and pasted in a chat transcript.

This means the only two remaining paths are the ones below; a credential
handed to this session cannot close the gap, because the gap is network
policy, not authorization.

## What's needed to finish this phase

One of, from the product owner:

1. **Provision manually and hand back the resulting IDs** — create the
   Worker (any name; `genevieve-family-budget-cookbook` matches the repo)
   and a Hyperdrive configuration pointing at
   `ep-divine-mountain-a79gcke0-pooler.ap-southeast-2.aws.neon.tech:5432`,
   database `genevieve_cookbook`, user `genevieve_app` (password stored
   only in Cloudflare's own Hyperdrive config, never in this repo) via the
   Cloudflare dashboard, then share the Hyperdrive config ID so
   `wrangler.toml`'s `[[hyperdrive]] id` can be set and the Worker
   deployed from this session.
2. **Deploy it yourself from your own machine** — clone
   `04_PRODUCTION_STARTER`, run `npm install`, copy `wrangler.toml.example`
   to `wrangler.toml`, run `wrangler login` (interactive OAuth works fine
   outside this sandbox), create the Hyperdrive config with
   `wrangler hyperdrive create` (or the dashboard) pointing at the Neon
   details above, put its ID in `wrangler.toml`, then `wrangler deploy`.
   This needs no changes from this session at all.

Until one of those happens, Phase 7 (which builds the recipe catalogue API
on top of this Worker) can proceed on the code side but cannot be verified
against a live deployment.

## GREEN gate assessment

| Criterion | Status |
|---|---|
| Cloudflare Worker reaches Neon through the approved path | **BLOCKED** — code is written and typechecks against real Worker types; no live Worker or Hyperdrive config exists yet to prove it reaches Neon, for the credential/tooling reasons above |
| No DB credentials are exposed to browser code | **GREEN in the code as written** — `src/index.ts` only ever reads `env.HYPERDRIVE.connectionString` server-side inside the Worker; nothing under `public/` references a database credential, and `wrangler.toml.example`'s own comment directs secrets to `wrangler secret put`, never into the repo |

Overall: **PARTIAL**, on the same honest basis as Phase 3 and Phase 5 — the
work this session's tools can do is complete and verified (including two
real pre-existing defects fixed along the way); the remaining work is
account-level Cloudflare provisioning that requires either credentials or
manual action this session does not have.
