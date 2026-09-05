/**
 * Phase 2.5 -- Substitution Safety & Cost Recalculation.
 *
 * DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md's substitution rule: a substitution
 * is only eligible if (a) it is mapped to the ingredient function needed by
 * the recipe, (b) it does not conflict with any hard exclusion, (c) its
 * dietary attributes are known enough for the requested requirement, (d) the
 * user is shown the change, and (e) the budget engine recalculates using the
 * substitute's price/pack data. This module implements (a)-(c) and (e);
 * (d) is a UI concern that consumes this module's output.
 *
 * GREEN gate: "every displayed adaptation changes both the ingredient list
 * and the affordability calculation" -- enforced by construction in
 * `Adaptation`, which always carries both an ingredient-list change
 * (originalIngredient -> substituteIngredient) and a cost change
 * (originalLine -> adaptedLine).
 *
 * Deliberately reuses the Phase 2.3 household combination output
 * (CombinedRequirementEntry[]) as its input for "which hard exclusions must
 * this substitute not violate" -- that's the whole point of building 2.3
 * before 2.5: a substitute is checked against every selected household
 * member's combined hard exclusions at once, not one member at a time.
 */
import { CombinedRequirementEntry, EnforcementLevel } from "./household";
import { INGREDIENT_KEY_ALIASES, SUBSTITUTE_ONLY_ATTRIBUTES, SWAP_GROUPS } from "./substitutionCatalogue";

export type EvidenceState = "VERIFIED_PRESENT" | "VERIFIED_ABSENT" | "CONDITIONAL" | "UNVERIFIED";

export interface AttributeRow {
  attribute_code: string;
  attribute_value: string;
  evidence_state: EvidenceState;
  notes?: string;
}

/** Same shape as ingredient_dietary_attributes_v1.json's `ingredients` array,
 * reduced to key -> attribute rows (this module doesn't need the recipe
 * group/swap group metadata Phase 2.2 also stores). */
export type AttributeLookup = Record<string, AttributeRow[]>;

// --------------------------------------------------------------------------
// Requirement violation checks -- mirrors
// 07_DIETARY_REQUIREMENTS_ENGINE/build_recipe_requirement_assessments.py's
// direct-code mapping and vegetarian/vegan flesh-fallback logic. Kept as its
// own (smaller) copy here rather than a shared import because this module
// checks a single substitute ingredient against a household's hard
// exclusions, not a whole recipe against the full taxonomy -- HALAL/KOSHER
// here are intentionally reduced to their single-ingredient-checkable rules
// (pork/shellfish presence), not the meat+dairy *combination* rule, which
// only makes sense at the whole-recipe level Phase 2.4 already covers.
// --------------------------------------------------------------------------

const DIRECT_VIOLATION_CODES: Record<string, string[]> = {
  ALLERGY_WHEAT: ["ALLERGEN_WHEAT"], ALLERGY_FISH: ["ALLERGEN_FISH"],
  ALLERGY_CRUSTACEAN: ["ALLERGEN_CRUSTACEAN"], ALLERGY_MOLLUSC: ["ALLERGEN_MOLLUSC"],
  ALLERGY_EGG: ["ALLERGEN_EGG"], ALLERGY_MILK: ["ALLERGEN_MILK"], ALLERGY_LUPIN: ["ALLERGEN_LUPIN"],
  ALLERGY_PEANUT: ["ALLERGEN_PEANUT"], ALLERGY_SOY: ["ALLERGEN_SOY"], ALLERGY_SESAME: ["ALLERGEN_SESAME"],
  ALLERGY_ALMOND: ["ALLERGEN_ALMOND"], ALLERGY_BRAZIL_NUT: ["ALLERGEN_BRAZIL_NUT"],
  ALLERGY_CASHEW: ["ALLERGEN_CASHEW"], ALLERGY_HAZELNUT: ["ALLERGEN_HAZELNUT"],
  ALLERGY_MACADAMIA: ["ALLERGEN_MACADAMIA"], ALLERGY_PECAN: ["ALLERGEN_PECAN"],
  ALLERGY_PISTACHIO: ["ALLERGEN_PISTACHIO"], ALLERGY_PINE_NUT: ["ALLERGEN_PINE_NUT"],
  ALLERGY_WALNUT: ["ALLERGEN_WALNUT"], ALLERGY_BARLEY: ["ALLERGEN_BARLEY"], ALLERGY_OATS: ["ALLERGEN_OATS"],
  ALLERGY_RYE: ["ALLERGEN_RYE"], SULPHITES_CONTROL: ["ALLERGEN_SULPHITES"],
  WHEAT_FREE: ["GLUTEN_CEREAL_WHEAT"], RYE_FREE: ["GLUTEN_CEREAL_RYE"], BARLEY_FREE: ["GLUTEN_CEREAL_BARLEY"],
  OAT_EXCLUDE: ["GLUTEN_CEREAL_OATS"],
  DAIRY_FREE: ["DAIRY_MILK"], LACTOSE_FREE: ["LACTOSE_CONTENT"], ALCOHOL_FREE: ["ALCOHOL_CONTENT"],
  CAFFEINE_FREE: ["CAFFEINE_CONTENT"], ONION_FREE: ["ONION_CONTENT"], GARLIC_FREE: ["GARLIC_CONTENT"],
  PORK_FREE: ["MEAT_PORK"], BEEF_FREE: ["MEAT_BEEF"],
  HALAL_COMPATIBLE: ["MEAT_PORK"],
  KOSHER_COMPATIBLE: ["MEAT_PORK", "SHELLFISH_CRUSTACEAN", "SHELLFISH_MOLLUSC"],
};

