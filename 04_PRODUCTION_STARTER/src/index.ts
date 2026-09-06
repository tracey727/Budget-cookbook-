import { Client } from "pg";
import {
  buildRecipeDetailQuery,
  buildRecipeIngredientsQuery,
  buildRecipeListQuery,
  mapRecipeDetailRow,
  mapRecipeSummaryRow,
  parseRecipeListFilters,
} from "./api/recipes";
import {
  assembleCatalogue,
  buildCatalogueIngredientsQuery,
  buildCatalogueRecipesQuery,
  buildIngredientUnitPairsQuery,
  buildSwapMapQuery,
} from "./api/catalogue";

interface Env {
  ASSETS: Fetcher;
  HYPERDRIVE: { connectionString: string };
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
}

/**
 * Every response (success or error) carries the same request ID, both as a
 * header and in the body of error responses. This is the one identifier a
 * user can quote back to support, and the one value to grep for across
 * Worker logs, so it must never differ between the two.
 */
function newRequestId(): string {
  return crypto.randomUUID();
}

const json = (data: unknown, status = 200, requestId?: string) =>
  new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...(requestId ? { "x-request-id": requestId } : {}),
    },
  });

/**
 * A caught, expected failure mode (bad input, missing record, dependency
 * down) -- as opposed to a genuine bug, which falls through to the
 * top-level handler's catch-all instead. Keeping the two paths distinct
 * means an unexpected exception is never quietly reshaped to look like a
 * normal 4xx and lost from view.
 */
class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message?: string,
  ) {
    super(message ?? code);
  }
}

function errorResponse(error: unknown, requestId: string): Response {
  if (error instanceof ApiError) {
    return json({ error: error.code, requestId }, error.status, requestId);
  }
  // Anything else is unexpected: log the real error server-side (with the
  // request ID so it can be found), but never leak its detail to the
  // client -- only the request ID, for them to report back.
  console.error("unhandled_error", requestId, error);
  return json({ error: "internal_error", requestId }, 500, requestId);
}

async function withDb<T>(env: Env, fn: (client: Client) => Promise<T>): Promise<T> {
  const client = new Client({ connectionString: env.HYPERDRIVE.connectionString });
  await client.connect();
  try {
    return await fn(client);
  } finally {
    await client.end();
  }
}

async function api(request: Request, env: Env, requestId: string): Promise<Response> {
  const url = new URL(request.url);

  if (url.pathname === "/api/health") {
    try {
      const result = await withDb(env, async (db) => db.query("select now() as database_time"));
      return json({ ok: true, databaseTime: result.rows[0]?.database_time ?? null, requestId }, 200, requestId);
    } catch (error) {
      console.error("health_check_db_unavailable", requestId, error);
      return json({ ok: false, error: "database_unavailable", requestId }, 503, requestId);
    }
  }

  if (url.pathname === "/api/recipes" && request.method === "GET") {
    const filters = parseRecipeListFilters(url.searchParams);
    const query = buildRecipeListQuery(filters);
    const rows = await withDb(env, async (db) => db.query(query.text, query.values));
    return json({ recipes: rows.rows.map(mapRecipeSummaryRow), requestId }, 200, requestId);
  }

  const match = url.pathname.match(/^\/api\/recipes\/([^/]+)$/);
  if (match && request.method === "GET") {
    const recipeId = decodeURIComponent(match[1]);
    const payload = await withDb(env, async (db) => {
      const detailQuery = buildRecipeDetailQuery(recipeId);
      const recipe = await db.query(detailQuery.text, detailQuery.values);
      if (!recipe.rowCount) return null;
      const ingredientsQuery = buildRecipeIngredientsQuery(recipeId);
      const ingredients = await db.query(ingredientsQuery.text, ingredientsQuery.values);
      return mapRecipeDetailRow(recipe.rows[0], ingredients.rows);
    });
    if (!payload) throw new ApiError(404, "recipe_not_found");
    return json({ recipe: payload, requestId }, 200, requestId);
  }

  if (url.pathname === "/api/catalogue" && request.method === "GET") {
    const payload = await withDb(env, async (db) => {
      const recipesQuery = buildCatalogueRecipesQuery();
      const ingredientsQuery = buildCatalogueIngredientsQuery();
      const swapMapQuery = buildSwapMapQuery();
      const pairsQuery = buildIngredientUnitPairsQuery();
      const [recipes, ingredients, swapOptions, pairs] = await Promise.all([
        db.query(recipesQuery.text, recipesQuery.values),
        db.query(ingredientsQuery.text, ingredientsQuery.values),
        db.query(swapMapQuery.text, swapMapQuery.values),
        db.query(pairsQuery.text, pairsQuery.values),
      ]);
      return assembleCatalogue(recipes.rows, ingredients.rows, swapOptions.rows, pairs.rows);
    });
    return json({ ...payload, requestId }, 200, requestId);
  }

  throw new ApiError(404, "not_found");
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const requestId = newRequestId();
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) {
      try {
        return await api(request, env, requestId);
      } catch (error) {
        return errorResponse(error, requestId);
      }
    }
    const assetResponse = await env.ASSETS.fetch(request);
    const withRequestId = new Response(assetResponse.body, assetResponse);
    withRequestId.headers.set("x-request-id", requestId);
    return withRequestId;
  },
};
