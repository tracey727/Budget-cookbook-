/**
 * Phase 7 GREEN-gate check for GET /api/catalogue: the bulk payload that
 * replaces the bundled public/data.prototype.js must reproduce the exact
 * data contract public/engine.prototype.js already depends on (see
 * catalogue.ts's module comment) -- byte-identical field names and
 * "Yes"/"No" encodings, scoped to only the Phase 2.8 launch-approved
 * recipes. Same standalone-assertion convention as src/dietary/*.test.ts.
 *
 * The second half of this file is an end-to-end fixture regression test: it
 * converts the real 04_PRODUCTION_STARTER/data/recipe_catalog_v1.json +
 * 02_RECIPE_CONTENT/recipe_launch_readiness_v1.json into the exact row
 * shapes scripts/build_seed_sql.py would load into Postgres, runs them
 * through this module, and diffs the result against the original
 * prototype data -- standing in for a live-database regression test, which
 * this sandbox's network policy cannot reach (see
 * PHASE_6_CLOUDFLARE_WORKER_HYPERDRIVE_REPORT.md). It does not replace a
 * real browser smoke test against a deployed Worker, which still needs to
 * happen once Cloudflare/Neon provisioning unblocks per that report.
 */
import * as fs from "fs";
import * as path from "path";
import {
  assembleCatalogue,
  assembleSwapMap,
  mapEngineRecipeRow,
  mapIngredientUnitPairRow,
} from "./catalogue";

type DbRow = Record<string, unknown>;

let failures = 0;
function check(label: string, condition: boolean): void {
  if (condition) {
    console.log(`PASS ${label}`);
  } else {
    failures++;
    console.error(`FAIL ${label}`);
  }
}

// --- small, hand-built fixtures ---

const recipeRowA = {
  recipe_id: "GEN-RCP-0001",
  meal_type: "Breakfast",
  recipe_name: "Banana Cinnamon Overnight Oats",
  base_family: "Overnight oats",
  base_serves: 4,
  prep_min: 8,
  cook_min: 0,
  budget_tier: "$",
  primary_protein: null,
  carb_base: "oats",
  produce_focus: "banana",
  freezer_friendly: false,
  lunchbox_friendly: true,
  vegetarian_base: true,
  gf_adaptable: true,
  df_adaptable: true,
  one_pan_pot: false,
  method_text: "1. Combine. | 2. Chill.",
  mix_change_notes: "Swap any fruit.",
};
const ingredientRowsA = [
  { recipe_id: "GEN-RCP-0001", line_no: 1, ingredient: "rolled oats", base_qty: 2, unit_code: "cup", optional: false, swap_group_code: "Oats/Breakfast Grain" },
  { recipe_id: "GEN-RCP-0001", line_no: 2, ingredient: "chia seeds", base_qty: 2, unit_code: "tbsp", optional: true, swap_group_code: null },
];

const mappedRecipe = mapEngineRecipeRow(recipeRowA, ingredientRowsA);
check(
  "boolean recipe flags map to the legacy 'Yes'/'No' strings engine.prototype.js's pass() compares against",
  mappedRecipe.lunchbox === "Yes" && mappedRecipe.freezer === "No" && mappedRecipe.vegetarian === "Yes",
);
check("a null primary_protein maps back to '' (the original bundle's empty-string convention)", mappedRecipe.protein === "");
check("a present produce_focus is preserved", mappedRecipe.focus === "banana");
check("ingredient optional flag stays a real boolean (engine's `i.optional?0:...` needs this)", mappedRecipe.ingredients[1].optional === true);

check(
  "assembleCatalogue groups ingredient rows under the correct recipe by recipe_id",
  assembleCatalogue([recipeRowA], ingredientRowsA, [], []).recipes[0].ingredients.length === 2,
);
check(
  "a recipe with no matching ingredient rows gets an empty array, not undefined",
  assembleCatalogue([recipeRowA], [], [], []).recipes[0].ingredients.length === 0,
);

const swapOptionRows: DbRow[] = [
  { swap_group_code: "Milk", ingredient_name: "Dairy milk" },
  { swap_group_code: "Milk", ingredient_name: "Oat milk" },
  { swap_group_code: "Seeds", ingredient_name: "Chia seeds" },
];
const swapMap = assembleSwapMap(swapOptionRows);
check("assembleSwapMap groups options under their swap_group_code key", Object.keys(swapMap).sort().join(",") === "Milk,Seeds");
check("assembleSwapMap preserves option_order (query orders by option_order)", swapMap.Milk[0] === "Dairy milk" && swapMap.Milk[1] === "Oat milk");