/** COELIAC_STRICT_GF / GLUTEN_FREE_PREFERENCE: wheat/barley/rye definitely
 * violate; oats violate UNLESS the substitute is specifically OAT_GF_CERTIFIED
 * (see substitutionCatalogue.ts's "Certified GF oats" entry) -- the AU claim
 * boundary this whole engine is built around. */
function coeliacStyleViolation(attrs: AttributeRow[]): "definite" | "maybe" | "none" {
  const byCode = new Map(attrs.map((r) => [r.attribute_code, r]));
  for (const code of ["GLUTEN_CEREAL_WHEAT", "GLUTEN_CEREAL_BARLEY", "GLUTEN_CEREAL_RYE"]) {
    const row = byCode.get(code);
    if (row && row.attribute_value !== "false") {
      return row.evidence_state === "VERIFIED_PRESENT" ? "definite" : "maybe";
    }
  }
  const oats = byCode.get("GLUTEN_CEREAL_OATS");
  if (oats && oats.attribute_value !== "false") {
    const certified = byCode.get("OAT_GF_CERTIFIED");
    if (certified && certified.attribute_value === "true") return "none";
    return "maybe"; // per REFERENCE_SOURCES.md: uncertified oats stay UNVERIFIED, not EXCLUDED
  }
  return "none";
}

const FLESH_CODES = ["MEAT_BEEF", "MEAT_PORK", "POULTRY", "FISH", "SHELLFISH_CRUSTACEAN", "SHELLFISH_MOLLUSC"];
const NON_FLESH_ANIMAL_CODES = ["DAIRY_MILK", "EGG", "HONEY_BEE_DERIVED"];

function lifestyleViolation(attrs: AttributeRow[], allowFish: boolean): "definite" | "maybe" | "none" {
  const byCode = new Map(attrs.map((r) => [r.attribute_code, r]));
  const fleshCodes = allowFish ? FLESH_CODES.filter((c) => !c.startsWith("FISH") && !c.startsWith("SHELLFISH")) : FLESH_CODES;
  const nonFleshCodes = allowFish ? [...NON_FLESH_ANIMAL_CODES, "FISH", "SHELLFISH_CRUSTACEAN", "SHELLFISH_MOLLUSC"] : NON_FLESH_ANIMAL_CODES;
  for (const code of fleshCodes) {
    const row = byCode.get(code);
    if (row && row.attribute_value !== "false" && row.evidence_state === "VERIFIED_PRESENT") return "definite";
  }
  for (const code of fleshCodes) {
    const row = byCode.get(code);
    if (row && row.attribute_value !== "false" && (row.evidence_state === "CONDITIONAL" || row.evidence_state === "UNVERIFIED")) return "maybe";
  }
  const animal = byCode.get("ANIMAL_DERIVED");
  if (animal && animal.attribute_value !== "false") {
    const hasNonFlesh = nonFleshCodes.some((c) => {
      const r = byCode.get(c);
      return r && r.attribute_value !== "false";
    });
    if (!hasNonFlesh) {
      if (animal.evidence_state === "VERIFIED_PRESENT") return "definite";
      if (animal.evidence_state === "CONDITIONAL" || animal.evidence_state === "UNVERIFIED") return "maybe";
    }
  }
  return "none";
}

function veganViolation(attrs: AttributeRow[]): "definite" | "maybe" | "none" {
  const row = attrs.find((r) => r.attribute_code === "ANIMAL_DERIVED");
  if (!row || row.attribute_value === "false") return "none";
  return row.evidence_state === "VERIFIED_PRESENT" ? "definite" : "maybe";
}

