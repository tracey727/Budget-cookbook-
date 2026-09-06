/**
 * Phase 7 -- Recipe Catalogue API.
 *
 * Pure query-building and row-shaping functions for GET /api/recipes (list/
 * filter) and GET /api/recipes/:id (detail). Kept free of any `pg`/Worker
 * dependency so they can be unit tested against plain fixture objects
 * without a live Postgres connection (see recipes.test.ts) -- the only
 * database access this repo can reach from this sandbox is blocked by
 * network policy (PHASE_6_CLOUDFLARE_WORKER_HYPERDRIVE_REPORT.md), so the
 * query text/params and row mapping are exactly what needs testing here.
 *
 * Every query below filters on `public_launch_approved = true`. That column
 * is the Phase 2.8 launch-readiness verdict (recipe_launch_readiness_v1.json
 * via scripts/build_seed_sql.py), not the separate dietary-claim "Launch
 * Rule" -- a recipe can be launch-approved for display while its dietary
 * requirement assessments are still UNVERIFIED pending human review.
 */

export interface RecipeListFilters {
  mealType?: string;
  budgetTier?: string;
  vegetarian?: boolean;
  gfAdaptable?: boolean;
  dfAdaptable?: boolean;
  lunchboxFriendly?: boolean;
  freezerFriendly?: boolean;
  onePanPot?: boolean;
  maxPrepMin?: number;
  maxCookMin?: number;
  search?: string;
  limit: number;
  offset: number;
}

export const DEFAULT_LIST_LIMIT = 60;
export const MAX_LIST_LIMIT = 200;

function truthy(value: string | null): boolean {
  if (value === null) return false;
  return ["true", "1", "yes", "required"].includes(value.toLowerCase());
}

function parsePositiveInt(value: string | null): number | undefined {
  if (value === null) return undefined;
  const n = Number.parseInt(value, 10);
  return Number.isFinite(n) && n >= 0 ? n : undefined;
}

/** Parses recipe-list query params. Unrecognised or malformed values are
 * dropped rather than rejected -- a bad filter should narrow to "no filter",
 * never crash the list endpoint. */
export function parseRecipeListFilters(searchParams: URLSearchParams): RecipeListFilters {
  const mealType = searchParams.get("mealType");
  const budgetTier = searchParams.get("budgetTier");
  const search = searchParams.get("search")?.trim();

  const limitRaw = parsePositiveInt(searchParams.get("limit"));
  const limit = limitRaw === undefined ? DEFAULT_LIST_LIMIT : Math.min(Math.max(limitRaw, 1), MAX_LIST_LIMIT);
  const offset = parsePositiveInt(searchParams.get("offset")) ?? 0;

  return {
    mealType: mealType && mealType !== "Any" ? mealType : undefined,
    budgetTier: budgetTier ?? undefined,
    vegetarian: truthy(searchParams.get("vegetarian")) || undefined,
    gfAdaptable: truthy(searchParams.get("gfAdaptable")) || undefined,
    dfAdaptable: truthy(searchParams.get("dfAdaptable")) || undefined,
    lunchboxFriendly: truthy(searchParams.get("lunchboxFriendly")) || undefined,
    freezerFriendly: truthy(searchParams.get("freezerFriendly")) || undefined,
    onePanPot: truthy(searchParams.get("onePanPot")) || undefined,
    maxPrepMin: parsePositiveInt(searchParams.get("maxPrepMin")),
    maxCookMin: parsePositiveInt(searchParams.get("maxCookMin")),
    search: search || undefined,
    limit,
    offset,
  };
}

const RECIPE_SUMMARY_COLUMNS = `recipe_id, meal_type, recipe_name, base_family, base_serves,
       prep_min, cook_min, budget_tier, freezer_friendly, lunchbox_friendly,
       vegetarian_base, gf_adaptable, df_adaptable, one_pan_pot`;

/** Escapes LIKE/ILIKE wildcard characters so a search term is matched
 * literally -- correctness, not injection safety (values are always bound
 * as query parameters below, never concatenated into SQL text). */
function escapeLikeTerm(term: string): string {
  return term.replace(/[\\%_]/g, (c) => `\\${c}`);
}

export interface SqlQuery {
  text: string;
  values: unknown[];
}

/** Builds the parameterised SQL for GET /api/recipes. Every value the
 * caller controls is bound positionally ($1, $2, ...) -- never
 * string-concatenated into `text` -- so arbitrary filter/search input
 * cannot change the query's shape. */