const pair = mapIngredientUnitPairRow({ ingredient: "apple", unit: "cup" });
check("mapIngredientUnitPairRow builds the '<ingredient>|<unit>' key the prototype pantry UI keys on", pair.key === "apple|cup");

// --- end-to-end fixture regression test against the real data files ---

const PRODUCTION_STARTER = process.cwd();
const REPO_ROOT = path.resolve(PRODUCTION_STARTER, "..");

interface OriginalIngredient {
  number: number;
  ingredient: string;
  baseQty: number;
  unit: string;
  group: string;
  optional: boolean;
  swapGroup?: string;
}
interface OriginalRecipe {
  id: string;
  mealType: string;
  name: string;
  family: string;
  baseServes: number;
  prepMin: number;
  cookMin: number;
  budgetTier: string;
  protein: string;
  carb: string;
  focus: string;
  freezer: string;
  lunchbox: string;
  vegetarian: string;
  gfAdaptable: string;
  dfAdaptable: string;
  onePot: string;
  method: string;
  swapNotes: string;
  ingredients: OriginalIngredient[];
}

const catalog: {
  recipes: OriginalRecipe[];
  swapMap: Record<string, string[]>;
  ingredientUnitPairs: Array<{ ingredient: string; unit: string; key: string }>;
} = JSON.parse(
  fs.readFileSync(path.join(PRODUCTION_STARTER, "data", "recipe_catalog_v1.json"), "utf8"),
);
const readiness: { launch_ready_count: number; recipes: Array<{ recipe_id: string; status: string }> } = JSON.parse(
  fs.readFileSync(path.join(REPO_ROOT, "02_RECIPE_CONTENT", "recipe_launch_readiness_v1.json"), "utf8"),
);
const launchReadyIds = new Set(
  readiness.recipes.filter((r) => r.status === "LAUNCH_READY").map((r) => r.recipe_id),
);
check(`fixture sanity: 385 recipes are LAUNCH_READY (found ${launchReadyIds.size})`, launchReadyIds.size === 385);

function blankToNull(value: string): string | null {
  const trimmed = (value || "").trim();
  return trimmed || null;
}

/** Mirrors scripts/build_seed_sql.py's build_recipes() column mapping exactly. */
function toDbRecipeRow(r: OriginalRecipe): DbRow {
  return {
    recipe_id: r.id,
    meal_type: r.mealType,
    recipe_name: r.name,
    base_family: r.family,
    base_serves: r.baseServes,
    prep_min: r.prepMin,
    cook_min: r.cookMin,
    budget_tier: r.budgetTier,
    primary_protein: blankToNull(r.protein),
    carb_base: blankToNull(r.carb),
    produce_focus: blankToNull(r.focus),
    freezer_friendly: r.freezer === "Yes",
    lunchbox_friendly: r.lunchbox === "Yes",
    vegetarian_base: r.vegetarian === "Yes",
    gf_adaptable: r.gfAdaptable === "Yes",
    df_adaptable: r.dfAdaptable === "Yes",
    one_pan_pot: r.onePot === "Yes",
    method_text: r.method,
    mix_change_notes: r.swapNotes,
  };
}

/** Mirrors build_recipe_ingredients(): canonical_name is lower-cased, so a
 * mixed-case source ingredient name (the seed script's own example is "BBQ
 * sauce") comes back lower-cased -- a real, pre-existing Phase 5 schema
 * decision this test accounts for rather than papers over. */
function toDbIngredientRows(r: OriginalRecipe): DbRow[] {
  return r.ingredients.map((i) => ({
    recipe_id: r.id,
    line_no: i.number,
    ingredient: i.ingredient.toLowerCase(),
    base_qty: i.baseQty,
    unit_code: i.unit,
    optional: i.optional,
    swap_group_code: i.swapGroup ?? null,
  }));
}

