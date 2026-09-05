/**
 * Phase 2.6 -- Medical / Professional-Plan Boundaries.
 *
 * DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md section F (clinician-directed
 * nutritional controls): "The engine should store the user-entered or
 * clinician-provided target. It must not invent a therapeutic target."
 *
 * GREEN gate: "medical modes cannot activate from an AI inference about the
 * user's health; they require explicit user/professional-plan configuration."
 *
 * This module is the structural enforcement of that gate, not a policy
 * statement about it:
 * - `createProfessionalNutritionTarget` is the ONLY way to produce a
 *   ProfessionalNutritionTarget in this codebase, and it throws if any of
 *   target_value / target_unit / source_type is missing or invalid. There is
 *   no code path here (or anywhere else in this dietary engine) that derives
 *   a numeric target from a diagnosis string, another member's data, a
 *   recipe's content, or any other inferred signal -- the only inputs this
 *   function accepts are the exact fields a clinician/dietitian/user would
 *   hand over explicitly.
 * - `checkClinicianDirectedActivation` / `applyProfessionalTargetGate` mean a
 *   clinician-directed requirement flag (SODIUM_TARGET, PKU_PHENYLALANINE_PLAN,
 *   etc. -- schema/002_dietary_requirements.sql's member_dietary_requirements)
 *   is inert -- filtered out of the household's combined requirement set
 *   entirely -- unless it is backed by a real, explicitly created target
 *   record for that same member and code. Turning on the flag alone (which
 *   an AI-driven UI could conceivably do from a passing remark) does nothing.
 */
import { CombinedHouseholdRequirements, CombinedRequirementEntry, EnforcementLevel, ENFORCEMENT_PRECEDENCE } from "./household";

export type ProfessionalTargetSource = "USER" | "CLINICIAN_PLAN" | "CARE_PLAN";

/** The 10 named clinician-directed codes from DIETARY_TAXONOMY.json's
 * `clinician_directed` class. "Other prescribed nutrient limit entered as a
 * custom professional plan" (master blueprint section F) is intentionally
 * NOT a fixed code here -- see `isClinicianDirectedCode` below, which also
 * treats any caller-supplied code paired with a CLINICIAN_PLAN/CARE_PLAN
 * source as clinician-directed, so a custom professional plan gets the same
 * activation gate without this module needing to know its label in advance. */
export const NAMED_CLINICIAN_DIRECTED_CODES = new Set([
  "SODIUM_TARGET", "CARBOHYDRATE_TARGET", "ENERGY_TARGET", "PROTEIN_TARGET",
  "POTASSIUM_LIMIT", "PHOSPHATE_LIMIT", "FLUID_PLAN", "FAT_TARGET",
  "FIBRE_TARGET", "PKU_PHENYLALANINE_PLAN",
]);

export interface ProfessionalNutritionTarget {
  target_id: string;
  member_id: string;
  target_code: string;
  target_value: number;
  target_unit: string;
  source_type: ProfessionalTargetSource;
  notes?: string;
  starts_at?: string;
  ends_at?: string;
}

export interface CreateProfessionalNutritionTargetInput {
  target_id: string;
  member_id: string;
  target_code: string;
  target_value: number;
  target_unit: string;
  source_type: ProfessionalTargetSource;
  notes?: string;
  starts_at?: string;
  ends_at?: string;
}

/**
 * The only constructor for a ProfessionalNutritionTarget. Every field the
 * blueprint requires must be an explicit, caller-supplied value -- this
 * function has no default, no lookup, and no inference step for
 * target_value/target_unit. If a caller cannot supply a real number and
 * unit, that is the correct place to stop, not a place for this function to
 * guess.
 */
export function createProfessionalNutritionTarget(
  input: CreateProfessionalNutritionTargetInput,
): ProfessionalNutritionTarget {
  if (typeof input.target_value !== "number" || !Number.isFinite(input.target_value)) {
    throw new Error(
      `Professional nutrition target for ${input.member_id}/${input.target_code} must carry an explicit finite ` +
        "numeric target_value. GENEVIEVE never invents a therapeutic target -- supply the value the user, " +
        "clinician or care plan actually gave.",
    );
  }
  if (!input.target_unit || input.target_unit.trim() === "") {
    throw new Error(`Professional nutrition target for ${input.member_id}/${input.target_code} must carry an explicit target_unit.`);
  }
  if (input.source_type !== "USER" && input.source_type !== "CLINICIAN_PLAN" && input.source_type !== "CARE_PLAN") {
    throw new Error(
      `Invalid source_type "${input.source_type}" for a professional nutrition target -- must be USER, ` +
        "CLINICIAN_PLAN or CARE_PLAN. There is no inferred/system-generated source: a target always traces back " +
        "to a person who supplied it.",
    );
  }
  if (!input.target_code || input.target_code.trim() === "") {
    throw new Error("Professional nutrition target must carry an explicit target_code.");
  }
  return { ...input };
}

