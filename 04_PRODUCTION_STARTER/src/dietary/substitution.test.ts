/**
 * Phase 2.5 checks. Run with (see package.json's test:dietary pattern):
 *   npx tsc --ignoreConfig --outDir dist/dietary-test src/dietary/household.ts \
 *     src/dietary/substitutionCatalogue.ts src/dietary/substitution.ts \
 *     src/dietary/substitution.test.ts --target ES2022 --module CommonJS --strict
 *   node dist/dietary-test/substitution.test.js
 * (wired up as `npm run test:substitution`.)
 */
import { combineHouseholdRequirements, HouseholdMember } from "./household";
import {
  adaptRecipeIngredient,
  evaluateSubstitute,
  findSafeSubstitute,
  AttributeLookup,
  PriceBook,
  RecipeIngredientLine,
} from "./substitution";

let failures = 0;
function check(label: string, condition: boolean): void {
  if (condition) {
    console.log(`PASS ${label}`);
  } else {
    failures++;
    console.error(`FAIL ${label}`);
  }
}

// A minimal stand-in for ingredient_dietary_attributes_v1.json -- just the
// entries these tests actually exercise, not the full 151-ingredient table.
const ingredientAttributes: AttributeLookup = {
  milk: [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "DAIRY_MILK", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "LACTOSE_CONTENT", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "ALLERGEN_MILK", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
  ],
  chicken: [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "POULTRY", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
  ],
  "beef mince": [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "MEAT_BEEF", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
  ],
  pork: [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "MEAT_PORK", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
  ],
  sausages: [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "MEAT_PORK", attribute_value: "true", evidence_state: "CONDITIONAL" },
  ],
  tofu: [{ attribute_code: "ANIMAL_DERIVED", attribute_value: "false", evidence_state: "VERIFIED_ABSENT" }],
  lentils: [{ attribute_code: "ANIMAL_DERIVED", attribute_value: "false", evidence_state: "VERIFIED_ABSENT" }],
  beans: [{ attribute_code: "ANIMAL_DERIVED", attribute_value: "false", evidence_state: "VERIFIED_ABSENT" }],
  chickpeas: [{ attribute_code: "ANIMAL_DERIVED", attribute_value: "false", evidence_state: "VERIFIED_ABSENT" }],
  eggs: [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "EGG", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "ALLERGEN_EGG", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
  ],
  "plain flour": [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "false", evidence_state: "VERIFIED_ABSENT" },
    { attribute_code: "ALLERGEN_WHEAT", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "GLUTEN_CEREAL_WHEAT", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
  ],
  "self-raising flour": [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "false", evidence_state: "VERIFIED_ABSENT" },
    { attribute_code: "ALLERGEN_WHEAT", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "GLUTEN_CEREAL_WHEAT", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
  ],
  "wholemeal flour": [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "false", evidence_state: "VERIFIED_ABSENT" },
    { attribute_code: "ALLERGEN_WHEAT", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "GLUTEN_CEREAL_WHEAT", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
  ],
  "oat flour": [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "false", evidence_state: "VERIFIED_ABSENT" },
    { attribute_code: "ALLERGEN_OATS", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "GLUTEN_CEREAL_OATS", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
  ],
  "rolled oats": [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "false", evidence_state: "VERIFIED_ABSENT" },
    { attribute_code: "ALLERGEN_OATS", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
    { attribute_code: "GLUTEN_CEREAL_OATS", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
  ],
  "peanut butter": [
    { attribute_code: "ANIMAL_DERIVED", attribute_value: "false", evidence_state: "VERIFIED_ABSENT" },
    { attribute_code: "ALLERGEN_PEANUT", attribute_value: "true", evidence_state: "VERIFIED_PRESENT" },
  ],
};

function memberWithHardExclude(id: string, requirementCode: string): HouseholdMember {
  return {
    member_id: id, household_id: "H", display_name: id, active: true,
    requirements: [{ requirement_code: requirementCode, enforcement_level: "HARD_EXCLUDE", source_type: "USER" }],
    custom_rules: [],
  };
}

