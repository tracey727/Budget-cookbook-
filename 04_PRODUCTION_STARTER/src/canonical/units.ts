/**
 * Phase 4 -- Canonical Ingredient, Unit & Pack Model.
 *
 * Pure functions over the data built by
 * 08_CANONICAL_INGREDIENT_MODEL/build_canonical_ingredients.py
 * (canonical_ingredients_v1.json, unit_conversions_v1.json). Nothing here
 * hits a database -- Phase 5 is where these tables actually land in Neon.
 */

export type QuantityDimension = "MASS" | "VOLUME" | "COUNT" | "MANUAL";

export interface CanonicalIngredient {
  ingredient_id: string;
  ingredient_key: string;
  quantity_dimension: QuantityDimension;
  canonical_unit_code: string | null;
}

export interface UnitConversion {
  ingredient_id: string | null; // null = universal, applies to any ingredient
  from_unit_code: string;
  to_unit_code: string;
  multiplier: number;
  verified: boolean;
}

export interface ConversionResult {
  value: number;
  verified: boolean;
}

/**
 * Convert `qty` of `fromUnit` to `toUnit` for a given ingredient. Looks for
 * an ingredient-specific conversion first (a density/yield fact particular
 * to this ingredient), then a universal one. Returns null -- never a
 * guessed number -- when no conversion path exists; per this phase's GREEN
 * gate, an unconvertible pair must be an explicit "I don't know", not a
 * silent identity conversion or a fabricated multiplier.
 */
export function convert(
  qty: number,
  fromUnit: string,
  toUnit: string,
  ingredientId: string,
  conversions: UnitConversion[],
): ConversionResult | null {
  if (fromUnit === toUnit) return { value: qty, verified: true };
  const specific = conversions.find(
    (c) => c.ingredient_id === ingredientId && c.from_unit_code === fromUnit && c.to_unit_code === toUnit,
  );
  if (specific) return { value: qty * specific.multiplier, verified: specific.verified };
  const universal = conversions.find(
    (c) => c.ingredient_id === null && c.from_unit_code === fromUnit && c.to_unit_code === toUnit,
  );
  if (universal) return { value: qty * universal.multiplier, verified: universal.verified };
  return null;
}

/**
 * How many whole packs must a household buy to cover `shortageQty` of an
 * ingredient, given a pack holds `packQty` in the same unit? Always rounds
 * up -- a household cannot purchase a fractional pack, and rounding down
 * would silently leave a real shortfall. Per Phase 10's future GREEN gate
 * ("no fractional tins/packs are presented as purchase instructions"),
 * this is the one place that rule is allowed to live.
 */
export function packsNeeded(shortageQty: number, packQty: number): number {
  if (packQty <= 0) {
    throw new Error(`packQty must be positive, got ${packQty}`);
  }
  if (shortageQty <= 0) return 0;
  return Math.ceil(shortageQty / packQty);
}