/** Does this single ingredient's attribute set violate `requirementCode`?
 * "definite" = confirmed violation, "maybe" = uncertain (CONDITIONAL/UNVERIFIED
 * evidence), "none" = no violation found. A HARD_EXCLUDE requirement treats
 * both "definite" and "maybe" as disqualifying for substitution-safety
 * purposes -- see `isSafeAgainst` below. */
export function checkAttributesAgainstRequirement(attrs: AttributeRow[], requirementCode: string): "definite" | "maybe" | "none" {
  if (requirementCode === "VEGETARIAN") return lifestyleViolation(attrs, false);
  if (requirementCode === "PESCATARIAN") return lifestyleViolation(attrs, true);
  if (requirementCode === "VEGAN") return veganViolation(attrs);
  if (requirementCode === "COELIAC_STRICT_GF" || requirementCode === "GLUTEN_FREE_PREFERENCE") return coeliacStyleViolation(attrs);

  const codes = DIRECT_VIOLATION_CODES[requirementCode];
  if (!codes) return "none"; // requirement not ingredient-attribute-checkable here (see PHASE_2_5 report's scope note)
  const byCode = new Map(attrs.map((r) => [r.attribute_code, r]));
  let maybe = false;
  for (const code of codes) {
    const row = byCode.get(code);
    if (row && row.attribute_value !== "false") {
      if (row.evidence_state === "VERIFIED_PRESENT") return "definite";
      maybe = true;
    }
  }
  return maybe ? "maybe" : "none";
}

// --------------------------------------------------------------------------
// Resolving a substitute display name to its attribute rows
// --------------------------------------------------------------------------

export function resolveSubstituteAttributes(
  substituteName: string,
  ingredientAttributes: AttributeLookup,
): AttributeRow[] {
  const alias = INGREDIENT_KEY_ALIASES[substituteName];
  if (alias) return ingredientAttributes[alias] ?? [];
  return SUBSTITUTE_ONLY_ATTRIBUTES[substituteName] ?? [];
}

// --------------------------------------------------------------------------
// Finding a safe substitute for a household
// --------------------------------------------------------------------------

export interface SubstituteEvaluation {
  substituteName: string;
  violatesHardExclusions: Array<{ requirementCode: string; confidence: "definite" | "maybe" }>;
  isSafe: boolean; // true only if zero violations, at any confidence
}

/** Evaluate one candidate substitute against every HARD_EXCLUDE entry a
 * household has combined for this meal (Phase 2.3's output). A "maybe"
 * (CONDITIONAL/UNVERIFIED) violation still disqualifies the candidate from
 * being called safe -- per the suitability-state contract, UNVERIFIED
 * evidence must never be silently treated as clearance for a hard safety
 * requirement. */
export function evaluateSubstitute(
  substituteName: string,
  hardExclusions: CombinedRequirementEntry[],
  ingredientAttributes: AttributeLookup,
): SubstituteEvaluation {
  const attrs = resolveSubstituteAttributes(substituteName, ingredientAttributes);
  const violations: SubstituteEvaluation["violatesHardExclusions"] = [];
  for (const entry of hardExclusions) {
    if (entry.effectiveEnforcement !== "HARD_EXCLUDE") continue;
    const requirementCode = entry.key.startsWith("CUSTOM:") ? null : entry.key;
    if (!requirementCode) continue; // custom rules need canonical_ingredient_id matching, not this attribute check
    const result = checkAttributesAgainstRequirement(attrs, requirementCode);
    if (result !== "none") {
      violations.push({ requirementCode, confidence: result });
    }
  }
  return { substituteName, violatesHardExclusions: violations, isSafe: violations.length === 0 };
}

export interface FindSubstituteResult {
  functionCode: string;
  safe: string | null; // the first fully-clear candidate, or null if none
  uncertain: SubstituteEvaluation[]; // candidates blocked only by "maybe" evidence
  unsafe: SubstituteEvaluation[]; // candidates with a definite violation
}

/** Search a swap group ("function") for a substitute that violates none of
 * the household's combined hard exclusions. Order in SWAP_GROUPS is the
 * preference order (first listed = first tried), matching how the V1
 * prototype already presents swap options. */
export function findSafeSubstitute(
  functionCode: string,
  hardExclusions: CombinedRequirementEntry[],
  ingredientAttributes: AttributeLookup,
  excludeName?: string,
): FindSubstituteResult {
  const options = (SWAP_GROUPS[functionCode] ?? []).filter((name) => name !== excludeName);
  const uncertain: SubstituteEvaluation[] = [];
  const unsafe: SubstituteEvaluation[] = [];
  for (const name of options) {
    const evaluation = evaluateSubstitute(name, hardExclusions, ingredientAttributes);
    if (evaluation.isSafe) {
      return { functionCode, safe: name, uncertain, unsafe };
    }
    if (evaluation.violatesHardExclusions.some((v) => v.confidence === "definite")) {
      unsafe.push(evaluation);
    } else {
      uncertain.push(evaluation);
    }
  }
  return { functionCode, safe: null, uncertain, unsafe };
}

