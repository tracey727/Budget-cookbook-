#!/usr/bin/env python3
"""Phase 4 -- Canonical Ingredient, Unit & Pack Model.

Assigns a stable canonical_ingredient_id and quantity_dimension to every one
of the 151 distinct ingredients in the V1 recipe bank (03_WORKING_PROTOTYPE/data.js),
and builds the unit conversion table needed to convert between the units a
recipe uses and the units retail packs are sold in --
schema/001_initial_schema.sql's `ingredients`/`unit_conversions` tables.

GREEN gate: "every launch ingredient converts deterministically or is
explicitly marked manual-only; no incompatible units are silently compared."
This script never invents a conversion it isn't confident in: an ingredient
whose recipe lines mix units that aren't safely convertible without a
product-specific density (e.g. "potato" used by cup, cup-cooked, g, kg and
"large") is assigned quantity_dimension MANUAL with no canonical_unit_code,
rather than picking one arbitrarily and quietly getting it wrong.
"""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "03_WORKING_PROTOTYPE" / "data.js"
OUT_INGREDIENTS = ROOT / "08_CANONICAL_INGREDIENT_MODEL" / "canonical_ingredients_v1.json"
OUT_CONVERSIONS = ROOT / "08_CANONICAL_INGREDIENT_MODEL" / "unit_conversions_v1.json"

# Stable namespace so re-running this script always produces the same
# ingredient_id for the same ingredient_key -- a "canonical" ID that can't
# drift between builds.
NAMESPACE = uuid.UUID("6f1d2a3b-6b8e-4c1a-9d3e-b0a1c2d3e4f5")

MASS_UNITS = {"g", "kg"}
VOLUME_UNITS = {"cup", "tbsp", "tsp"}
COUNT_UNITS = {"each", "large"}


def load_ingredient_units():
    text = DATA_JS.read_text()
    payload = text[text.index("=") + 1:].strip().rstrip(";")
    data = json.loads(payload)
    by_ing = {}
    for r in data["recipes"]:
        for ing in r["ingredients"]:
            name = ing["ingredient"].strip().lower()
            by_ing.setdefault(name, set()).add(ing["unit"])
    return by_ing


def classify(units):
    if units <= MASS_UNITS:
        return "MASS", "g"
    if units <= VOLUME_UNITS:
        return "VOLUME", "mL"
    if units <= COUNT_UNITS:
        return "COUNT", "each"
    return "MANUAL", None


def canonical_id(ingredient_key: str) -> str:
    return str(uuid.uuid5(NAMESPACE, ingredient_key))


# Universal, dimension-level conversions -- true by definition of the units
# themselves, not an estimate about any ingredient. verified=true.
UNIVERSAL_CONVERSIONS = [
    {"from_unit_code": "kg", "to_unit_code": "g", "multiplier": 1000, "notes": "Metric definition."},
    {"from_unit_code": "g", "to_unit_code": "kg", "multiplier": 0.001, "notes": "Metric definition."},
    {"from_unit_code": "cup", "to_unit_code": "mL", "multiplier": 250, "notes": "Australian/metric cup = 250 mL."},
    {"from_unit_code": "mL", "to_unit_code": "cup", "multiplier": 1 / 250, "notes": "Australian/metric cup = 250 mL."},
    {"from_unit_code": "tbsp", "to_unit_code": "mL", "multiplier": 20, "notes": "Australian tablespoon = 20 mL (NOT the US 15 mL tablespoon -- this product is AU-scoped, see REFERENCE_SOURCES.md)."},
    {"from_unit_code": "mL", "to_unit_code": "tbsp", "multiplier": 1 / 20, "notes": "Australian tablespoon = 20 mL."},
    {"from_unit_code": "tsp", "to_unit_code": "mL", "multiplier": 5, "notes": "Australian/metric teaspoon = 5 mL."},
    {"from_unit_code": "mL", "to_unit_code": "tsp", "multiplier": 1 / 5, "notes": "Australian/metric teaspoon = 5 mL."},
]

# Ingredient-specific density/yield conversions this script is confident
# enough to state as a reference value -- always verified=false (a real
# density belongs to a specific product, this is a widely-published average
# for the category), always with a note saying so. Deliberately NOT
# provided for protein/produce items where preparation state (raw/cooked/
# canned/diced/whole) makes a single value misleading -- those stay
# quantity_dimension MANUAL instead of getting a confident-looking number
# this script can't actually back up.
INGREDIENT_DENSITY_CONVERSIONS = [
    {"ingredient_key": "broccoli", "from_unit_code": "cup", "to_unit_code": "g", "multiplier": 90,
     "notes": "Reference average for chopped broccoli (~90 g/cup). Confirm against the specific product before high-precision use."},
    {"ingredient_key": "carrot", "from_unit_code": "cup", "to_unit_code": "g", "multiplier": 110,
     "notes": "Reference average for grated/chopped carrot (~110 g/cup). Confirm against the specific product."},
    {"ingredient_key": "pumpkin", "from_unit_code": "cup", "to_unit_code": "g", "multiplier": 120,
     "notes": "Reference average for diced raw pumpkin (~120 g/cup). Confirm against the specific product."},
]

