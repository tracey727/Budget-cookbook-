/**
 * Phase 7 GREEN-gate check for the recipe list/filter + detail API: query
 * text/params are built safely (every caller-controlled value bound as a
 * parameter, never concatenated) and row mapping produces the documented
 * shape. Same standalone-assertion convention as src/dietary/*.test.ts --
 * see household.test.ts for the run command.
 */
import {
  DEFAULT_LIST_LIMIT,
  MAX_LIST_LIMIT,
  buildRecipeDetailQuery,
  buildRecipeIngredientsQuery,
  buildRecipeListQuery,
  mapRecipeDetailRow,
  mapRecipeSummaryRow,
  parseRecipeListFilters,
} from "./recipes";

let failures = 0;
function check(label: string, condition: boolean): void {
  if (condition) {
    console.log(`PASS ${label}`);
  } else {
    failures++;
    console.error(`FAIL ${label}`);
  }
}

function params(query: string): URLSearchParams {
  return new URL(`https://example.test/api/recipes${query}`).searchParams;
}

// --- parseRecipeListFilters ---

const empty = parseRecipeListFilters(params(""));
check("no params: every filter is undefined", [
  empty.mealType, empty.budgetTier, empty.vegetarian, empty.gfAdaptable, empty.dfAdaptable,
  empty.lunchboxFriendly, empty.freezerFriendly, empty.onePanPot, empty.maxPrepMin, empty.maxCookMin, empty.search,
].every((v) => v === undefined));
check("no params: limit defaults", empty.limit === DEFAULT_LIST_LIMIT);
check("no params: offset defaults to 0", empty.offset === 0);

check(
  "mealType=Any is treated as no filter, matching the prototype's pass() semantics",
  parseRecipeListFilters(params("?mealType=Any")).mealType === undefined,
);
check(
  "a real mealType value (with a slash) is preserved",
  parseRecipeListFilters(params("?mealType=Dinner%2FTea")).mealType === "Dinner/Tea",
);

for (const truthyValue of ["true", "1", "yes", "Required", "REQUIRED"]) {
  check(
    `vegetarian=${truthyValue} is treated as a hard filter`,
    parseRecipeListFilters(params(`?vegetarian=${truthyValue}`)).vegetarian === true,
  );
}
check(
  "vegetarian=false does not set the filter (absence, not a negative filter)",
  parseRecipeListFilters(params("?vegetarian=false")).vegetarian === undefined,
);

check("limit=0 clamps up to 1, never zero rows", parseRecipeListFilters(params("?limit=0")).limit === 1);
check(
  `limit=99999 clamps down to MAX_LIST_LIMIT (${MAX_LIST_LIMIT})`,
  parseRecipeListFilters(params("?limit=99999")).limit === MAX_LIST_LIMIT,
);
check(
  "limit=notanumber falls back to the default rather than crashing",
  parseRecipeListFilters(params("?limit=notanumber")).limit === DEFAULT_LIST_LIMIT,
);
check("offset=10 is preserved", parseRecipeListFilters(params("?offset=10")).offset === 10);
check(
  "offset=-5 (negative) is dropped back to 0, not sent through as -5",
  parseRecipeListFilters(params("?offset=-5")).offset === 0,
);

check(
  "search is trimmed",
  parseRecipeListFilters(params("?search=%20chicken%20")).search === "chicken",
);
check(
  "an empty search string is treated as no filter",
  parseRecipeListFilters(params("?search=")).search === undefined,
);
check(
  "maxPrepMin=-1 (invalid) is dropped rather than sent through negative",
  parseRecipeListFilters(params("?maxPrepMin=-1")).maxPrepMin === undefined,
);
check("maxPrepMin=15 is preserved", parseRecipeListFilters(params("?maxPrepMin=15")).maxPrepMin === 15);

// --- buildRecipeListQuery ---

const noFilterQuery = buildRecipeListQuery({ limit: 60, offset: 0 });
check(
  "every list query always gates on public_launch_approved = true",
  noFilterQuery.text.includes("public_launch_approved = true"),
);
check("no filters: only limit and offset are bound", noFilterQuery.values.length === 2);
check("no filters: values are [limit, offset] in that order", noFilterQuery.values[0] === 60 && noFilterQuery.values[1] === 0);
check("no filters: query text references $1 and $2 for limit/offset", noFilterQuery.text.includes("$1") && noFilterQuery.text.includes("$2"));