// --------------------------------------------------------------------------
// Cost recalculation -- "the budget engine recalculates using the
// substitute's price/pack data", not the original ingredient's.
// --------------------------------------------------------------------------

export interface RecipeIngredientLine {
  ingredient: string;
  baseQty: number;
  unit: string;
  optional: boolean;
}

export interface PriceBook {
  /** price per recipe unit, keyed "<ingredient>|<unit>" (matches the V1
   * prototype's own price-book key shape in 03_WORKING_PROTOTYPE/engine.js). */
  get(ingredient: string, unit: string): number | undefined;
}

export interface AdaptedCostLine {
  substituteIngredient: string;
  unit: string;
  requiredQty: number;
  /** The V1 prototype's pantry-first rule still applies -- a household is
   * assumed to hold none of a brand-new substitute in pantry yet, so the
   * full required quantity is priced as a shortage. A household that
   * separately records pantry stock of the substitute would reduce this in
   * the live engine the same way it does for any other ingredient. */
  shortageQty: number;
  unitPrice: number | null;
  cost: number | null;
  priceStatus: "PRICED" | "NEED_PRICE";
}

export function recalculateAdaptedCost(
  line: RecipeIngredientLine,
  scaleFactor: number,
  substituteName: string,
  priceBook: PriceBook,
): AdaptedCostLine {
  const requiredQty = line.baseQty * scaleFactor;
  const unitPrice = priceBook.get(substituteName, line.unit) ?? null;
  return {
    substituteIngredient: substituteName,
    unit: line.unit,
    requiredQty,
    shortageQty: requiredQty,
    unitPrice,
    cost: unitPrice === null ? null : requiredQty * unitPrice,
    priceStatus: unitPrice === null ? "NEED_PRICE" : "PRICED",
  };
}

// --------------------------------------------------------------------------
// Putting it together: one displayed adaptation
// --------------------------------------------------------------------------

export interface Adaptation {
  requirementCode: string;
  functionCode: string;
  ingredientChange: { from: string; to: string };
  costChange: { from: RecipeIngredientLine; to: AdaptedCostLine };
  newSuitabilityState: "ADAPTABLE" | "EXCLUDED" | "UNVERIFIED";
  explanation: string;
}

/**
 * Attempt to adapt one recipe ingredient line so it stops violating
 * `requirementCode` for this household, without violating anyone else's
 * hard exclusion. Returns null only when the ingredient has no swap group at
 * all (nothing to substitute with) -- an unresolved shortfall still returns
 * an Adaptation with newSuitabilityState EXCLUDED/UNVERIFIED so the caller
 * always has an explicit answer, never silence.
 */
export function adaptRecipeIngredient(
  line: RecipeIngredientLine,
  functionCode: string | undefined,
  requirementCode: string,
  scaleFactor: number,
  hardExclusions: CombinedRequirementEntry[],
  ingredientAttributes: AttributeLookup,
  priceBook: PriceBook,
): Adaptation | null {
  if (!functionCode || !(functionCode in SWAP_GROUPS)) return null;

  const result = findSafeSubstitute(functionCode, hardExclusions, ingredientAttributes, line.ingredient);

  if (!result.safe) {
    const state = result.unsafe.length > 0 || result.uncertain.length > 0 ? "UNVERIFIED" : "EXCLUDED";
    return {
      requirementCode,
      functionCode,
      ingredientChange: { from: line.ingredient, to: line.ingredient },
      costChange: { from: line, to: recalculateAdaptedCost(line, scaleFactor, line.ingredient, priceBook) },
      newSuitabilityState: state,
      explanation:
        `No substitute in the "${functionCode}" swap group is confirmed safe for every selected household ` +
        `member's hard exclusion (${result.unsafe.length} definitely unsafe, ${result.uncertain.length} unverified). ` +
        "Recipe stays as originally classified for this requirement.",
    };
  }

  const adaptedCost = recalculateAdaptedCost(line, scaleFactor, result.safe, priceBook);
  return {
    requirementCode,
    functionCode,
    ingredientChange: { from: line.ingredient, to: result.safe },
    costChange: { from: line, to: adaptedCost },
    newSuitabilityState: "ADAPTABLE",
    explanation:
      `Replace "${line.ingredient}" with "${result.safe}" to satisfy ${requirementCode} without violating any other ` +
      "selected household member's hard exclusion. Shopping cost is recalculated using the substitute's price, not the original ingredient's.",
  };
}

export type { EnforcementLevel };
