BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS recipes (
  recipe_id text PRIMARY KEY,
  meal_type text NOT NULL,
  recipe_name text NOT NULL,
  base_family text NOT NULL,
  base_serves numeric(8,2) NOT NULL CHECK (base_serves > 0),
  prep_min integer NOT NULL DEFAULT 0 CHECK (prep_min >= 0),
  cook_min integer NOT NULL DEFAULT 0 CHECK (cook_min >= 0),
  budget_tier text,
  primary_protein text,
  carb_base text,
  produce_focus text,
  freezer_friendly boolean NOT NULL DEFAULT false,
  lunchbox_friendly boolean NOT NULL DEFAULT false,
  vegetarian_base boolean NOT NULL DEFAULT false,
  gf_adaptable boolean NOT NULL DEFAULT false,
  df_adaptable boolean NOT NULL DEFAULT false,
  one_pan_pot boolean NOT NULL DEFAULT false,
  method_text text NOT NULL,
  mix_change_notes text,
  public_launch_approved boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingredients (
  ingredient_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_name text NOT NULL UNIQUE,
  quantity_dimension text NOT NULL DEFAULT 'manual',
  canonical_unit_code text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
  recipe_id text NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
  line_no integer NOT NULL,
  ingredient_id uuid NOT NULL REFERENCES ingredients(ingredient_id),
  base_qty numeric(14,4) NOT NULL CHECK (base_qty >= 0),
  unit_code text NOT NULL,
  optional boolean NOT NULL DEFAULT false,
  swap_group_code text,
  PRIMARY KEY (recipe_id, line_no)
);

CREATE TABLE IF NOT EXISTS swap_groups (
  swap_group_code text PRIMARY KEY,
  display_name text NOT NULL
);

CREATE TABLE IF NOT EXISTS swap_options (
  swap_group_code text NOT NULL REFERENCES swap_groups(swap_group_code) ON DELETE CASCADE,
  option_order integer NOT NULL,
  ingredient_name text NOT NULL,
  PRIMARY KEY (swap_group_code, option_order)
);

CREATE TABLE IF NOT EXISTS unit_conversions (
  from_unit_code text NOT NULL,
  to_unit_code text NOT NULL,
  ingredient_id uuid REFERENCES ingredients(ingredient_id),
  multiplier numeric(18,8) NOT NULL CHECK (multiplier > 0),
  verified boolean NOT NULL DEFAULT false,
  notes text
);
-- ingredient_id is nullable (NULL = universal conversion, e.g. kg<->g, that
-- applies to any ingredient -- see 08_CANONICAL_INGREDIENT_MODEL). A
-- composite PRIMARY KEY including ingredient_id would make it implicitly
-- NOT NULL in Postgres, so uniqueness is two partial indexes instead: one
-- per specific ingredient, one for the universal (NULL-ingredient) rows.
-- ingredient_id has no CREATE TABLE-level NOT NULL, but a column that was
-- ever part of a PRIMARY KEY keeps attnotnull=true even after the
-- constraint is dropped -- ALTER COLUMN ... DROP NOT NULL below is required,
-- not just dropping the constraint (found by actually seeding this table).
ALTER TABLE unit_conversions ALTER COLUMN ingredient_id DROP NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS unit_conversions_specific_uq ON unit_conversions (from_unit_code, to_unit_code, ingredient_id) WHERE ingredient_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS unit_conversions_universal_uq ON unit_conversions (from_unit_code, to_unit_code) WHERE ingredient_id IS NULL;

CREATE TABLE IF NOT EXISTS households (
  household_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id text NOT NULL,
  display_name text,
  default_serves integer NOT NULL DEFAULT 4 CHECK (default_serves > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS households_owner_user_id_idx ON households(owner_user_id);

CREATE TABLE IF NOT EXISTS pantry_items (
  household_id uuid NOT NULL REFERENCES households(household_id) ON DELETE CASCADE,
  ingredient_id uuid NOT NULL REFERENCES ingredients(ingredient_id),
  quantity numeric(18,4) NOT NULL CHECK (quantity >= 0),
  unit_code text NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (household_id, ingredient_id, unit_code)
);

CREATE TABLE IF NOT EXISTS price_book_items (
  price_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id uuid NOT NULL REFERENCES households(household_id) ON DELETE CASCADE,
  ingredient_id uuid NOT NULL REFERENCES ingredients(ingredient_id),
  store_source text,
  pack_price numeric(12,2) NOT NULL CHECK (pack_price >= 0),
  pack_qty numeric(18,4) NOT NULL CHECK (pack_qty > 0),
  pack_unit_code text NOT NULL,
  source_type text NOT NULL DEFAULT 'USER',
  checked_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS price_book_household_ingredient_idx ON price_book_items(household_id, ingredient_id);

CREATE TABLE IF NOT EXISTS favourites (
  household_id uuid NOT NULL REFERENCES households(household_id) ON DELETE CASCADE,
  recipe_id text NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (household_id, recipe_id)
);

CREATE TABLE IF NOT EXISTS meal_plans (
  meal_plan_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id uuid NOT NULL REFERENCES households(household_id) ON DELETE CASCADE,
  week_start date NOT NULL,
  weekly_budget numeric(12,2),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (household_id, week_start)
);

CREATE TABLE IF NOT EXISTS meal_plan_items (
  meal_plan_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  meal_plan_id uuid NOT NULL REFERENCES meal_plans(meal_plan_id) ON DELETE CASCADE,
  meal_date date NOT NULL,
  meal_slot text NOT NULL,
  recipe_id text NOT NULL REFERENCES recipes(recipe_id),
  target_serves numeric(8,2) NOT NULL CHECK (target_serves > 0),
  leftover_source_item_id uuid REFERENCES meal_plan_items(meal_plan_item_id),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS subscriptions (
  owner_user_id text PRIMARY KEY,
  stripe_customer_id text,
  stripe_subscription_id text,
  entitlement text NOT NULL DEFAULT 'FREE',
  subscription_status text,
  current_period_end timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_events (
  event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id text,
  household_id uuid,
  event_type text NOT NULL,
  event_data jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS audit_events_created_at_idx ON audit_events(created_at DESC);

COMMIT;
