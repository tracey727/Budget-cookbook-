import { Client } from "pg";

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
    const mealType = url.searchParams.get("mealType");
    const rows = await withDb(env, async (db) => {
      if (mealType && mealType !== "Any") {
        return db.query(
          `select recipe_id, meal_type, recipe_name, base_family, base_serves,
                  prep_min, cook_min, budget_tier, freezer_friendly,
                  lunchbox_friendly, vegetarian_base, gf_adaptable,
                  df_adaptable, one_pan_pot
             from recipes
            where meal_type = $1
            order by recipe_name
            limit 1000`,
          [mealType],
        );
      }
      return db.query(
        `select recipe_id, meal_type, recipe_name, base_family, base_serves,
                prep_min, cook_min, budget_tier, freezer_friendly,
                lunchbox_friendly, vegetarian_base, gf_adaptable,
                df_adaptable, one_pan_pot
           from recipes
          order by recipe_name
          limit 1000`,
      );
    });
    return json({ recipes: rows.rows, requestId }, 200, requestId);
  }

  const match = url.pathname.match(/^\/api\/recipes\/([^/]+)$/);
  if (match && request.method === "GET") {
    const recipeId = decodeURIComponent(match[1]);
    const payload = await withDb(env, async (db) => {
      const recipe = await db.query("select * from recipes where recipe_id = $1", [recipeId]);
      if (!recipe.rowCount) return null;
      const ingredients = await db.query(
        `select ri.line_no, i.canonical_name as ingredient, ri.base_qty, ri.unit_code,
                ri.optional, ri.swap_group_code
           from recipe_ingredients ri
           join ingredients i on i.ingredient_id = ri.ingredient_id
          where ri.recipe_id = $1
          order by ri.line_no`,
        [recipeId],
      );
      return { recipe: recipe.rows[0], ingredients: ingredients.rows };
    });
    if (!payload) throw new ApiError(404, "recipe_not_found");
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