const filteredQuery = buildRecipeListQuery({
  mealType: "Dinner/Tea",
  search: "50% off_deal",
  vegetarian: true,
  maxPrepMin: 20,
  limit: 10,
  offset: 5,
});
check(
  "mealType is bound as a parameter, not concatenated into the SQL text",
  !filteredQuery.text.includes("Dinner/Tea") && filteredQuery.values.includes("Dinner/Tea"),
);
check(
  "search wildcard characters (% and _) are escaped so they match literally",
  filteredQuery.values.some((v) => v === "%50\\% off\\_deal%"),
);
check(
  "boolean filters compile to a fixed literal condition, not a bound parameter",
  filteredQuery.text.includes("vegetarian_base = true"),
);
check(
  "5 bound values: mealType, search, maxPrepMin, limit, offset",
  filteredQuery.values.length === 5,
);
check(
  "limit/offset are always the last two bound values regardless of which filters are present",
  filteredQuery.values[filteredQuery.values.length - 2] === 10 &&
    filteredQuery.values[filteredQuery.values.length - 1] === 5,
);

const maliciousSearch = buildRecipeListQuery({ search: "'; drop table recipes; --", limit: 5, offset: 0 });
check(
  "a hostile search string only ever appears as a bound parameter value, never inside the SQL text",
  !maliciousSearch.text.toLowerCase().includes("drop table") &&
    maliciousSearch.values.some((v) => typeof v === "string" && v.includes("drop table")),
);

// --- buildRecipeDetailQuery / buildRecipeIngredientsQuery ---

const detailQuery = buildRecipeDetailQuery("GEN-RCP-0001");
check("detail query binds the id as $1", detailQuery.values.length === 1 && detailQuery.values[0] === "GEN-RCP-0001");
check(
  "detail query also gates on public_launch_approved = true (a held-back recipe must 404, not display)",
  detailQuery.text.includes("public_launch_approved = true"),
);

const ingredientsQuery = buildRecipeIngredientsQuery("GEN-RCP-0001");
check(
  "ingredients query binds the id and orders by line_no",
  ingredientsQuery.values[0] === "GEN-RCP-0001" && ingredientsQuery.text.includes("order by ri.line_no"),
);

// --- mapRecipeSummaryRow / mapRecipeDetailRow ---

const summaryRow = {
  recipe_id: "GEN-RCP-0001",
  meal_type: "Breakfast",
  recipe_name: "Banana Cinnamon Overnight Oats",
  base_family: "Overnight oats",
  base_serves: "4.00", // pg can return numeric columns as strings
  prep_min: "8",
  cook_min: "0",
  budget_tier: "$",
  freezer_friendly: false,
  lunchbox_friendly: true,
  vegetarian_base: true,
  gf_adaptable: true,
  df_adaptable: true,
  one_pan_pot: false,
};
const summary = mapRecipeSummaryRow(summaryRow);
check("mapRecipeSummaryRow preserves the recipe id exactly", summary.id === "GEN-RCP-0001");
check("mapRecipeSummaryRow coerces numeric-string columns to numbers", summary.baseServes === 4 && summary.prepMin === 8);
check("mapRecipeSummaryRow maps booleans through unchanged", summary.lunchboxFriendly === true && summary.freezerFriendly === false);

const nullBudgetTier = mapRecipeSummaryRow({ ...summaryRow, budget_tier: null });
check("a null budget_tier maps to null, not the string 'null'", nullBudgetTier.budgetTier === null);

const detail = mapRecipeDetailRow(
  {
    ...summaryRow,
    primary_protein: null,
    carb_base: "oats",
    produce_focus: "banana",
    method_text: "1. Combine. | 2. Chill.",
    mix_change_notes: "Swap any fruit.",
  },
  [
    { line_no: 1, ingredient: "rolled oats", base_qty: "2", unit_code: "cup", optional: false, swap_group_code: "Oats/Breakfast Grain" },
    { line_no: 2, ingredient: "chia seeds", base_qty: "2", unit_code: "tbsp", optional: true, swap_group_code: null },
  ],
);
check("mapRecipeDetailRow maps a null primary_protein to null (not the string 'null')", detail.protein === null);
check("mapRecipeDetailRow preserves ingredient order and line numbers", detail.ingredients[0].number === 1 && detail.ingredients[1].number === 2);
check("mapRecipeDetailRow coerces ingredient base_qty to a number", detail.ingredients[0].baseQty === 2);
check("mapRecipeDetailRow maps a null swap_group_code to null", detail.ingredients[1].swapGroup === null);
check("mapRecipeDetailRow maps a present swap_group_code through unchanged", detail.ingredients[0].swapGroup === "Oats/Breakfast Grain");

if (failures > 0) {
  throw new Error(`${failures} check(s) failed.`);
}
console.log("\nAll Phase 7 recipe API checks passed.");
