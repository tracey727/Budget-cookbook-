# Production Deployment Runbook

## Preconditions
- Phases 0–17 GREEN.
- authoritative GitHub repo verified and `main` protected;
- production Neon branch and migration state recorded;
- Cloudflare Worker/Hyperdrive IDs recorded securely;
- Stripe products/prices and webhook secret configured;
- UAT release candidate checksum recorded;
- rollback commit/deployment identified.

## Neon
1. Apply reviewed migrations to production.
2. Verify schema version.
3. Seed/verify approved public recipe catalogue.
4. Run count reconciliation.
5. Verify least-privilege application role.
6. Verify backup/recovery settings.

## Cloudflare
1. Set production Hyperdrive binding.
2. Add secrets using `wrangler secret put` or dashboard secret management.
3. Deploy exact protected-main commit.
4. Verify `/api/health`.
5. Verify static assets.
6. Verify recipe catalogue query.
7. Verify household-authenticated endpoints.
8. Verify custom domain and TLS.

## Stripe
1. Configure production webhook URL.
2. Verify webhook signing secret is Cloudflare secret only.
3. Trigger controlled checkout/payment test appropriate for live release process.
4. Confirm entitlement state.
5. Confirm cancellation and webhook retry behaviour.

## Smoke test
- open home on mobile;
- set household size;
- enter pantry;
- enter/receive prices;
- rank meals;
- open recipe;
- add to planner;
- generate shopping list;
- check budget total;
- verify account persistence;
- verify premium gate if enabled.

## Rollback
If a critical defect appears:
1. stop new release promotion;
2. rollback Cloudflare deployment to recorded previous version;
3. do not roll database backward destructively unless a tested backward migration exists;
4. disable affected feature behind server-side control if available;
5. preserve logs and incident evidence;
6. repair through protected-main change control.