// --- Case 1: dairy-free member needs a milk substitute. ---
{
  const dairyFree = memberWithHardExclude("A", "DAIRY_FREE");
  const combined = combineHouseholdRequirements([dairyFree], ["A"]);
  const result = findSafeSubstitute("Milk", combined.hardExclusions, ingredientAttributes);
  check("dairy-free household gets a plant milk, not 'Dairy milk'", result.safe !== "Dairy milk" && result.safe !== null);
  check("dairy-free household is NOT offered 'Lactose-free milk' (still dairy)", result.safe !== "Lactose-free milk");
}

// --- Case 2: dairy-free AND soy-allergic member together must skip soy milk. ---
{
  const dairyFree: HouseholdMember = {
    member_id: "A", household_id: "H", display_name: "A", active: true,
    requirements: [
      { requirement_code: "DAIRY_FREE", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
      { requirement_code: "ALLERGY_SOY", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
    ],
    custom_rules: [],
  };
  const combined = combineHouseholdRequirements([dairyFree], ["A"]);
  const result = findSafeSubstitute("Milk", combined.hardExclusions, ingredientAttributes);
  check(
    "dairy-free + soy-allergic household skips 'Soy milk' and still finds a safe plant milk",
    result.safe !== null && result.safe !== "Soy milk" && result.safe !== "Dairy milk",
  );
  const soyMilkEval = evaluateSubstitute("Soy milk", combined.hardExclusions, ingredientAttributes);
  check("'Soy milk' itself is correctly flagged unsafe for this household", !soyMilkEval.isSafe);
}

// --- Case 3: vegetarian household needs a Dinner Protein substitute, must not get meat. ---
{
  const veg = memberWithHardExclude("A", "VEGETARIAN");
  const combined = combineHouseholdRequirements([veg], ["A"]);
  const result = findSafeSubstitute("Dinner Protein", combined.hardExclusions, ingredientAttributes, "Chicken");
  check(
    "vegetarian household gets a plant protein (tofu/lentils/beans/chickpeas/eggs), not another meat",
    result.safe !== null && !["Chicken", "Beef mince", "Pork", "Sausages"].includes(result.safe),
  );
}

// --- Case 4: peanut allergy only -- must NOT over-exclude nut/seed butters the household has no allergy to. ---
{
  const peanutAllergy = memberWithHardExclude("A", "ALLERGY_PEANUT");
  const combined = combineHouseholdRequirements([peanutAllergy], ["A"]);
  const result = findSafeSubstitute("Nut/Seed Butter", combined.hardExclusions, ingredientAttributes, "Peanut butter");
  check(
    "peanut-only allergy accepts the first non-peanut option (Sunflower seed butter) rather than rejecting every nut/seed butter",
    result.safe === "Sunflower seed butter",
  );
}

// --- Case 5: coeliac-strict household needs a Flour substitute -- must get the GF-labelled option, not oats (unverified per AU boundary). ---
{
  const coeliac = memberWithHardExclude("A", "COELIAC_STRICT_GF");
  const combined = combineHouseholdRequirements([coeliac], ["A"]);
  const result = findSafeSubstitute("Flour", combined.hardExclusions, ingredientAttributes);
  check("coeliac-strict household gets 'GF flour blend' for a flour substitution", result.safe === "GF flour blend");
}

// --- Case 6: coeliac-strict household needs an Oats/Breakfast Grain substitute -- must get Certified GF oats, not plain rolled oats. ---
{
  const coeliac = memberWithHardExclude("A", "COELIAC_STRICT_GF");
  const combined = combineHouseholdRequirements([coeliac], ["A"]);
  const result = findSafeSubstitute("Oats/Breakfast Grain", combined.hardExclusions, ingredientAttributes);
  check("coeliac-strict household gets 'Certified GF oats', not plain rolled/quick oats", result.safe === "Certified GF oats");
  const rolledOatsEval = evaluateSubstitute("Rolled oats", combined.hardExclusions, ingredientAttributes);
  check("plain 'Rolled oats' is correctly NOT treated as safe for a coeliac-strict household", !rolledOatsEval.isSafe);
}

// --- Case 7: no safe substitute exists in the group -> explicit unresolved result, not a silent wrong pick. ---
{
  const allergicToEverything: HouseholdMember = {
    member_id: "A", household_id: "H", display_name: "A", active: true,
    requirements: [
      { requirement_code: "DAIRY_FREE", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
      { requirement_code: "ALLERGY_SOY", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
      { requirement_code: "ALLERGY_ALMOND", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
      { requirement_code: "ALLERGY_OATS", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
      // No entry excludes coconut -- "Coconut drink" should be the one safe option left.
    ],
    custom_rules: [],
  };
  const combined = combineHouseholdRequirements([allergicToEverything], ["A"]);
  const result = findSafeSubstitute("Milk", combined.hardExclusions, ingredientAttributes);
  check("with dairy/soy/almond/oats all excluded, 'Coconut drink' is still found as the safe leftover option", result.safe === "Coconut drink");
}

// --- Case 8: full adaptRecipeIngredient() -- ingredient list AND cost both change. ---
{
  const dairyFree = memberWithHardExclude("A", "DAIRY_FREE");
  const combined = combineHouseholdRequirements([dairyFree], ["A"]);
  const line: RecipeIngredientLine = { ingredient: "milk", baseQty: 2, unit: "cup", optional: false };
  const prices = new Map<string, number>([["milk|cup", 1.2], ["Oat milk|cup", 2.5], ["Soy milk|cup", 2.0], ["Almond milk|cup", 2.8], ["Coconut drink|cup", 2.2]]);
  const priceBook: PriceBook = { get: (ingredient, unit) => prices.get(`${ingredient}|${unit}`) };
  const adaptation = adaptRecipeIngredient(line, "Milk", "DAIRY_FREE", 2, combined.hardExclusions, ingredientAttributes, priceBook);

  check("adaptation was found (not null)", adaptation !== null);
  check("ingredientChange actually changes the ingredient", adaptation!.ingredientChange.from !== adaptation!.ingredientChange.to);
  check("costChange uses the substitute's price, not milk's price", adaptation!.costChange.to.unitPrice !== 1.2);
  check(
    "costChange.to.cost reflects the substitute's price x required qty (baseQty 2 x scale 2 = 4 units)",
    adaptation!.costChange.to.cost === adaptation!.costChange.to.unitPrice! * 4,
  );
  check("newSuitabilityState is ADAPTABLE once a safe substitute with cost is found", adaptation!.newSuitabilityState === "ADAPTABLE");
}

// --- Case 9: unresolved case still returns a full Adaptation (never null) when the ingredient has a swap group. ---
{
  const allergicToEverything: HouseholdMember = {
    member_id: "A", household_id: "H", display_name: "A", active: true,
    requirements: [
      { requirement_code: "DAIRY_FREE", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
      { requirement_code: "ALLERGY_SOY", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
      { requirement_code: "ALLERGY_ALMOND", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
      { requirement_code: "ALLERGY_OATS", enforcement_level: "HARD_EXCLUDE", source_type: "USER" },
    ],
    custom_rules: [{ custom_rule_id: "c1", rule_type: "CUSTOM_EXCLUSION", rule_label: "no coconut", enforcement_level: "HARD_EXCLUDE", active: true }],
  };
  const combined = combineHouseholdRequirements([allergicToEverything], ["A"]);
  const line: RecipeIngredientLine = { ingredient: "milk", baseQty: 1, unit: "cup", optional: false };
  const priceBook: PriceBook = { get: () => 2.0 };
  const adaptation = adaptRecipeIngredient(line, "Milk", "DAIRY_FREE", 1, combined.hardExclusions, ingredientAttributes, priceBook);
  check("a custom exclusion (no attribute mapping) does not crash the search", adaptation !== null);
  check(
    "custom 'no coconut' exclusion isn't attribute-checkable so Coconut drink still comes back safe (documented limitation, not silently ignored)",
    adaptation!.newSuitabilityState === "ADAPTABLE" && adaptation!.ingredientChange.to === "Coconut drink",
  );
}

// --- Case 10: no function/swap group -- returns null (nothing to substitute with), not a fabricated answer. ---
{
  const line: RecipeIngredientLine = { ingredient: "cinnamon", baseQty: 1, unit: "tsp", optional: false };
  const priceBook: PriceBook = { get: () => 0.5 };
  const adaptation = adaptRecipeIngredient(line, undefined, "ALLERGY_PEANUT", 1, [], ingredientAttributes, priceBook);
  check("an ingredient with no swap group returns null rather than fabricating a substitute", adaptation === null);
}

if (failures > 0) {
  throw new Error(`${failures} check(s) failed.`);
}
console.log("\nAll Phase 2.5 substitution checks passed.");
