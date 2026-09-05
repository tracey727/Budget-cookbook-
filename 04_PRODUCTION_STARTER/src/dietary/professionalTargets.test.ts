/**
 * Phase 2.6 GREEN-gate check: "medical modes cannot activate from an AI
 * inference about the user's health; they require explicit user/
 * professional-plan configuration." Run via `npm run test:professional`.
 */
import { combineHouseholdRequirements, HouseholdMember } from "./household";
import {
  applyProfessionalTargetGate,
  checkClinicianDirectedActivation,
  createProfessionalNutritionTarget,
  isClinicianDirectedCode,
  ProfessionalNutritionTarget,
} from "./professionalTargets";

let failures = 0;
function check(label: string, condition: boolean): void {
  if (condition) {
    console.log(`PASS ${label}`);
  } else {
    failures++;
    console.error(`FAIL ${label}`);
  }
}

function throws(fn: () => void): boolean {
  try {
    fn();
    return false;
  } catch {
    return true;
  }
}

// --- createProfessionalNutritionTarget refuses to invent anything. ---
check(
  "missing/NaN target_value throws rather than defaulting",
  throws(() =>
    createProfessionalNutritionTarget({
      target_id: "t1", member_id: "A", target_code: "SODIUM_TARGET",
      target_value: NaN, target_unit: "mg/day", source_type: "CLINICIAN_PLAN",
    }),
  ),
);
check(
  "empty target_unit throws",
  throws(() =>
    createProfessionalNutritionTarget({
      target_id: "t2", member_id: "A", target_code: "SODIUM_TARGET",
      target_value: 1500, target_unit: "", source_type: "CLINICIAN_PLAN",
    }),
  ),
);
check(
  "a source_type outside USER/CLINICIAN_PLAN/CARE_PLAN throws -- there is no 'inferred' or 'system' source",
  throws(() =>
    createProfessionalNutritionTarget({
      target_id: "t3", member_id: "A", target_code: "SODIUM_TARGET",
      target_value: 1500, target_unit: "mg/day",
      source_type: "AI_INFERRED" as unknown as "CLINICIAN_PLAN",
    }),
  ),
);
check(
  "a fully explicit target is created successfully",
  createProfessionalNutritionTarget({
    target_id: "t4", member_id: "A", target_code: "SODIUM_TARGET",
    target_value: 1500, target_unit: "mg/day", source_type: "CLINICIAN_PLAN",
  }).target_value === 1500,
);

// --- checkClinicianDirectedActivation ---
const sodiumTarget: ProfessionalNutritionTarget = createProfessionalNutritionTarget({
  target_id: "t5", member_id: "A", target_code: "SODIUM_TARGET",
  target_value: 1500, target_unit: "mg/day", source_type: "CLINICIAN_PLAN",
});
check(
  "SODIUM_TARGET is inactive for a member with no target on file",
  !checkClinicianDirectedActivation("SODIUM_TARGET", "A", []).active,
);
check(
  "SODIUM_TARGET is active once a real target is on file for that member",
  checkClinicianDirectedActivation("SODIUM_TARGET", "A", [sodiumTarget]).active,
);
check(
  "SODIUM_TARGET stays inactive for a DIFFERENT member even if member A has a target",
  !checkClinicianDirectedActivation("SODIUM_TARGET", "B", [sodiumTarget]).active,
);
const expiredTarget = createProfessionalNutritionTarget({
  target_id: "t6", member_id: "A", target_code: "FLUID_PLAN",
  target_value: 1000, target_unit: "mL/day", source_type: "CARE_PLAN", ends_at: "2020-01-01",
});
check(
  "an expired professional target does not activate its requirement today",
  !checkClinicianDirectedActivation("FLUID_PLAN", "A", [expiredTarget], "2026-09-05").active,
);
check(
  "the same target DID activate before its end date",
  checkClinicianDirectedActivation("FLUID_PLAN", "A", [expiredTarget], "2019-06-01").active,
);
check(
  "a non-clinician-directed code (VEGETARIAN) is always active regardless of targets -- this gate doesn't overreach",
  checkClinicianDirectedActivation("VEGETARIAN", "A", []).active,
);

