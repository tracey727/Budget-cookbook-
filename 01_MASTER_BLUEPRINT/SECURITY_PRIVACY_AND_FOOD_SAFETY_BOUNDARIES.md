# Security, Privacy & Food-Safety Boundaries

## Security
- GitHub repository private during production build unless deliberately changed later.
- Protected `main`.
- No Neon password, Hyperdrive connection secret or Stripe secret in committed files.
- Browser never receives raw database credentials.
- Parameterise SQL.
- Verify Stripe webhook signatures.
- Rate-limit sensitive endpoints.
- Tenant/household isolation must be server-enforced.

## Privacy
Keep account data minimal. A household cookbook does not need unnecessary identity, health or location data. Document data export/deletion and retention before public account launch.

## Dietary/allergen language
“GF adaptable” / “DF adaptable” means the recipe pattern can be changed. It is **not** a guarantee that every packaged ingredient, kitchen or substitution is safe for allergy/coeliac requirements.

The UI must instruct users to check labels and cross-contamination requirements. Do not turn preferences into medical advice.

## Recipe QA
Before public launch, review ingredient amounts, cooking temperatures where relevant, timings, storage/freezer guidance and special scaling behaviours. Recipes not yet reviewed should be excluded from the public launch set rather than presented as tested.
