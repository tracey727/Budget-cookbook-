import { Client } from "pg";

interface Env {
  ASSETS: Fetcher;
  HYPERDRIVE: { connectionString: string };
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
}

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });

async function withDb<T>(env: Env, fn: (client: Client) => Promise<T>): Promise<T> {
  const client = new Client({ connectionString: env.HYPERDRIVE.connectionString });
  await client.connect();
  try {
    return await fn(client);
  } finally {
    await client.end();
  }
}

async function api(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);

  if (url.pathname === "/api/health") {
    try {
      const result = await withDb(env, async (db) => db.query("select now() as database_time"));
      return json({ ok: true, databaseTime: result.rows[0]?.database_time ?? null });
    } catch (error) {
      return json({ ok: false, error: "database_unavailable" }, 503);
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
    return json({ recipes: rows.rows });
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
    return payload ? json(payload) : json({ error: "recipe_not_found" }, 404);
  }

  return json({ error: "not_found" }, 404);
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) {
      try {
        return await api(request, env);
      } catch (error) {
        console.error("api_error", error);
        return json({ error: "internal_error" }, 500);
      }
    }
    return env.ASSETS.fetch(request);
  },
};
