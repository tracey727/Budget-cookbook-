/**
 * Phase 2.7 GREEN-gate check: "no recipe is called IDDSI compliant from
 * description alone." Run via `npm run test:texture`.
 */
import {
  classifyTextureSuitability,
  createRecipeTextureVerification,
  RecipeTextureVerification,
  validateTextureRequirementSource,
} from "./textureVerification";

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

// --- No verification on file: always UNVERIFIED, whatever the recipe looks like. ---
check(
  "a recipe with no verification record is UNVERIFIED for IDDSI_LEVEL_4",
  classifyTextureSuitability("GEN-RCP-0001", "IDDSI_LEVEL_4", []).state === "UNVERIFIED",
);
check(
  "even a recipe literally named to sound compliant gets no special treatment -- classifyTextureSuitability isn't given the name at all",
  classifyTextureSuitability("GEN-RCP-PUREED-SMOOTH-SOUP", "IDDSI_LEVEL_4", []).state === "UNVERIFIED",
);

// --- createRecipeTextureVerification refuses vague/placeholder evidence. ---
check(
  "an empty method_notes is refused",
  throws(() =>
    createRecipeTextureVerification({
      recipe_id: "GEN-RCP-0001", requirement_code: "IDDSI_LEVEL_4", suitability_state: "MEETS",
      verified_by_source: "TESTED_PREPARATION", method_notes: "", verified_at: "2026-09-05",
    }),
  ),
);
check(
  "a too-short placeholder-looking method_notes is refused",
  throws(() =>
    createRecipeTextureVerification({
      recipe_id: "GEN-RCP-0001", requirement_code: "IDDSI_LEVEL_4", suitability_state: "MEETS",
      verified_by_source: "TESTED_PREPARATION", method_notes: "looks soft", verified_at: "2026-09-05",
    }),
  ),
);
check(
  "suitability_state cannot be set to UNVERIFIED via this constructor -- absence of a record already means that",
  throws(() =>
    createRecipeTextureVerification({
      recipe_id: "GEN-RCP-0001", requirement_code: "IDDSI_LEVEL_4",
      suitability_state: "UNVERIFIED" as unknown as "MEETS",
      verified_by_source: "TESTED_PREPARATION", method_notes: "Blended and passed through a fine sieve; tested with an IDDSI flow test.",
      verified_at: "2026-09-05",
    }),
  ),
);
check(
  "an invalid verified_by_source is refused",
  throws(() =>
    createRecipeTextureVerification({
      recipe_id: "GEN-RCP-0001", requirement_code: "IDDSI_LEVEL_4", suitability_state: "MEETS",
      verified_by_source: "AI_ASSESSMENT" as unknown as "TESTED_PREPARATION",
      method_notes: "Blended and passed through a fine sieve; tested with an IDDSI flow test.",
      verified_at: "2026-09-05",
    }),
  ),
);

// --- A real verification record is honoured, scoped to its exact recipe+code. ---
const verification: RecipeTextureVerification = createRecipeTextureVerification({
  recipe_id: "GEN-RCP-0001", requirement_code: "IDDSI_LEVEL_4", suitability_state: "MEETS",
  verified_by_source: "TESTED_PREPARATION",
  method_notes: "Blended smooth, passed IDDSI flow test at 25C; no lumps on fork-pressure test.",
  verified_at: "2026-09-05",
});
check(
  "a real verification record produces the recorded state for its exact recipe+code",
  classifyTextureSuitability("GEN-RCP-0001", "IDDSI_LEVEL_4", [verification]).state === "MEETS",
);
check(
  "the same verification does NOT apply to a different requirement code on the same recipe",
  classifyTextureSuitability("GEN-RCP-0001", "IDDSI_LEVEL_6", [verification]).state === "UNVERIFIED",
);
check(
  "the same verification does NOT apply to a different recipe",
  classifyTextureSuitability("GEN-RCP-0002", "IDDSI_LEVEL_4", [verification]).state === "UNVERIFIED",
);

// --- Requirement source boundary: high-consequence texture codes need a clinical/care-plan source. ---
check(
  "IDDSI_LEVEL_4 set with a plain USER source is rejected",
  throws(() => validateTextureRequirementSource("IDDSI_LEVEL_4", "USER")),
);
check(
  "IDDSI_LEVEL_4 set with a CARE_PLAN source is accepted",
  !throws(() => validateTextureRequirementSource("IDDSI_LEVEL_4", "CARE_PLAN")),
);
check(
  "SAUCE_GRAVY_REQUIRED (added in the Phase 2.1 freeze) also requires a clinical/care-plan source",
  throws(() => validateTextureRequirementSource("SAUCE_GRAVY_REQUIRED", "USER")),
);
check(
  "EASY_TO_CHEW is a lower-consequence preference and may be set by a plain USER",
  !throws(() => validateTextureRequirementSource("EASY_TO_CHEW", "USER")),
);

if (failures > 0) {
  throw new Error(`${failures} check(s) failed.`);
}
console.log("\nAll Phase 2.7 texture/IDDSI checks passed.");
