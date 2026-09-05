# Phase 5 — Neon Database Foundation

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 5.

**GREEN gate (as written):** migrations reproducible from zero; 800 recipes
and 3,840 ingredient lines reconcile after seed; least-privilege role works.

## Project identity

| Field | Value |
|---|---|
| Neon project | `genevieve-family-budget-cookbook` (`round-tree-37047152`) |
| Region | `aws-ap-southeast-2` (Sydney) |
| Branch | `main` (`br-steep-smoke-a7yj6hlh`) |
| Database | `genevieve_cookbook` |
| Postgres version | 18 |
| Owner role | `genevieve_cookbook_owner` |

This project was created fresh for this product after inspecting three
existing Neon projects in the account and confirming, by looking at their
actual branches and tables (not just their names), that all three were
unrelated live production apps — two personal finance trackers and a legal
practice-management system ("Irene"). None was reused.

## 1–2. Migrations applied

Both schema files in `04_PRODUCTION_STARTER/schema/` were applied in order
to a clean database:

- `001_initial_schema.sql` — core catalogue and household tables
  (`recipes`, `ingredients`, `recipe_ingredients`, `swap_groups`,
  `swap_options`, `unit_conversions`, `households`, `pantry_items`,
  `price_book_items`, `favourites`, `meal_plans`, `meal_plan_items`,
  `subscriptions`, `audit_events`).
- `002_dietary_requirements.sql` — dietary engine tables
  (`household_members`, `dietary_requirement_definitions`,
  `member_dietary_requirements`, `ingredient_dietary_attributes`,
  `recipe_requirement_assessments`, `dietary_substitution_rules`,
  `professional_nutrition_targets`, `custom_dietary_rules`).

**Real defect found and fixed in `001_initial_schema.sql`:** the original
`unit_conversions` table declared `PRIMARY KEY (from_unit_code, to_unit_code,
ingredient_id)`. Since `ingredient_id` is `NULL` for universal conversions
(e.g. kg↔g) but must be a specific ingredient for reference conversions
(e.g. cup→g for broccoli), a composite primary key over a nullable column
is unsound — and in practice Postgres made the column implicitly `NOT NULL`
by virtue of being part of a `PRIMARY KEY`, which rejected every universal
conversion row on insert. Discovered by actually seeding the table, not by
inspection. Fixed by:

1. Dropping the composite primary key.
2. Adding `ALTER TABLE unit_conversions ALTER COLUMN ingredient_id DROP NOT
   NULL` — dropping the constraint alone does **not** clear the column's
   `attnotnull` flag in Postgres; this explicit step is required.
3. Replacing the primary key with two partial unique indexes:
   `unit_conversions_specific_uq` (`ingredient_id IS NOT NULL`) and
   `unit_conversions_universal_uq` (`ingredient_id IS NULL`).

This fix is committed in the schema file itself (not just applied live), so
the migration is reproducible from zero on a new branch or project without
hitting the same defect. Re-running both files against a fresh database was
used as the "reproducible from zero" check for the gate.

## 3. Seed data

All catalogue data was generated from the frozen pack sources (not
hand-typed) via a new script, `04_PRODUCTION_STARTER/scripts/build_seed_sql.py`,
and loaded via the Neon MCP `run_sql`/`run_sql_transaction` tools:

| Table | Rows | Source |
|---|---:|---|
| `ingredients` | 151 | `08_CANONICAL_INGREDIENT_MODEL/canonical_ingredients_v1.json` |
| `unit_conversions` | 14 | `08_CANONICAL_INGREDIENT_MODEL/unit_conversions_v1.json` |
| `swap_groups` | 20 | `04_PRODUCTION_STARTER/data/recipe_catalog_v1.json` (`swapMap`) |
| `swap_options` | 136 | same |
| `recipes` | 800 | same (`recipes`) |
| `recipe_ingredients` | 3,840 | same (`recipes[].ingredients`) |
| `dietary_requirement_definitions` | 95 | `07_DIETARY_REQUIREMENTS_ENGINE/DIETARY_TAXONOMY.json` |
| `ingredient_dietary_attributes` | 365 | `07_DIETARY_REQUIREMENTS_ENGINE/ingredient_dietary_attributes_v1.json` |
| `recipe_requirement_assessments` | 33,600 | `07_DIETARY_REQUIREMENTS_ENGINE/recipe_requirement_assessments_v1.json` |

