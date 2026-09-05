/**
 * Phase 2.3 -- Household Member Requirement Model.
 *
 * Types and combination logic for household_members / member_dietary_requirements
 * / custom_dietary_rules (schema/002_dietary_requirements.sql), matching the
 * field contract in 07_DIETARY_REQUIREMENTS_ENGINE/HOUSEHOLD_MEMBER_PROFILE_CONTRACT.md.
 *
 * Scope boundary: this module resolves *which requirements apply, at what
 * severity, for which members* when a meal is shared by a selected group of
 * household members (steps 1-2 of the "Recipe evaluation order" in
 * DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md: "Resolve selected household
 * members" and "Combine hard exclusions first"). It does not evaluate a
 * recipe against those requirements -- that needs the ingredient attribute
 * model (Phase 2.2, done) plus recipe classification (Phase 2.4) and
 * substitution mapping (Phase 2.5), neither of which exist yet.
 */

export type EnforcementLevel = "HARD_EXCLUDE" | "REQUIRE_VERIFIED" | "PREFER" | "INFORMATION_ONLY";
export type SourceType = "USER" | "CLINICIAN_PLAN" | "CARE_PLAN" | "SYSTEM_DEFAULT";
export type CustomRuleType = "CUSTOM_EXCLUSION" | "CUSTOM_REQUIREMENT" | "CUSTOM_PREFERENCE";

/** Highest number wins when the same requirement_code appears on multiple
 * members in a shared meal -- the group must satisfy the strictest applicable
 * level, per DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md's evaluation order. */
const ENFORCEMENT_PRECEDENCE: Record<EnforcementLevel, number> = {
  HARD_EXCLUDE: 4,
  REQUIRE_VERIFIED: 3,
  PREFER: 2,
  INFORMATION_ONLY: 1,
};

export interface MemberDietaryRequirement {
  requirement_code: string;
  enforcement_level: EnforcementLevel;
  source_type: SourceType;
  notes?: string;
  starts_at?: string; // ISO date
  ends_at?: string; // ISO date
  verified_at?: string; // ISO timestamp
  /** Never surfaced in combined/explanation output -- see privacy note below. */
  professional_plan_reference?: string;
}

export interface CustomDietaryRule {
  custom_rule_id: string;
  rule_type: CustomRuleType;
  rule_label: string;
  canonical_ingredient_id?: string;
  enforcement_level: EnforcementLevel;
  notes?: string;
  active: boolean;
}

export interface HouseholdMember {
  member_id: string;
  household_id: string;
  display_name: string;
  age_band?: string;
  active: boolean;
  requirements: MemberDietaryRequirement[];
  custom_rules: CustomDietaryRule[];
}

/** One requirement_code (or custom rule label), as it applies across every
 * member selected for a meal. Never collapses members into one value --
 * `perMember` always carries every contributing member's own enforcement
 * level, so no profile can overwrite another's. */
export interface CombinedRequirementEntry {
  key: string; // requirement_code, or "CUSTOM:<rule_label>" for custom rules
  effectiveEnforcement: EnforcementLevel; // strictest across contributing members
  perMember: Array<{
    member_id: string;
    display_name: string;
    enforcement_level: EnforcementLevel;
    source_type: SourceType;
    notes?: string;
  }>;
}

export interface CombinedHouseholdRequirements {
  mealMemberIds: string[];
  hardExclusions: CombinedRequirementEntry[];
  requireVerified: CombinedRequirementEntry[];
  preferences: CombinedRequirementEntry[];
  informationOnly: CombinedRequirementEntry[];
}

function isActiveOn(req: { starts_at?: string; ends_at?: string }, asOf: string): boolean {
  if (req.starts_at && asOf < req.starts_at) return false;
  if (req.ends_at && asOf > req.ends_at) return false;
  return true;
}

/**
 * Combine dietary requirements across the household members selected for one
 * meal. Every selected member must be `active`; inactive members and
 * requirements outside their starts_at/ends_at window on `asOf` are excluded
 * from the meal, not silently kept.
 *
 * GREEN gate (Phase 2.3): different members can carry conflicting
 * requirements without one profile overwriting another. Verified by
 * household.test.ts using the four-member household from
 * DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md's "Core household use case".
 */
export function combineHouseholdRequirements(
  members: HouseholdMember[],
  mealMemberIds: string[],
  asOf: string = new Date().toISOString().slice(0, 10),
): CombinedHouseholdRequirements {
  const selected = members.filter((m) => mealMemberIds.includes(m.member_id));
  const missing = mealMemberIds.filter((id) => !selected.some((m) => m.member_id === id));
  if (missing.length) {
    throw new Error(`Unknown household member id(s) selected for this meal: ${missing.join(", ")}`);
  }
  const inactive = selected.filter((m) => !m.active);
  if (inactive.length) {
    throw new Error(
      `Inactive member(s) cannot be selected for a meal: ${inactive.map((m) => m.member_id).join(", ")}`,
    );
  }

  const byKey = new Map<string, CombinedRequirementEntry>();

  for (const member of selected) {
    for (const req of member.requirements) {
      if (!isActiveOn(req, asOf)) continue;
      addContribution(byKey, req.requirement_code, member, req.enforcement_level, req.source_type, req.notes);
    }
    for (const rule of member.custom_rules) {
      if (!rule.active) continue;
      addContribution(
        byKey,
        `CUSTOM:${rule.rule_label}`,
        member,
        rule.enforcement_level,
        "USER",
        rule.notes,
      );
    }
  }

  const entries = [...byKey.values()];
  return {
    mealMemberIds,
    hardExclusions: entries.filter((e) => e.effectiveEnforcement === "HARD_EXCLUDE"),
    requireVerified: entries.filter((e) => e.effectiveEnforcement === "REQUIRE_VERIFIED"),
    preferences: entries.filter((e) => e.effectiveEnforcement === "PREFER"),
    informationOnly: entries.filter((e) => e.effectiveEnforcement === "INFORMATION_ONLY"),
  };
}

function addContribution(
  byKey: Map<string, CombinedRequirementEntry>,
  key: string,
  member: HouseholdMember,
  enforcement_level: EnforcementLevel,
  source_type: SourceType,
  notes: string | undefined,
): void {
  let entry = byKey.get(key);
  if (!entry) {
    entry = { key, effectiveEnforcement: enforcement_level, perMember: [] };
    byKey.set(key, entry);
  }
  // Every member's own level is always appended -- never overwritten by
  // another member's contribution for the same key.
  entry.perMember.push({
    member_id: member.member_id,
    display_name: member.display_name,
    enforcement_level,
    source_type,
    notes,
  });
  if (ENFORCEMENT_PRECEDENCE[enforcement_level] > ENFORCEMENT_PRECEDENCE[entry.effectiveEnforcement]) {
    entry.effectiveEnforcement = enforcement_level;
  }
}