const launchReadyRecipes = catalog.recipes.filter((r) => launchReadyIds.has(r.id));
const dbRecipeRows = launchReadyRecipes.map(toDbRecipeRow);
const dbIngredientRows = launchReadyRecipes.flatMap(toDbIngredientRows);
const dbSwapOptionRows: DbRow[] = Object.entries(catalog.swapMap).flatMap(([code, options]) =>
  options.map((ingredient_name) => ({ swap_group_code: code, ingredient_name })),
);
const referencedPairs = new Set(
  dbIngredientRows.map((row) => `${String(row.ingredient)}|${String(row.unit_code)}`),
);
const dbPairRows: DbRow[] = [...referencedPairs].map((key) => {
  const [ingredient, unit] = key.split("|");
  return { ingredient, unit };
});

const payload = assembleCatalogue(dbRecipeRows, dbIngredientRows, dbSwapOptionRows, dbPairRows);

check("the catalogue payload contains exactly the 385 launch-ready recipes, no more, no fewer", payload.recipes.length === 385);
check(
  "no HELD_FOR_KITCHEN_TEST recipe leaks into the served catalogue",
  payload.recipes.every((r) => launchReadyIds.has(r.id)),
);

const byId = new Map(payload.recipes.map((r) => [r.id, r]));
let idMismatch = 0;
let fieldMismatch = 0;
let ingredientMismatch = 0;
for (const original of launchReadyRecipes) {
  const mapped = byId.get(original.id);
  if (!mapped) {
    idMismatch++;
    continue;
  }
  const fieldsMatch =
    mapped.name === original.name &&
    mapped.mealType === original.mealType &&
    mapped.baseServes === original.baseServes &&
    mapped.prepMin === original.prepMin &&
    mapped.cookMin === original.cookMin &&
    mapped.budgetTier === original.budgetTier &&
    mapped.freezer === original.freezer &&
    mapped.lunchbox === original.lunchbox &&
    mapped.vegetarian === original.vegetarian &&
    mapped.gfAdaptable === original.gfAdaptable &&
    mapped.dfAdaptable === original.dfAdaptable &&
    mapped.onePot === original.onePot &&
    mapped.method === original.method &&
    (mapped.swapNotes || "") === (original.swapNotes || "");
  if (!fieldsMatch) fieldMismatch++;

  if (mapped.ingredients.length !== original.ingredients.length) {
    ingredientMismatch++;
    continue;
  }
  for (let i = 0; i < original.ingredients.length; i++) {
    const o = original.ingredients[i];
    const m = mapped.ingredients[i];
    const matches =
      m.number === o.number &&
      m.ingredient.toLowerCase() === o.ingredient.toLowerCase() &&
      m.baseQty === o.baseQty &&
      m.unit === o.unit &&
      m.optional === o.optional &&
      (m.swapGroup ?? undefined) === (o.swapGroup ?? undefined);
    if (!matches) ingredientMismatch++;
  }
}
check("every launch-ready recipe id round-trips through the seed-shape -> API mapping", idMismatch === 0);
check(
  "every engine-relevant field (used by engine.prototype.js's pass()/assess()/render) is preserved exactly",
  fieldMismatch === 0,
);
check(
  "every ingredient line is preserved (case-insensitively for the name, per the documented canonicalisation)",
  ingredientMismatch === 0,
);

check(
  "swapMap is reproduced exactly (it's a fixed 20-group catalogue, not scoped to which recipes are launch-approved)",
  JSON.stringify(payload.swapMap) === JSON.stringify(catalog.swapMap),
);

const originalPairKeys = new Set(
  catalog.recipes.flatMap((r) => r.ingredients.map((i) => `${i.ingredient.toLowerCase()}|${i.unit}`)),
);
check(
  "every served ingredient/unit pair is a real pair from the source catalogue (none invented)",
  payload.ingredientUnitPairs.every((p) => originalPairKeys.has(p.key)),
);
check(
  "ingredientUnitPairs is scoped down to only pairs used by launch-approved recipes (a tighter, intentional set" +
    ` than the source catalogue's ${catalog.ingredientUnitPairs.length} static pairs)`,
  payload.ingredientUnitPairs.length <= catalog.ingredientUnitPairs.length && payload.ingredientUnitPairs.length > 0,
);

if (failures > 0) {
  throw new Error(`${failures} check(s) failed.`);
}
console.log("\nAll Phase 7 catalogue API checks passed.");
