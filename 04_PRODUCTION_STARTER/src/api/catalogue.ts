/**
 * Phase 7 -- bulk catalogue payload for GET /api/catalogue.
 *
 * `public/engine.prototype.js` is preserved byte-for-byte (see
 * README_PRODUCTION_STARTER.md's migration note: "keeping the deterministic
 * calculation rules") to avoid changing engine behaviour silently. That
 * script reads `window.GENEVIEVE_DATA` synchronously and expects the exact
 * shape `data.prototype.js` used to provide -- including "Yes"/"No" string
 * flags rather than booleans, and field names like `gfAdaptable` rather
 * than the database's `gf_adaptable`. This module reproduces that legacy
 * contract deliberately, from live (launch-approved-only) data, rather than
 * exposing it as the general-purpose recipe API's shape (recipes.ts uses
 * clean camelCase + real booleans there instead, since that's a new
 * contract with no existing consumer to keep faithful to).
 */
import type { DbRow, SqlQuery } from "./recipes";

export interface EngineIngredient {
  number: number;
  ingredient: string;
  baseQty: number;
  unit: string;
  optional: boolean;
  swapGroup: string | null;
}

export interface EngineRecipe {
  id: string;
  mealType: string;
  name: string;
  family: string;
  baseServes: number;
  prepMin: number;
  cookMin: number;
  budgetTier: string | null;
  protein: string;
  carb: string;
  focus: string;
  freezer: "Yes" | "No";
  lunchbox: "Yes" | "No";
  vegetarian: "Yes" | "No";
  gfAdaptable: "Yes" | "No";
  dfAdaptable: "Yes" | "No";
  onePot: "Yes" | "No";
  method: string;
  swapNotes: string;
  ingredients: EngineIngredient[];
}

export interface IngredientUnitPair {
  ingredient: string;
  unit: string;
  key: string;
}

export interface CataloguePayload {
  recipes: EngineRecipe[];
  swapMap: Record<string, string[]>;
  ingredientUnitPairs: IngredientUnitPair[];
}

export function buildCatalogueRecipesQuery(): SqlQuery {
  return {
    text: `select recipe_id, meal_type, recipe_name, base_family, base_serves, prep_min, cook_min,
                  budget_tier, primary_protein, carb_base, produce_focus, freezer_friendly,
                  lunchbox_friendly, vegetarian_base, gf_adaptable, df_adaptable, one_pan_pot,
                  method_text, mix_change_notes
             from recipes
            where public_launch_approved = true
            order by recipe_id`,
    values: [],
  };
}

export function buildCatalogueIngredientsQuery(): SqlQuery {
  return {
    text: `select ri.recipe_id, ri.line_no, i.canonical_name as ingredient, ri.base_qty, ri.unit_code,
                  ri.optional, ri.swap_group_code
             from recipe_ingredients ri
             join ingredients i on i.ingredient_id = ri.ingredient_id
             join recipes r on r.recipe_id = ri.recipe_id
            where r.public_launch_approved = true
            order by ri.recipe_id, ri.line_no`,
    values: [],
  };
}

export function buildSwapMapQuery(): SqlQuery {
  return {
    text: `select swap_group_code, ingredient_name
             from swap_options
            order by swap_group_code, option_order`,
    values: [],
  };
}

/** Scoped to ingredients actually used by a launch-approved recipe, so the
 * pantry/price entry list a shopper sees never references a held-back
 * recipe's ingredients. */
export function buildIngredientUnitPairsQuery(): SqlQuery {
  return {
    text: `select distinct i.canonical_name as ingredient, ri.unit_code as unit
             from recipe_ingredients ri
             join ingredients i on i.ingredient_id = ri.ingredient_id
             join recipes r on r.recipe_id = ri.recipe_id
            where r.public_launch_approved = true
            order by ingredient, unit`,
    values: [],
  };
}

function yesNo(value: unknown): "Yes" | "No" {
  return value ? "Yes" : "No";
}

export function mapEngineIngredientRow(row: DbRow): EngineIngredient {
  return {
    number: Number(row.line_no),
    ingredient: String(row.ingredient),
    baseQty: Number(row.base_qty),
    unit: String(row.unit_code),
    optional: Boolean(row.optional),
    swapGroup: row.swap_group_code == null ? null : String(row.swap_group_code),
  };
}

export function mapEngineRecipeRow(recipeRow: DbRow, ingredientRows: DbRow[]): EngineRecipe {
  return {
    id: String(recipeRow.recipe_id),
    mealType: String(recipeRow.meal_type),
    name: String(recipeRow.recipe_name),
    family: String(recipeRow.base_family),
    baseServes: Number(recipeRow.base_serves),
    prepMin: Number(recipeRow.prep_min),
    cookMin: Number(recipeRow.cook_min),
    budgetTier: recipeRow.budget_tier == null ? null : String(recipeRow.budget_tier),
    protein: recipeRow.primary_protein == null ? "" : String(recipeRow.primary_protein),
    carb: recipeRow.carb_base == null ? "" : String(recipeRow.carb_base),
    focus: recipeRow.produce_focus == null ? "" : String(recipeRow.produce_focus),
    freezer: yesNo(recipeRow.freezer_friendly),
    lunchbox: yesNo(recipeRow.lunchbox_friendly),
    vegetarian: yesNo(recipeRow.vegetarian_base),
    gfAdaptable: yesNo(recipeRow.gf_adaptable),
    dfAdaptable: yesNo(recipeRow.df_adaptable),
    onePot: yesNo(recipeRow.one_pan_pot),
    method: String(recipeRow.method_text),
    swapNotes: recipeRow.mix_change_notes == null ? "" : String(recipeRow.mix_change_notes),
    ingredients: ingredientRows.map(mapEngineIngredientRow),
  };
}

export function assembleSwapMap(swapOptionRows: DbRow[]): Record<string, string[]> {
  const map: Record<string, string[]> = {};
  for (const row of swapOptionRows) {
    const code = String(row.swap_group_code);
    if (!map[code]) map[code] = [];
    map[code].push(String(row.ingredient_name));
  }
  return map;
}

export function mapIngredientUnitPairRow(row: DbRow): IngredientUnitPair {
  const ingredient = String(row.ingredient);
  const unit = String(row.unit);
  return { ingredient, unit, key: `${ingredient}|${unit}` };
}

export function assembleCatalogue(
  recipeRows: DbRow[],
  ingredientRows: DbRow[],
  swapOptionRows: DbRow[],
  pairRows: DbRow[],
): CataloguePayload {
  const ingredientsByRecipe = new Map<string, DbRow[]>();
  for (const row of ingredientRows) {
    const recipeId = String(row.recipe_id);
    const existing = ingredientsByRecipe.get(recipeId);
    if (existing) existing.push(row);
    else ingredientsByRecipe.set(recipeId, [row]);
  }

  return {
    recipes: recipeRows.map((row) => mapEngineRecipeRow(row, ingredientsByRecipe.get(String(row.recipe_id)) ?? [])),
    swapMap: assembleSwapMap(swapOptionRows),
    ingredientUnitPairs: pairRows.map(mapIngredientUnitPairRow),
  };
}