# Dry:cooked volume yield ratios -- well-established culinary reference
# ratios (how much 1 cup of the dry/uncooked ingredient yields once cooked),
# needed for recipes that mix "cup"/"cup dry" and "cup cooked" lines of the
# same ingredient. Still verified=false: actual yield varies with cooking
# method and product. Expressed as multiplier from 1 cup DRY to N cups
# COOKED (from_unit_code/to_unit_code both "cup", disambiguated by ingredient
# + notes since the schema's unit_conversions table doesn't have a separate
# "cup dry" vs "cup cooked" unit code).
DRY_TO_COOKED_YIELD = [
    {"ingredient_key": "rice", "multiplier": 3.0, "notes": "1 cup dry rice yields ~3 cups cooked rice (reference ratio; varies by rice type and method)."},
    {"ingredient_key": "pasta", "multiplier": 2.0, "notes": "1 cup dry pasta yields ~2 cups cooked pasta (reference ratio; varies by shape)."},
    {"ingredient_key": "couscous", "multiplier": 2.0, "notes": "1 cup dry couscous yields ~2 cups cooked couscous (reference ratio)."},
    {"ingredient_key": "potato", "multiplier": 1.0, "notes": "Not a dry-goods yield case here -- potato mixes cup/cup cooked/g/kg/large for other reasons; left MANUAL, not given a yield ratio."},
]


def main():
    by_ing = load_ingredient_units()
    density_by_key = {d["ingredient_key"]: d for d in INGREDIENT_DENSITY_CONVERSIONS}
    yield_by_key = {d["ingredient_key"]: d for d in DRY_TO_COOKED_YIELD if d["ingredient_key"] != "potato"}

    ingredients = []
    manual_count = 0
    for name in sorted(by_ing):
        units = by_ing[name]
        dimension, canonical_unit = classify(units)
        if dimension == "MANUAL":
            manual_count += 1
        ingredients.append({
            "ingredient_id": canonical_id(name),
            "ingredient_key": name,
            "quantity_dimension": dimension,
            "canonical_unit_code": canonical_unit,
            "recipe_units_used": sorted(units),
            "has_ingredient_specific_conversion": name in density_by_key or name in yield_by_key,
        })

    conversions = []
    for c in UNIVERSAL_CONVERSIONS:
        conversions.append({**c, "ingredient_id": None, "verified": True})
    for key, c in density_by_key.items():
        conversions.append({
            "ingredient_id": canonical_id(key), "ingredient_key": key,
            "from_unit_code": c["from_unit_code"], "to_unit_code": c["to_unit_code"],
            "multiplier": c["multiplier"], "verified": False, "notes": c["notes"],
        })
    for key, c in yield_by_key.items():
        conversions.append({
            "ingredient_id": canonical_id(key), "ingredient_key": key,
            "from_unit_code": "cup dry", "to_unit_code": "cup cooked",
            "multiplier": c["multiplier"], "verified": False, "notes": c["notes"],
        })

    out_ingredients = {
        "schema_version": "1.0",
        "keying": "ingredient_id is a stable uuid5 derived from ingredient_key -- re-running this script "
                  "reproduces identical IDs. This IS the canonical ingredient ID Phase 2.2/2.4/2.5's "
                  "interim ingredient_key-based tables should be re-keyed onto.",
        "quantity_dimensions": ["MASS", "VOLUME", "COUNT", "MANUAL"],
        "ingredient_count": len(ingredients),
        "manual_dimension_count": manual_count,
        "ingredients": ingredients,
    }
    out_conversions = {
        "schema_version": "1.0",
        "note": "Universal conversions (verified=true) hold for any ingredient by definition of the units. "
                "Ingredient-specific conversions (verified=false) are reference/average values needing "
                "confirmation against a real product before high-precision use -- never treated as a launch "
                "safety fact the way the dietary engine's VERIFIED_PRESENT/ABSENT states are.",
        "conversions": conversions,
    }
    OUT_INGREDIENTS.write_text(json.dumps(out_ingredients, indent=2))
    OUT_CONVERSIONS.write_text(json.dumps(out_conversions, indent=2))
    print(f"{len(ingredients)} canonical ingredients: "
          f"{sum(1 for i in ingredients if i['quantity_dimension']=='MASS')} MASS, "
          f"{sum(1 for i in ingredients if i['quantity_dimension']=='VOLUME')} VOLUME, "
          f"{sum(1 for i in ingredients if i['quantity_dimension']=='COUNT')} COUNT, "
          f"{manual_count} MANUAL.")
    print(f"{len(conversions)} unit conversion rows "
          f"({sum(1 for c in conversions if c['verified'])} verified universal, "
          f"{sum(1 for c in conversions if not c['verified'])} reference ingredient-specific).")


if __name__ == "__main__":
    main()