**Reconciliation (the gate's explicit numeric check):** 800 recipes and
3,840 recipe-ingredient lines were confirmed to reconcile after seeding —
row counts, meal-type/family cardinality, freezer/lunchbox/vegetarian
boolean totals, and the summed base quantity across all lines were computed
independently from the source JSON and compared against the seeded
database; all matched exactly. `recipe_requirement_assessments` was
verified more strongly: the full 33,600-row assessment set was checksummed
(MD5) against the source file and matched byte-for-byte before being
written into the real table, and the loaded state distribution (26,861
MEETS / 4,023 EXCLUDED / 2,716 UNVERIFIED / 0 ADAPTABLE) matches the
source's own recorded `state_counts` exactly. Every ingredient in
`ingredient_dietary_attributes` still carries an `ANIMAL_DERIVED` row (the
Phase 2.2 build-time invariant), now checked against the live database
rather than only the source JSON.

**Real data gap found (not fixed — a content gap, not a defect in this
phase's work):** 23 of the 43 distinct `swap_group_code` values referenced
by `recipe_ingredients` rows (1,165 of 3,840 lines) have no matching entry
in `swap_groups`/`swap_options` — e.g. `Bake Base`, `Curry Base`, `Dressing`,
`Egg`, `Stock`. `04_PRODUCTION_STARTER/data/recipe_catalog_v1.json`'s
`swapMap` only ever defined 20 of the ~43 group codes actually used across
`recipes[].ingredients[].swapGroup`. This is a genuine gap in the V1 pack
content (undocumented swap groups), not something Phase 5 introduced or can
correct — the missing swap-option lists don't exist anywhere in the source
data to seed from. Flagging for the recipe-content track; the affected
recipe lines still have correct ingredients, quantities and units, they
just have no alternate-ingredient list surfaced for that particular line's
swap group yet.

**Context-budget note (methodology, not a defect):** loading the SQL for
this seed initially proved far more expensive than expected — reading and
re-emitting the raw generated `recipes` INSERT text cost roughly 0.77
tokens per byte, and the uncompressed `recipe_requirement_assessments`
INSERT would have cost an estimated several million tokens. The seed
generator was rewritten to dictionary-encode repeated text (819 distinct
strings covering meal types, families, method text, swap notes, and
explanations, each stored once and referenced by a small integer) and, for
`recipe_requirement_assessments` specifically, to encode each of the 33,600
rows as a 4-character token (1 state character + a 3-digit index into 455
distinct explanation strings) reconstructed inside Postgres via
`generate_series` and `substring` rather than transmitted as 33,600
explicit rows. This cut the total transmitted SQL from an estimated ~6.4 MB
to 410 KB (a 16× reduction) with no loss of fidelity — verified by the
MD5 checksum match above.

## 4. Indexes and constraints

Already present in the schema as applied (not added separately in this
phase): primary keys on every table, foreign keys from `recipe_ingredients`,
`ingredient_dietary_attributes`, `recipe_requirement_assessments`,
`dietary_substitution_rules`, `professional_nutrition_targets`,
`custom_dietary_rules`, `member_dietary_requirements`, `pantry_items`,
`price_book_items`, `favourites`, `meal_plans`, and `meal_plan_items` back
to their parent tables; `CHECK` constraints on suitability/enforcement/
evidence-state enums and on positive quantities; `households_owner_user_id_idx`,
`price_book_household_ingredient_idx`, and `audit_events_created_at_idx` as
explicit secondary indexes; the two partial unique indexes on
`unit_conversions` described above.

## 5. Least-privilege application database role

Created `genevieve_app` (login role, Neon-managed password) for the future
Cloudflare Worker to use instead of the `genevieve_cookbook_owner` role.
Grants, verified against `information_schema.role_table_grants`:

- **Read-only** (`SELECT`) on every catalogue/reference table the app
  reads but never writes: `ingredients`, `unit_conversions`, `swap_groups`,
  `swap_options`, `recipes`, `recipe_ingredients`,
  `dietary_requirement_definitions`, `ingredient_dietary_attributes`,
  `recipe_requirement_assessments`, `dietary_substitution_rules`.
- **Read-write** (`SELECT, INSERT, UPDATE, DELETE`) on every
  household/user-generated table: `households`, `household_members`,
  `member_dietary_requirements`, `pantry_items`, `price_book_items`,
  `favourites`, `meal_plans`, `meal_plan_items`,
  `professional_nutrition_targets`, `custom_dietary_rules`, `subscriptions`.
- **Append-only** (`SELECT, INSERT`, no `UPDATE`/`DELETE`) on
  `audit_events`, so the app can write audit records but never alter or
  erase them.
- `PUBLIC` access to every catalogue table was explicitly revoked.
- Default privileges for any *future* table created by the owner role
  default to `SELECT` only for `genevieve_app` — a new table must be
  explicitly granted write access, not implicitly get it.
- No `DROP`/`ALTER`/`TRUNCATE`/`REFERENCES`/`TRIGGER` grants anywhere, and
  no role-management or database-creation grants were made to this role by
  this phase's work.

**Disclosed limitation (platform-level, not something this phase could
fix):** every Postgres role Neon creates — including `genevieve_app` and
the project's own owner role — is provisioned with instance-level
`CREATEDB` and `CREATEROLE` attributes by default. Two independent attempts
to strip these (`ALTER ROLE genevieve_app NOCREATEDB NOCREATEROLE` run both
as the branch owner and attempted via `SET ROLE`) were rejected with
`permission denied` — Neon does not expose a role with the authority to
change this on its platform, including to the project owner. This does not
weaken the object-level grants above (`genevieve_app` still cannot read or
write anything beyond what's explicitly granted), but it is a real gap
against a strict definition of least privilege and is recorded here rather
than glossed over.

**Verification performed:** the object-level grants were confirmed by
querying `information_schema.role_table_grants` directly (see table above)
and by confirming `PUBLIC` has no residual grants on catalogue tables. A
live connection test as `genevieve_app` (`SET ROLE genevieve_app`, then
querying as that role) was attempted from the same session and rejected
with `permission denied to set role` — the owner role is not a member of
`genevieve_app`, which is expected and correct (it stops the owner
accidentally acting as the lower-privileged role, and confirms `SET ROLE`
can't be used to bypass the separation). A full end-to-end connection test
using `genevieve_app`'s own password was not possible from this sandbox:
outbound raw Postgres connections are blocked by the environment's network
policy (confirmed by both a `psql` attempt and a direct HTTPS attempt to
Neon's serverless-driver endpoint, both rejected by the egress proxy).
The Cloudflare Worker built in Phase 6 will be the first real end-to-end
test of this role's connection.

## 6. Backup / recovery policy

Neon provides continuous point-in-time recovery (PITR) rather than
scheduled snapshot backups. This project's `history_retention_seconds` is
**21,600 seconds (6 hours)** — the platform default for a `free_v3`
subscription tier, confirmed via `describe_project`. In practice this means
any point in the last 6 hours of write history can be restored to, but nothing
older. This is disclosed as-is rather than assumed adequate: a 6-hour
window is a real limitation for a production consumer app (e.g. it would
not cover recovering from a mistake discovered the next day), and widening
it requires a paid Neon plan — a cost/product decision outside this
phase's scope, flagged here for the product owner rather than decided
unilaterally.

## GREEN gate assessment

| Criterion | Status |
|---|---|
| Migrations reproducible from zero | **GREEN** — both schema files apply cleanly to an empty database, including the `unit_conversions` fix committed in-file |
| 800 recipes and 3,840 ingredient lines reconcile after seed | **GREEN** — verified by independent aggregate cross-checks and (for the larger dietary table) a full MD5 checksum match |
| Least-privilege role works | **PARTIAL** — object-level grants built and verified correct by direct inspection; the Neon-platform `CREATEDB`/`CREATEROLE` default could not be removed (disclosed above) and a live network connection test could not be run from this sandbox |

Overall: **PARTIAL**, on the same honest basis as the Phase 3 report — the
data and migration work is complete and verified, and the one open item is
an environment/platform constraint outside this session's control, not
unfinished work.
