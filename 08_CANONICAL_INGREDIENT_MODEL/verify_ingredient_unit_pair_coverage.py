#!/usr/bin/env python3
"""Phase 4 verification: every one of the V1 prototype's 187
ingredientUnitPairs (03_WORKING_PROTOTYPE/data.js) resolves to a known
canonical ingredient and a unit this model has an explicit answer for --
either a universal conversion, an ingredient-specific conversion, or a
recorded MANUAL designation. Fails loudly on any orphaned key instead of
letting one slip through silently.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "03_WORKING_PROTOTYPE" / "data.js"
INGREDIENTS = ROOT / "08_CANONICAL_INGREDIENT_MODEL" / "canonical_ingredients_v1.json"
CONVERSIONS = ROOT / "08_CANONICAL_INGREDIENT_MODEL" / "unit_conversions_v1.json"

UNIVERSAL_UNIT_PAIRS = {("kg", "g"), ("g", "kg"), ("cup", "mL"), ("mL", "cup"),
                        ("tbsp", "mL"), ("mL", "tbsp"), ("tsp", "mL"), ("mL", "tsp")}


def main():
    text = DATA_JS.read_text()
    payload = text[text.index("=") + 1:].strip().rstrip(";")
    pairs = json.loads(payload)["ingredientUnitPairs"]

    canonical = {i["ingredient_key"]: i for i in json.loads(INGREDIENTS.read_text())["ingredients"]}
    conversions = json.loads(CONVERSIONS.read_text())["conversions"]
    ingredient_specific_units = {(c["ingredient_key"], c["from_unit_code"]) for c in conversions if c.get("ingredient_key")}

    orphaned = []
    for pair in pairs:
        key = pair["ingredient"].strip().lower()
        unit = pair["unit"]
        entry = canonical.get(key)
        if entry is None:
            orphaned.append((pair["key"], "unknown ingredient_key"))
            continue
        if entry["quantity_dimension"] == "MANUAL":
            continue  # explicitly manual -- accounted for, not orphaned
        if entry["canonical_unit_code"] is None:
            orphaned.append((pair["key"], "non-MANUAL entry missing a canonical_unit_code"))
            continue
        has_universal = (unit, entry["canonical_unit_code"]) in UNIVERSAL_UNIT_PAIRS or unit == entry["canonical_unit_code"]
        has_specific = (key, unit) in ingredient_specific_units
        if not (has_universal or has_specific):
            orphaned.append((pair["key"], f"no conversion path from {unit} to {entry['canonical_unit_code']}"))

    print(f"{len(pairs)} ingredient/unit pantry-price keys checked.")
    if orphaned:
        print(f"{len(orphaned)} ORPHANED key(s):")
        for key, reason in orphaned:
            print(f"  {key}: {reason}")
        sys.exit(1)
    print("All keys resolve to a known canonical ingredient and an explicit conversion path or MANUAL designation.")


if __name__ == "__main__":
    main()
