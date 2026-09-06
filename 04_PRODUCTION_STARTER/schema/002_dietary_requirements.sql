BEGIN;

CREATE TABLE IF NOT EXISTS household_members (
  member_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id uuid NOT NULL REFERENCES households(household_id) ON DELETE CASCADE,
  display_name text NOT NULL,
  age_band text,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS household_members_household_idx ON household_members(household_id);

CREATE TABLE IF NOT EXISTS dietary_requirement_definitions (
  requirement_code text PRIMARY KEY,
  requirement_class text NOT NULL,
  display_name text NOT NULL,
  high_consequence boolean NOT NULL DEFAULT false,
  professional_plan_only boolean NOT NULL DEFAULT false,
  claim_notes text,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS member_dietary_requirements (
  member_requirement_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id uuid NOT NULL REFERENCES household_members(member_id) ON DELETE CASCADE,
  requirement_code text NOT NULL REFERENCES dietary_requirement_definitions(requirement_code),
  enforcement_level text NOT NULL CHECK (enforcement_level IN ('HARD_EXCLUDE','REQUIRE_VERIFIED','PREFER','INFORMATION_ONLY')),
  source_type text NOT NULL DEFAULT 'USER' CHECK (source_type IN ('USER','CLINICIAN_PLAN','CARE_PLAN','SYSTEM_DEFAULT')),
  notes text,
  starts_at date,
  ends_at date,
  verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (member_id, requirement_code)
);

CREATE TABLE IF NOT EXISTS ingredient_dietary_attributes (
  ingredient_id uuid NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE CASCADE,
  attribute_code text NOT NULL,
  attribute_value text NOT NULL,
  evidence_state text NOT NULL DEFAULT 'UNVERIFIED' CHECK (evidence_state IN ('VERIFIED_PRESENT','VERIFIED_ABSENT','CONDITIONAL','UNVERIFIED')),
  source_reference text,
  verified_at timestamptz,
  PRIMARY KEY (ingredient_id, attribute_code)
);

CREATE TABLE IF NOT EXISTS recipe_requirement_assessments (
  recipe_id text NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
  requirement_code text NOT NULL REFERENCES dietary_requirement_definitions(requirement_code),
  suitability_state text NOT NULL CHECK (suitability_state IN ('MEETS','ADAPTABLE','EXCLUDED','UNVERIFIED')),
  explanation text NOT NULL,
  reviewed boolean NOT NULL DEFAULT false,
  reviewed_at timestamptz,
  review_source text,
  PRIMARY KEY (recipe_id, requirement_code)
);

CREATE TABLE IF NOT EXISTS dietary_substitution_rules (
  substitution_rule_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_ingredient_id uuid NOT NULL REFERENCES ingredients(ingredient_id),
  substitute_ingredient_id uuid NOT NULL REFERENCES ingredients(ingredient_id),
  function_code text NOT NULL,
  requirement_code text REFERENCES dietary_requirement_definitions(requirement_code),
  suitability_state text NOT NULL DEFAULT 'UNVERIFIED' CHECK (suitability_state IN ('MEETS','ADAPTABLE','EXCLUDED','UNVERIFIED')),
  preparation_notes text,
  verified boolean NOT NULL DEFAULT false,
  verified_at timestamptz,
  UNIQUE (source_ingredient_id, substitute_ingredient_id, function_code, requirement_code)
);

CREATE TABLE IF NOT EXISTS professional_nutrition_targets (
  target_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id uuid NOT NULL REFERENCES household_members(member_id) ON DELETE CASCADE,
  target_code text NOT NULL,
  target_value numeric(18,6),
  target_unit text,
  source_type text NOT NULL CHECK (source_type IN ('USER','CLINICIAN_PLAN','CARE_PLAN')),
  notes text,
  starts_at date,
  ends_at date,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS custom_dietary_rules (
  custom_rule_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id uuid NOT NULL REFERENCES household_members(member_id) ON DELETE CASCADE,
  rule_type text NOT NULL CHECK (rule_type IN ('CUSTOM_EXCLUSION','CUSTOM_REQUIREMENT','CUSTOM_PREFERENCE')),
  rule_label text NOT NULL,
  canonical_ingredient_id uuid REFERENCES ingredients(ingredient_id),
  enforcement_level text NOT NULL CHECK (enforcement_level IN ('HARD_EXCLUDE','REQUIRE_VERIFIED','PREFER','INFORMATION_ONLY')),
  notes text,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

COMMIT;
