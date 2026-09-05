/**
 * Phase 2.7 -- Texture / IDDSI Boundary.
 *
 * DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md section G: "IDDSI suitability
 * cannot be inferred only from a recipe name. Final food/drink
 * characteristics depend on preparation and serving conditions and need
 * appropriate testing/clinical direction where dysphagia is involved."
 *
 * GREEN gate: "no recipe is called IDDSI compliant from description alone."
 *
 * Same shape of guarantee as Phase 2.6's professional-target gate, applied
 * to texture/swallowing instead of nutrition: the only way a recipe reaches
 * MEETS/ADAPTABLE/EXCLUDED for a texture_swallowing code is an explicit
 * RecipeTextureVerification record created via createRecipeTextureVerification,
 * which demands a real verification method and a real source -- there is no
 * function anywhere in this module (or the rest of the dietary engine) that
 * inspects a recipe's name, ingredients, or method text and derives a
 * texture/IDDSI claim from it. Absent a verification record, the answer is
 * always UNVERIFIED, per RECIPE_SUITABILITY_STATE_CONTRACT.md's "UNVERIFIED
 * outranks optimism".
 */
import type { EnforcementLevel } from "./household";

export type TextureVerificationSource = "CLINICIAN_PLAN" | "CARE_PLAN" | "TESTED_PREPARATION";
type RequirementSourceType = "USER" | "CLINICIAN_PLAN" | "CARE_PLAN" | "SYSTEM_DEFAULT";

/** IDDSI levels and the two dysphagia-relevant attributes added in the
 * Phase 2.1 taxonomy freeze (SAUCE_GRAVY_REQUIRED, MOISTURE_REQUIRED) are
 * high-consequence: DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md is explicit
 * that an IDDSI level must be "selected by an appropriate clinician or care
 * plan." REGULAR_TEXTURE/EASY_TO_CHEW are lower-consequence comfort
 * preferences the blueprint never frames that way, so they may carry a
 * plain USER source. */
export const HIGH_CONSEQUENCE_TEXTURE_CODES = new Set([
  "SAUCE_GRAVY_REQUIRED", "MOISTURE_REQUIRED",
  ...[0, 1, 2, 3, 4, 5, 6, 7].map((n) => `IDDSI_LEVEL_${n}`),
]);

/**
 * A household member requirement for a high-consequence texture code must
 * be sourced from a clinician or care plan, not entered casually by a user
 * on their own initiative -- mirrors the professional-target boundary in
 * professionalTargets.ts, applied here instead to the source of the
 * *requirement itself* rather than a numeric target.
 */
export function validateTextureRequirementSource(requirementCode: string, sourceType: RequirementSourceType): void {
  if (HIGH_CONSEQUENCE_TEXTURE_CODES.has(requirementCode) && sourceType !== "CLINICIAN_PLAN" && sourceType !== "CARE_PLAN") {
    throw new Error(
      `${requirementCode} is a dysphagia-relevant texture requirement and must be sourced from an appropriate ` +
        `CLINICIAN_PLAN or CARE_PLAN, not "${sourceType}". Per DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md section G, ` +
        "an IDDSI level (or an equivalent swallowing-safety need) is selected by a clinician or care plan, not entered casually.",
    );
  }
}

export interface RecipeTextureVerification {
  recipe_id: string;
  requirement_code: string;
  suitability_state: "MEETS" | "ADAPTABLE" | "EXCLUDED";
  verified_by_source: TextureVerificationSource;
  method_notes: string;
  verified_at: string;
}

export interface CreateRecipeTextureVerificationInput {
  recipe_id: string;
  requirement_code: string;
  suitability_state: "MEETS" | "ADAPTABLE" | "EXCLUDED";
  verified_by_source: TextureVerificationSource;
  method_notes: string;
  verified_at: string;
}

/**
 * The only way to record that a recipe has been checked against a texture/
 * IDDSI requirement. Requires a real method_notes description (what was
 * actually tested, and how) -- an empty or placeholder note is refused,
 * because "looks soft" is exactly the kind of description-based inference
 * this gate exists to block. suitability_state cannot be UNVERIFIED here:
 * a verification record only exists when someone has concluded something
 * concrete; the "nothing on file yet" case is represented by the absence of
 * a record, not a record that says "unverified".
 */
export function createRecipeTextureVerification(
  input: CreateRecipeTextureVerificationInput,
): RecipeTextureVerification {
  if (input.suitability_state !== "MEETS" && input.suitability_state !== "ADAPTABLE" && input.suitability_state !== "EXCLUDED") {
    throw new Error(
      `Invalid suitability_state "${input.suitability_state}" for a texture verification record -- must be MEETS, ` +
        "ADAPTABLE or EXCLUDED. There is no verified-UNVERIFIED state: omit the record instead.",
    );
  }
  if (input.verified_by_source !== "CLINICIAN_PLAN" && input.verified_by_source !== "CARE_PLAN" && input.verified_by_source !== "TESTED_PREPARATION") {
    throw new Error(`Invalid verified_by_source "${input.verified_by_source}" -- must be CLINICIAN_PLAN, CARE_PLAN or TESTED_PREPARATION.`);
  }
  if (!input.method_notes || input.method_notes.trim().length < 20) {
    throw new Error(
      "A texture/IDDSI verification requires a real method_notes description of how the recipe/preparation was " +
        "actually tested or clinically assessed -- not left blank or a placeholder. A recipe's name or ingredient " +
        "list is never sufficient evidence on its own.",
    );
  }
  return { ...input };
}

export interface TextureSuitabilityResult {
  recipeId: string;
  requirementCode: string;
  state: "MEETS" | "ADAPTABLE" | "EXCLUDED" | "UNVERIFIED";
  explanation: string;
}

/**
 * Look up whether `recipeId` has an explicit, on-file verification for
 * `requirementCode`. This function does not, and structurally cannot,
 * consult the recipe's own name/ingredients/method text -- it isn't even
 * given them as a parameter. That is the enforcement of "no recipe is
 * called IDDSI compliant from description alone": there is nothing here to
 * infer from even if someone tried.
 */
export function classifyTextureSuitability(
  recipeId: string,
  requirementCode: string,
  verifications: RecipeTextureVerification[],
): TextureSuitabilityResult {
  const match = verifications.find((v) => v.recipe_id === recipeId && v.requirement_code === requirementCode);
  if (!match) {
    return {
      recipeId, requirementCode, state: "UNVERIFIED",
      explanation:
        `No recipe/preparation verification on file for ${requirementCode}. Texture and IDDSI suitability are ` +
        "never inferred from a recipe's name, ingredient list, or category -- only an explicit, tested verification changes this.",
    };
  }
  return {
    recipeId, requirementCode, state: match.suitability_state,
    explanation: `Verified ${match.suitability_state} by ${match.verified_by_source} on ${match.verified_at}: ${match.method_notes}`,
  };
}

export type { EnforcementLevel };
