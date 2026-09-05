/**
 * Phase 2.3 GREEN-gate check: "different members can carry conflicting
 * requirements without one profile overwriting another."
 *
 * No test framework is wired into this starter yet (package.json has none),
 * so this is a small self-contained assertion script -- run it with:
 *   npx tsc --outDir /tmp/dietary-test-out src/dietary/household.ts src/dietary/household.test.ts \
 *     --target ES2022 --module ESNext --moduleResolution Bundler
 *   node /tmp/dietary-test-out/household.test.js
 * (see PHASE_2_3_HOUSEHOLD_MEMBER_REQUIREMENT_MODEL_REPORT.md for the exact
 * commands used to verify this, including the tsc --noEmit typecheck.)
 */
import { combineHouseholdRequirements, HouseholdMember } from "./household";

let failures = 0;
function check(label: string, condition: boolean): void {
  if (condition) {
    console.log(`PASS ${label}`);
  } else {
    failures++;
    console.error(`FAIL ${label}`);
  }
}

// The "Core household use case" from DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md:
// Member A: vegetarian + lactose avoidance (soft).
// Member B: no dietary restriction.
// Member C: peanut allergy.
// Member D: sensory preference -- sauces separate.
const memberA: HouseholdMember = {
  member_id: "A",
  household_id: "H1",
  display_name: "Member A",
  active: true,
  requirements: [
    { requirement_code: "VEGETARIAN", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
    { requirement_code: "LACTOSE_FREE", enforcement_level: "PREFER", source_type: "USER" },
  ],
  custom_rules: [],
};
const memberB: HouseholdMember = {
  member_id: "B",
  household_id: "H1",
  display_name: "Member B",
  active: true,
  requirements: [],
  custom_rules: [],
};
const memberC: HouseholdMember = {
  member_id: "C",
  household_id: "H1",
  display_name: "Member C",
  active: true,
  requirements: [
    { requirement_code: "ALLERGY_PEANUT", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
  ],
  custom_rules: [],
};
const memberD: HouseholdMember = {
  member_id: "D",
  household_id: "H1",
  display_name: "Member D",
  active: true,
  requirements: [],
  custom_rules: [
    {
      custom_rule_id: "CR1",
      rule_type: "CUSTOM_PREFERENCE",
      rule_label: "Sauces served separately",
      enforcement_level: "PREFER",
      active: true,
    },
  ],
};
// Member E shares Member A's LACTOSE_FREE code but at HARD_EXCLUDE, not PREFER --
// the classic "same code, different severity, different member" case.
const memberE: HouseholdMember = {
  member_id: "E",
  household_id: "H1",
  display_name: "Member E",
  active: true,
  requirements: [
    { requirement_code: "LACTOSE_FREE", enforcement_level: "HARD_EXCLUDE", source_type: "CLINICIAN_PLAN" },
  ],
  custom_rules: [],
};
const memberInactive: HouseholdMember = {
  member_id: "F",
  household_id: "H1",
  display_name: "Member F (inactive)",
  active: false,
  requirements: [{ requirement_code: "PORK_FREE", enforcement_level: "HARD_EXCLUDE", source_type: "USER" }],
  custom_rules: [],
};
const memberExpired: HouseholdMember = {
  member_id: "G",
  household_id: "H1",
  display_name: "Member G",
  active: true,
  requirements: [
    {
      requirement_code: "SODIUM_TARGET",
      enforcement_level: "REQUIRE_VERIFIED",
      source_type: "CLINICIAN_PLAN",
      starts_at: "2020-01-01",
      ends_at: "2020-06-01",
    },
  ],
  custom_rules: [],
};

const allMembers = [memberA, memberB, memberC, memberD, memberE, memberInactive, memberExpired];

// --- Core use case: A + B + C + D share a meal. ---
const combined = combineHouseholdRequirements(allMembers, ["A", "B", "C", "D"], "2026-09-05");

check(
  "vegetarian hard exclusion present from Member A",
  combined.hardExclusions.some((e) => e.key === "VEGETARIAN"),
);
check(
  "peanut allergy hard exclusion present from Member C",
  combined.hardExclusions.some((e) => e.key === "ALLERGY_PEANUT"),
);
check(
  "Member B (no restrictions) does not remove A's or C's hard exclusions",
  combined.hardExclusions.length === 2,
);
check(
  "Member D's sensory preference is preserved as a preference, not dropped or promoted to a hard exclusion",
  combined.preferences.some((e) => e.key === "CUSTOM:Sauces served separately") &&
    !combined.hardExclusions.some((e) => e.key === "CUSTOM:Sauces served separately"),
);
check(
  "Member A's own VEGETARIAN record is still individually attributable to A, not merged away",
  combined.hardExclusions.find((e) => e.key === "VEGETARIAN")!.perMember.length === 1 &&
    combined.hardExclusions.find((e) => e.key === "VEGETARIAN")!.perMember[0].member_id === "A",
);

// --- Same requirement_code, different severity, different members: A (PREFER) + E (HARD_EXCLUDE). ---
const combinedAE = combineHouseholdRequirements(allMembers, ["A", "E"], "2026-09-05");
const lactose = combinedAE.hardExclusions.find((e) => e.key === "LACTOSE_FREE");
check(
  "group-level LACTOSE_FREE escalates to HARD_EXCLUDE because Member E requires it, even though Member A only prefers it",
  lactose !== undefined && lactose.effectiveEnforcement === "HARD_EXCLUDE",
);
check(
  "Member A's own PREFER-level record is NOT overwritten by Member E's HARD_EXCLUDE -- both are visible in perMember",
  lactose !== undefined &&
    lactose.perMember.length === 2 &&
    lactose.perMember.find((m) => m.member_id === "A")?.enforcement_level === "PREFER" &&
    lactose.perMember.find((m) => m.member_id === "E")?.enforcement_level === "HARD_EXCLUDE",
);

// --- A meal that does NOT include Member E must not inherit E's HARD_EXCLUDE. ---
const combinedAOnly = combineHouseholdRequirements(allMembers, ["A"], "2026-09-05");
const lactoseAOnly = combinedAOnly.hardExclusions.find((e) => e.key === "LACTOSE_FREE");
check(
  "excluding Member E from the meal means the group constraint reverts to A's own PREFER level",
  lactoseAOnly === undefined &&
    combinedAOnly.preferences.some((e) => e.key === "LACTOSE_FREE"),
);

// --- Inactive members are never silently included. ---
let threwForInactive = false;
try {
  combineHouseholdRequirements(allMembers, ["A", "F"], "2026-09-05");
} catch {
  threwForInactive = true;
}
check("selecting an inactive member for a meal is rejected, not silently honoured", threwForInactive);

// --- Expired clinician-plan requirement does not apply after its end date. ---
const combinedExpired = combineHouseholdRequirements(allMembers, ["G"], "2026-09-05");
check(
  "a requirement past its ends_at date does not apply to today's meal",
  combinedExpired.requireVerified.length === 0 && combinedExpired.hardExclusions.length === 0,
);
const combinedInWindow = combineHouseholdRequirements(allMembers, ["G"], "2020-03-01");
check(
  "the same requirement DOES apply when asOf falls inside its starts_at/ends_at window",
  combinedInWindow.requireVerified.some((e) => e.key === "SODIUM_TARGET"),
);

// --- Unknown member id is rejected rather than silently ignored. ---
let threwForUnknown = false;
try {
  combineHouseholdRequirements(allMembers, ["does-not-exist"], "2026-09-05");
} catch {
  threwForUnknown = true;
}
check("selecting an unknown member id throws rather than silently proceeding", threwForUnknown);

if (failures > 0) {
  // Thrown (not process.exit) so this script has no @types/node dependency --
  // it's compiled standalone for verification, not bundled into the Worker.
  throw new Error(`${failures} check(s) failed.`);
}
console.log("\nAll Phase 2.3 household-combination checks passed.");
