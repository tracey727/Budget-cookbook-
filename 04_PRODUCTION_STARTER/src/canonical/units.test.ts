/**
 * Phase 4 checks. Run via `npm run test:units`.
 */
import { convert, packsNeeded, UnitConversion } from "./units";

let failures = 0;
function check(label: string, condition: boolean): void {
  if (condition) {
    console.log(`PASS ${label}`);
  } else {
    failures++;
    console.error(`FAIL ${label}`);
  }
}

const conversions: UnitConversion[] = [
  { ingredient_id: null, from_unit_code: "kg", to_unit_code: "g", multiplier: 1000, verified: true },
  { ingredient_id: null, from_unit_code: "cup", to_unit_code: "mL", multiplier: 250, verified: true },
  { ingredient_id: null, from_unit_code: "tbsp", to_unit_code: "mL", multiplier: 20, verified: true },
  { ingredient_id: "broccoli-id", from_unit_code: "cup", to_unit_code: "g", multiplier: 90, verified: false },
];

check("same-unit conversion is a verified identity", convert(2, "cup", "cup", "any-id", conversions)?.value === 2);
check("universal kg->g conversion applies to any ingredient", convert(1.5, "kg", "g", "any-id", conversions)?.value === 1500);
check("universal conversion is marked verified", convert(1, "kg", "g", "any-id", conversions)?.verified === true);
check(
  "Australian tablespoon uses 20 mL, not the US 15 mL",
  convert(1, "tbsp", "mL", "any-id", conversions)?.value === 20,
);
check(
  "an ingredient-specific conversion is used when present, and correctly marked unverified",
  (() => {
    const r = convert(2, "cup", "g", "broccoli-id", conversions);
    return r?.value === 180 && r?.verified === false;
  })(),
);
check(
  "the SAME cup->g conversion does NOT apply to a different ingredient with no specific entry",
  convert(2, "cup", "g", "carrot-id", conversions) === null,
);
check(
  "an unconvertible pair returns null rather than guessing",
  convert(1, "serve", "g", "bread-id", conversions) === null,
);

check("a shortage smaller than one pack still needs exactly 1 pack", packsNeeded(0.3, 1) === 1);
check("a shortage of exactly one pack needs 1 pack, not 0 or a fraction", packsNeeded(1, 1) === 1);
check("a shortage of 2.01 packs needs 3 whole packs", packsNeeded(2.01, 1) === 3);
check("zero shortage needs zero packs", packsNeeded(0, 1) === 0);
check("a negative shortage (already covered by pantry) needs zero packs", packsNeeded(-5, 1) === 0);
check(
  "a non-positive pack size is rejected rather than dividing by zero or a negative",
  (() => {
    try {
      packsNeeded(5, 0);
      return false;
    } catch {
      return true;
    }
  })(),
);

if (failures > 0) {
  throw new Error(`${failures} check(s) failed.`);
}
console.log("\nAll Phase 4 canonical unit checks passed.");