/** A requirement_code counts as clinician-directed either because it's one
 * of the 10 named codes, or because a caller has attached a
 * CLINICIAN_PLAN/CARE_PLAN-sourced target to it under a custom label
 * ("Other prescribed nutrient limit entered as a custom professional plan").
 * A USER-sourced custom target does NOT make an arbitrary code
 * clinician-directed -- only the named codes and clinician/care-plan-backed
 * custom ones carry the activation gate below. */
export function isClinicianDirectedCode(code: string, targets: ProfessionalNutritionTarget[]): boolean {
  if (NAMED_CLINICIAN_DIRECTED_CODES.has(code)) return true;
  return targets.some(
    (t) => t.target_code === code && (t.source_type === "CLINICIAN_PLAN" || t.source_type === "CARE_PLAN"),
  );
}

function isTargetActiveOn(target: ProfessionalNutritionTarget, asOf: string): boolean {
  if (target.starts_at && asOf < target.starts_at) return false;
  if (target.ends_at && asOf > target.ends_at) return false;
  return true;
}

export interface ClinicianDirectedActivationCheck {
  requirementCode: string;
  memberId: string;
  active: boolean;
  reason: string;
}

/**
 * Is `requirementCode` actually usable for `memberId` right now? A
 * clinician-directed code is active only when backed by a real, current
 * ProfessionalNutritionTarget for that exact member and code. A
 * non-clinician-directed code is always active as far as this module is
 * concerned (it isn't this gate's business) -- see household.ts for the
 * general enforcement-level logic every other requirement code uses.
 */
export function checkClinicianDirectedActivation(
  requirementCode: string,
  memberId: string,
  targets: ProfessionalNutritionTarget[],
  asOf: string = new Date().toISOString().slice(0, 10),
): ClinicianDirectedActivationCheck {
  if (!isClinicianDirectedCode(requirementCode, targets)) {
    return { requirementCode, memberId, active: true, reason: "Not a clinician-directed code; no professional target required to activate." };
  }
  const backing = targets.find(
    (t) => t.member_id === memberId && t.target_code === requirementCode && isTargetActiveOn(t, asOf),
  );
  if (!backing) {
    return {
      requirementCode, memberId, active: false,
      reason: `No current professional_nutrition_targets record on file for this member/${requirementCode}. ` +
        "A clinician-directed mode never activates from an inferred health condition -- it requires an explicit " +
        "target on file, which this member does not have (or it has expired/not yet started).",
    };
  }
  return {
    requirementCode, memberId, active: true,
    reason: `Backed by an explicit target: ${backing.target_value} ${backing.target_unit} (source: ${backing.source_type}).`,
  };
}

/**
 * Post-processes Phase 2.3's combineHouseholdRequirements() output: any
 * clinician-directed entry loses the contribution of every member who lacks
 * a backing target, and disappears entirely if that leaves zero
 * contributors. Non-clinician-directed entries pass through untouched. This
 * is where the GREEN gate becomes visible in the actual request pipeline,
 * not just in this module's own unit tests: a household combination that
 * included an unbacked SODIUM_TARGET flag comes out of this function with
 * that flag gone, exactly as if it had never been set.
 */
export function applyProfessionalTargetGate(
  combined: CombinedHouseholdRequirements,
  targets: ProfessionalNutritionTarget[],
  asOf: string = new Date().toISOString().slice(0, 10),
): CombinedHouseholdRequirements {
  const allEntries: CombinedRequirementEntry[] = [
    ...combined.hardExclusions,
    ...combined.requireVerified,
    ...combined.preferences,
    ...combined.informationOnly,
  ];

  const gated: CombinedRequirementEntry[] = [];
  for (const entry of allEntries) {
    if (!isClinicianDirectedCode(entry.key, targets)) {
      gated.push(entry);
      continue;
    }
    const survivors = entry.perMember.filter(
      (m) => checkClinicianDirectedActivation(entry.key, m.member_id, targets, asOf).active,
    );
    if (survivors.length === 0) continue; // fully deactivated: nobody has a backing target
    const effectiveEnforcement = survivors.reduce<EnforcementLevel>(
      (acc, m) => (ENFORCEMENT_PRECEDENCE[m.enforcement_level] > ENFORCEMENT_PRECEDENCE[acc] ? m.enforcement_level : acc),
      survivors[0].enforcement_level,
    );
    gated.push({ key: entry.key, effectiveEnforcement, perMember: survivors });
  }

  return {
    mealMemberIds: combined.mealMemberIds,
    hardExclusions: gated.filter((e) => e.effectiveEnforcement === "HARD_EXCLUDE"),
    requireVerified: gated.filter((e) => e.effectiveEnforcement === "REQUIRE_VERIFIED"),
    preferences: gated.filter((e) => e.effectiveEnforcement === "PREFER"),
    informationOnly: gated.filter((e) => e.effectiveEnforcement === "INFORMATION_ONLY"),
  };
}