// --- Custom professional plan codes get the same gate; USER-sourced arbitrary codes don't. ---
const customClinicianTarget = createProfessionalNutritionTarget({
  target_id: "t7", member_id: "A", target_code: "CUSTOM_PROTEIN_RESTRICTION",
  target_value: 40, target_unit: "g/day", source_type: "CLINICIAN_PLAN",
});
check(
  "a custom code backed by a CLINICIAN_PLAN target counts as clinician-directed",
  isClinicianDirectedCode("CUSTOM_PROTEIN_RESTRICTION", [customClinicianTarget]),
);
check(
  "an arbitrary code with no clinician/care-plan-sourced target is NOT treated as clinician-directed",
  !isClinicianDirectedCode("SOME_RANDOM_CODE", [customClinicianTarget]),
);

// --- Full pipeline: Phase 2.3 combine -> Phase 2.6 gate. ---
function memberWithSodiumFlag(id: string, enforcement: "HARD_EXCLUDE" | "REQUIRE_VERIFIED"): HouseholdMember {
  return {
    member_id: id, household_id: "H", display_name: id, active: true,
    requirements: [
      { requirement_code: "SODIUM_TARGET", enforcement_level: enforcement, source_type: "CLINICIAN_PLAN" },
      { requirement_code: "VEGETARIAN", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
    ],
    custom_rules: [],
  };
}

{
  const memberA = memberWithSodiumFlag("A", "REQUIRE_VERIFIED");
  const combined = combineHouseholdRequirements([memberA], ["A"]);
  check("before gating, Phase 2.3 alone shows SODIUM_TARGET as active (it doesn't know about targets)", combined.requireVerified.some((e) => e.key === "SODIUM_TARGET"));

  const gatedNoTarget = applyProfessionalTargetGate(combined, []);
  check(
    "an unbacked SODIUM_TARGET flag disappears entirely after the Phase 2.6 gate -- exactly as if never set",
    !gatedNoTarget.requireVerified.some((e) => e.key === "SODIUM_TARGET") &&
      !gatedNoTarget.hardExclusions.some((e) => e.key === "SODIUM_TARGET"),
  );
  check(
    "VEGETARIAN (not clinician-directed) is untouched by the gate",
    gatedNoTarget.hardExclusions.some((e) => e.key === "VEGETARIAN"),
  );

  const gatedWithTarget = applyProfessionalTargetGate(combined, [sodiumTarget]);
  check(
    "SODIUM_TARGET survives the gate once a real target backs it",
    gatedWithTarget.requireVerified.some((e) => e.key === "SODIUM_TARGET"),
  );
}

// --- Multi-member: only the backed member's contribution survives. ---
{
  const memberA = memberWithSodiumFlag("A", "HARD_EXCLUDE"); // backed
  const memberB = memberWithSodiumFlag("B", "REQUIRE_VERIFIED"); // not backed
  const combined = combineHouseholdRequirements([memberA, memberB], ["A", "B"]);
  const gated = applyProfessionalTargetGate(combined, [sodiumTarget]); // only backs member A

  const sodiumEntry = [...gated.hardExclusions, ...gated.requireVerified].find((e) => e.key === "SODIUM_TARGET");
  check("SODIUM_TARGET entry survives because member A is backed", sodiumEntry !== undefined);
  check(
    "only member A's contribution remains -- member B's unbacked flag is dropped, not silently kept",
    sodiumEntry !== undefined && sodiumEntry.perMember.length === 1 && sodiumEntry.perMember[0].member_id === "A",
  );
  check(
    "effective enforcement is recomputed from the surviving member only (A's HARD_EXCLUDE), not B's now-dropped REQUIRE_VERIFIED",
    sodiumEntry !== undefined && sodiumEntry.effectiveEnforcement === "HARD_EXCLUDE" &&
      gated.hardExclusions.some((e) => e.key === "SODIUM_TARGET"),
  );
}

if (failures > 0) {
  throw new Error(`${failures} check(s) failed.`);
}
console.log("\nAll Phase 2.6 professional-target checks passed.");