export function buildRecipeListQuery(filters: RecipeListFilters): SqlQuery {
  const conditions: string[] = ["public_launch_approved = true"];
  const values: unknown[] = [];

  const bind = (fragment: string, value: unknown) => {
    values.push(value);
    conditions.push(fragment.replace("?", `$${values.length}`));
  };

  if (filters.mealType) bind("meal_type = ?", filters.mealType);
  if (filters.budgetTier) bind("budget_tier = ?", filters.budgetTier);
  if (filters.vegetarian) conditions.push("vegetarian_base = true");
  if (filters.gfAdaptable) conditions.push("gf_adaptable = true");
  if (filters.dfAdaptable) conditions.push("df_adaptable = true");
  if (filters.lunchboxFriendly) conditions.push("lunchbox_friendly = true");
  if (filters.freezerFriendly) conditions.push("freezer_friendly = true");
  if (filters.onePanPot) conditions.push("one_pan_pot = true");
  if (filters.maxPrepMin !== undefined) bind("prep_min <= ?", filters.maxPrepMin);
  if (filters.maxCookMin !== undefined) bind("cook_min <= ?", filters.maxCookMin);
  if (filters.search) bind("recipe_name ilike ? escape '\\'", `%${escapeLikeTerm(filters.search)}%`);

  values.push(filters.limit);
  const limitParam = `$${values.length}`;
  values.push(filters.offset);
  const offsetParam = `$${values.length}`;

  const text = `select ${RECIPE_SUMMARY_COLUMNS}
     from recipes
    where ${conditions.join(" and ")}
    order by recipe_name
    limit ${limitParam} offset ${offsetParam}`;

  return { text, values };
}

/** GET /api/recipes/:id detail query -- id is always bound as $1. */
export function buildRecipeDetailQuery(recipeId: string): SqlQuery {
  return {
    text: `select recipe_id, meal_type, recipe_name, base_family, base_serves, prep_min, cook_min,
                  budget_tier, primary_protein, carb_base, produce_focus, freezer_friendly,
                  lunchbox_friendly, vegetarian_base, gf_adaptable, df_adaptable, one_pan_pot,
                  method_text, mix_change_notes
             from recipes
            where recipe_id = $1 and public_launch_approved = true`,
    values: [recipeId],
  };
}

export function buildRecipeIngredientsQuery(recipeId: string): SqlQuery {
  return {
    text: `select ri.line_no, i.canonical_name as ingredient, ri.base_qty, ri.unit_code,
                  ri.optional, ri.swap_group_code
             from recipe_ingredients ri
             join ingredients i on i.ingredient_id = ri.ingredient_id
            where ri.recipe_id = $1
            order by ri.line_no`,
    values: [recipeId],
  };
}

export interface RecipeSummary {
  id: string;
  mealType: string;
  name: string;
  family: string;
  baseServes: number;
  prepMin: number;
  cookMin: number;
  budgetTier: string | null;
  freezerFriendly: boolean;
  lunchboxFriendly: boolean;
  vegetarian: boolean;
  gfAdaptable: boolean;
  dfAdaptable: boolean;
  onePot: boolean;
}

export interface RecipeIngredientDetail {
  number: number;
  ingredient: string;
  baseQty: number;
  unit: string;
  optional: boolean;
  swapGroup: string | null;
}

export interface RecipeDetail extends RecipeSummary {
  protein: string | null;
  carb: string | null;
  focus: string | null;
  method: string;
  swapNotes: string | null;
  ingredients: RecipeIngredientDetail[];
}

/** Row shape returned by the pg driver: numeric/boolean columns can arrive
 * as strings depending on driver config, so every field is coerced rather
 * than trusted as already-typed. */
export type DbRow = Record<string, unknown>;

export function mapRecipeSummaryRow(row: DbRow): RecipeSummary {
  return {
    id: String(row.recipe_id),
    mealType: String(row.meal_type),
    name: String(row.recipe_name),
    family: String(row.base_family),
    baseServes: Number(row.base_serves),
    prepMin: Number(row.prep_min),
    cookMin: Number(row.cook_min),
    budgetTier: row.budget_tier == null ? null : String(row.budget_tier),
    freezerFriendly: Boolean(row.freezer_friendly),
    lunchboxFriendly: Boolean(row.lunchbox_friendly),
    vegetarian: Boolean(row.vegetarian_base),
    gfAdaptable: Boolean(row.gf_adaptable),
    dfAdaptable: Boolean(row.df_adaptable),
    onePot: Boolean(row.one_pan_pot),
  };
}

export function mapRecipeIngredientRow(row: DbRow): RecipeIngredientDetail {
  return {
    number: Number(row.line_no),
    ingredient: String(row.ingredient),
    baseQty: Number(row.base_qty),
    unit: String(row.unit_code),
    optional: Boolean(row.optional),
    swapGroup: row.swap_group_code == null ? null : String(row.swap_group_code),
  };
}

export function mapRecipeDetailRow(recipeRow: DbRow, ingredientRows: DbRow[]): RecipeDetail {
  return {
    ...mapRecipeSummaryRow(recipeRow),
    protein: recipeRow.primary_protein == null ? null : String(recipeRow.primary_protein),
    carb: recipeRow.carb_base == null ? null : String(recipeRow.carb_base),
    focus: recipeRow.produce_focus == null ? null : String(recipeRow.produce_focus),
    method: String(recipeRow.method_text),
    swapNotes: recipeRow.mix_change_notes == null ? null : String(recipeRow.mix_change_notes),
    ingredients: ingredientRows.map(mapRecipeIngredientRow),
  };
}
