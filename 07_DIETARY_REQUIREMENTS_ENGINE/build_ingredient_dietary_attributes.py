#!/usr/bin/env python3
"""Phase 2.2 — Canonical Ingredient Dietary Attribute Model.

Builds an evidence-based dietary attribute record for every distinct ingredient
name used across the 800-recipe V1 baseline (03_WORKING_PROTOTYPE/data.js),
using the attribute dictionary in INGREDIENT_ATTRIBUTE_CODES.md and the
evidence states / requirement classes frozen in DIETARY_TAXONOMY.json v1.1.

Interim keying: canonical ingredient IDs are not assigned until Phase 4
(01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md). This script
keys attribute records by normalised ingredient name instead, and that key
must be re-mapped onto `ingredients.ingredient_id` (schema/001_initial_schema.sql)
when Phase 4/5 assigns canonical IDs -- see the note in
INGREDIENT_DIETARY_ATTRIBUTE_MODEL_REPORT.md.

Deliberately does NOT string-match at evaluation time (Phase 2.2's GREEN gate
requires the model to express requirement classes without relying only on
ingredient-name matching): this script performs the matching ONCE, offline,
producing a reviewed evidence table. Phase 2.4 recipe classification and the
production engine read this table's attribute_code/evidence_state pairs, not
the raw ingredient text.

"X or Y" ingredient lines (e.g. "butter or oil") are a real recipe-writing
pattern in this dataset for swap-flexible slots. Where the two alternatives
disagree on an attribute, this script marks it CONDITIONAL rather than
picking one side -- the household's actual choice determines the outcome.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "03_WORKING_PROTOTYPE" / "data.js"
OUT_JSON = ROOT / "07_DIETARY_REQUIREMENTS_ENGINE" / "ingredient_dietary_attributes_v1.json"

VERIFIED_PRESENT = "VERIFIED_PRESENT"
VERIFIED_ABSENT = "VERIFIED_ABSENT"
CONDITIONAL = "CONDITIONAL"
UNVERIFIED = "UNVERIFIED"

AU_OATS_NOTE = (
    "Australian gluten-free claim boundary: oats are modelled separately from "
    "other gluten cereals. Do not treat as coeliac-safe unless the specific "
    "product is a verified gluten-free-certified oat source "
    "(see 07_DIETARY_REQUIREMENTS_ENGINE/REFERENCE_SOURCES.md)."
)


def attr(code, value, state, note=None, source="generic ingredient identity, as named in the recipe bank"):
    return {"attribute_code": code, "attribute_value": value, "evidence_state": state,
            "notes": note, "source_reference": source}


# Exact-match rules for whole ingredient terms (checked before any decomposition).
# Each entry is a list of attr() records. Anything not listed defaults to a
# plant/no-major-allergen assumption with ANIMAL_DERIVED=false, which is safe
# for this recipe bank because every ingredient is a plain generic pantry
# term (no branded products) -- see the report's "what this model does not
# cover" section for the limits of that assumption.
EXACT_RULES = {
    "chicken": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("POULTRY", "true", VERIFIED_PRESENT)],
    "beef mince": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("MEAT_BEEF", "true", VERIFIED_PRESENT)],
    "pork": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("MEAT_PORK", "true", VERIFIED_PRESENT)],
    "ham": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("MEAT_PORK", "true", VERIFIED_PRESENT)],
    "sausages": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT),
                 attr("MEAT_PORK", "true", CONDITIONAL, "Recipe does not specify sausage type; beef/plant-based sausages are also sold. Verify product before excluding for a pork-free member.")],
    "leftover roast meat": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT,
                                  "Meat type (beef/pork/poultry/lamb) not specified by the recipe -- 'any leftover roast'. Treat MEAT_BEEF/MEAT_PORK/POULTRY as UNVERIFIED, not false, until the household states what was roasted; do not code a specific meat-type attribute from a guess.")],
    "tuna": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("FISH", "true", VERIFIED_PRESENT),
             attr("ALLERGEN_FISH", "true", VERIFIED_PRESENT)],
    "egg": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("EGG", "true", VERIFIED_PRESENT),
            attr("ALLERGEN_EGG", "true", VERIFIED_PRESENT)],
    "eggs": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("EGG", "true", VERIFIED_PRESENT),
             attr("ALLERGEN_EGG", "true", VERIFIED_PRESENT)],
    "milk": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("DAIRY_MILK", "true", VERIFIED_PRESENT),
             attr("ALLERGEN_MILK", "true", VERIFIED_PRESENT)],
    "coconut milk": [attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT),
                      attr("DAIRY_MILK", "false", VERIFIED_ABSENT,
                           "Coconut milk is plant-derived. Named 'milk' but must NOT be classified as dairy or as the AU milk allergen -- naive substring matching on 'milk' would get this wrong, which is exactly the failure mode this model exists to avoid.")],
    "cheese": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("DAIRY_MILK", "true", VERIFIED_PRESENT),
               attr("ALLERGEN_MILK", "true", VERIFIED_PRESENT)],
    "cottage cheese": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("DAIRY_MILK", "true", VERIFIED_PRESENT),
                        attr("ALLERGEN_MILK", "true", VERIFIED_PRESENT)],
    "ricotta": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("DAIRY_MILK", "true", VERIFIED_PRESENT),
                attr("ALLERGEN_MILK", "true", VERIFIED_PRESENT)],
    "yoghurt": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("DAIRY_MILK", "true", VERIFIED_PRESENT),
                attr("ALLERGEN_MILK", "true", VERIFIED_PRESENT)],
    "yoghurt dressing": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("DAIRY_MILK", "true", VERIFIED_PRESENT),
                          attr("ALLERGEN_MILK", "true", VERIFIED_PRESENT)],
    "creamy garlic sauce": [attr("DAIRY_MILK", "true", CONDITIONAL, "Cream-based sauces are conventionally dairy; verify the specific product/recipe if a dairy-free version is used."),
                             attr("ALLERGEN_MILK", "true", CONDITIONAL),
                             attr("GARLIC_CONTENT", "true", VERIFIED_PRESENT, "Named in the ingredient itself.")],
    "onion": [attr("ONION_CONTENT", "true", VERIFIED_PRESENT), attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT)],
    "garlic seasoning": [attr("GARLIC_CONTENT", "true", VERIFIED_PRESENT, "Named in the ingredient itself."),
                          attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT)],
    "coffee": [attr("CAFFEINE_CONTENT", "true", VERIFIED_PRESENT), attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT)],
    "honey": [attr("HONEY_BEE_DERIVED", "true", VERIFIED_PRESENT), attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT,
              "Bee-derived. Relevant to VEGAN, not to VEGETARIAN.")],
    "peanut": [attr("ALLERGEN_PEANUT", "true", VERIFIED_PRESENT)],
    "peanut butter": [attr("ALLERGEN_PEANUT", "true", VERIFIED_PRESENT)],
    "peanut sauce": [attr("ALLERGEN_PEANUT", "true", VERIFIED_PRESENT)],
    "peanut oat": [attr("ALLERGEN_PEANUT", "true", VERIFIED_PRESENT)],
    "hummus": [attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT),
               attr("ALLERGEN_SESAME", "true", CONDITIONAL,
                    "Standard hummus is made with tahini (sesame paste). Not named in the ingredient text -- hidden-source risk. Verify for a sesame-allergic member rather than trusting the name.")],
    "pesto veg sauce": [attr("DAIRY_MILK", "true", CONDITIONAL,
                              "Traditional pesto contains parmesan (dairy) and pine nuts. Not named in the ingredient text -- hidden-source risk."),
                         attr("ALLERGEN_PINE_NUT", "true", CONDITIONAL,
                              "Traditional pesto contains pine nuts. Hidden-source risk; verify product/recipe."),
                         attr("GARLIC_CONTENT", "true", CONDITIONAL,
                              "Garlic is a core traditional pesto ingredient, not named in the ingredient text.")],
    "mild curry powder or paste": [attr("FISH", "unspecified", CONDITIONAL,
                                         "Some commercial curry pastes contain shrimp/fish paste. Not named in the ingredient text -- hidden-source risk; verify product for fish/shellfish allergy."),
                                    attr("ALLERGEN_CRUSTACEAN", "unspecified", CONDITIONAL,
                                         "Some commercial curry pastes contain shrimp paste. Verify product.")],
    "mild curry sauce": [attr("FISH", "unspecified", CONDITIONAL,
                               "Some commercial curry sauces/pastes contain shrimp paste. Verify product for fish/shellfish allergy."),
                          attr("DAIRY_MILK", "true", CONDITIONAL, "Curry sauces are often cream/yoghurt based; verify product.")],
    "bbq sauce": [attr("FISH", "unspecified", CONDITIONAL, "Some commercial BBQ sauces include Worcestershire sauce, which typically contains anchovy. Hidden-source risk; verify product for fish allergy.")],
    "bbq tomato sauce": [attr("FISH", "unspecified", CONDITIONAL, "Some commercial BBQ-style sauces include Worcestershire sauce (anchovy). Hidden-source risk; verify product.")],
    "soy garlic sauce": [attr("ALLERGEN_SOY", "true", VERIFIED_PRESENT),
                          attr("ALLERGEN_WHEAT", "true", CONDITIONAL, "Traditional soy sauce is brewed with wheat; tamari is a wheat-free alternative. Verify product for a wheat allergy."),
                          attr("GARLIC_CONTENT", "true", VERIFIED_PRESENT, "Named in the ingredient itself.")],
    "honey soy sauce": [attr("ALLERGEN_SOY", "true", VERIFIED_PRESENT), attr("HONEY_BEE_DERIVED", "true", VERIFIED_PRESENT),
                         attr("ALLERGEN_WHEAT", "true", CONDITIONAL, "Traditional soy sauce is brewed with wheat; tamari is a wheat-free alternative.")],
    "teriyaki sauce": [attr("ALLERGEN_SOY", "true", VERIFIED_PRESENT),
                        attr("ALLERGEN_WHEAT", "true", CONDITIONAL, "Traditional soy sauce base is brewed with wheat; verify product.")],
    "chocolate": [attr("DAIRY_MILK", "true", CONDITIONAL, "Milk chocolate is dairy; dark/vegan chocolate exists. Hidden-source risk if the product isn't specified."),
                  attr("ALLERGEN_SOY", "unspecified", CONDITIONAL, "Soy lecithin is a common chocolate emulsifier. Verify product."),
                  attr("CAFFEINE_CONTENT", "true", CONDITIONAL, "Cocoa naturally contains caffeine/theobromine; amount varies by product.")],
    "choc chip": [attr("DAIRY_MILK", "true", CONDITIONAL, "Milk chocolate chips are common; dairy-free chips exist. Verify product."),
                  attr("ALLERGEN_SOY", "unspecified", CONDITIONAL, "Soy lecithin is a common chocolate emulsifier. Verify product."),
                  attr("CAFFEINE_CONTENT", "true", CONDITIONAL, "Cocoa naturally contains caffeine/theobromine; amount varies by product.")],
    "cocoa oat": [attr("CAFFEINE_CONTENT", "true", CONDITIONAL, "Contains cocoa, which naturally contains caffeine/theobromine."),
                  attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT)],
    "caramel": [attr("DAIRY_MILK", "true", CONDITIONAL, "Traditional caramel is made with butter/cream. Hidden-source risk if the product isn't specified.")],
    "vanilla": [attr("ALCOHOL_CONTENT", "unspecified", CONDITIONAL, "Vanilla extract is conventionally alcohol-based; vanilla essence/paste formulations vary. Hidden-source risk for an alcohol-free requirement; verify product.")],
    "sultana": [attr("ALLERGEN_SULPHITES", "unspecified", CONDITIONAL, "Dried fruit including sultanas is commonly treated with sulphur dioxide (220) as a preservative. Hidden-source risk; verify product for a sulphite-sensitive member.")],
    "sultana oat": [attr("ALLERGEN_SULPHITES", "unspecified", CONDITIONAL, "Contains sultanas; dried fruit is commonly sulphured. Verify product.")],
    "stock": [attr("ANIMAL_DERIVED", "unspecified", UNVERIFIED, "Recipe does not specify chicken/beef/vegetable stock. A certified vegetable stock is required for vegetarian/vegan; do not assume plant-based from the name alone.")],
    "baked beans": [attr("ANIMAL_DERIVED", "false", CONDITIONAL, "Standard baked beans (beans in tomato sauce) are vegetarian, but some brands add pork/bacon. Verify product for a strict vegetarian/pork-free member.")],
    "couscous": [attr("ALLERGEN_WHEAT", "true", VERIFIED_PRESENT, "Couscous is made from wheat semolina -- not gluten-free despite sometimes being treated like a plain grain."),
                 attr("GLUTEN_CEREAL_WHEAT", "true", VERIFIED_PRESENT)],
    "noodles": [attr("ALLERGEN_WHEAT", "unspecified", CONDITIONAL, "Recipe does not specify wheat noodles vs. rice/gluten-free noodles. Verify product for a wheat allergy or coeliac requirement."),
                attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT)],
    "pasta": [attr("ALLERGEN_WHEAT", "true", VERIFIED_PRESENT, "Standard pasta is wheat-based; a gluten-free pasta swap is available via the Pasta swap group but changes this attribute for the adapted version, not the base recipe."),
              attr("GLUTEN_CEREAL_WHEAT", "true", VERIFIED_PRESENT),
              attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT)],
    # -- sub-terms that only ever appear inside "X or Y" compound lines, plus
    # explicit ANIMAL_DERIVED backfill for every EXACT_RULES entry above that
    # didn't already state one. Every ingredient must resolve ANIMAL_DERIVED
    # explicitly -- leaving it to an implicit default is exactly the kind of
    # silent gap Phase 2.2 exists to close.
    "butter": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("DAIRY_MILK", "true", VERIFIED_PRESENT),
               attr("ALLERGEN_MILK", "true", VERIFIED_PRESENT)],
    "melted butter": [attr("ANIMAL_DERIVED", "true", VERIFIED_PRESENT), attr("DAIRY_MILK", "true", VERIFIED_PRESENT),
                       attr("ALLERGEN_MILK", "true", VERIFIED_PRESENT)],
    "plant spread": [attr("ANIMAL_DERIVED", "unspecified", CONDITIONAL, "Marketed as a plant spread/margarine, but some blends contain buttermilk or milk solids. Verify product for a dairy-free requirement."),
                      attr("DAIRY_MILK", "unspecified", CONDITIONAL, "Some margarine/plant-spread blends contain buttermilk or milk solids. Verify product.")],
    "oil": [attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT), attr("DAIRY_MILK", "false", VERIFIED_ABSENT)],
    "syrup": [attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT), attr("HONEY_BEE_DERIVED", "false", VERIFIED_ABSENT)],
    "water": [attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT), attr("DAIRY_MILK", "false", VERIFIED_ABSENT),
              attr("ALLERGEN_MILK", "false", VERIFIED_ABSENT)],
    "brown sugar": [attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT), attr("HONEY_BEE_DERIVED", "false", VERIFIED_ABSENT)],
    "seed butter": [attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT),
                     attr("ALLERGEN_SESAME", "unspecified", CONDITIONAL, "'Seed butter' may be sunflower, sesame (tahini) or another seed. Verify product for a sesame allergy.")],
    "oats": [attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT), attr("ALLERGEN_OATS", "true", VERIFIED_PRESENT, AU_OATS_NOTE),
             attr("GLUTEN_CEREAL_OATS", "true", VERIFIED_PRESENT, AU_OATS_NOTE)],
}

# ANIMAL_DERIVED backfill for exact-match entries defined above that address a
# different question (an allergen or hidden-source flag) but didn't also state
# whether the ingredient itself is animal-derived. Every one of these is a
# manual, reasoned call -- not a blanket default -- based on what the named
# ingredient conventionally is.
_ANIMAL_DERIVED_BACKFILL = {
    "peanut": ("false", VERIFIED_ABSENT, None),
    "peanut butter": ("false", VERIFIED_ABSENT, None),
    "peanut sauce": ("false", VERIFIED_ABSENT, None),
    "peanut oat": ("false", VERIFIED_ABSENT, None),
    "creamy garlic sauce": ("true", CONDITIONAL, "Follows the DAIRY_MILK assessment for this ingredient: conventionally cream-based."),
    "pesto veg sauce": ("true", CONDITIONAL, "Follows the DAIRY_MILK/pine-nut assessment: traditional pesto contains parmesan."),
    "mild curry powder or paste": ("unspecified", CONDITIONAL, "Some commercial curry pastes contain shrimp paste; verify product."),
    "mild curry sauce": ("unspecified", CONDITIONAL, "Curry sauces are often cream/yoghurt based and some pastes contain shrimp paste; verify product."),
    "bbq sauce": ("unspecified", CONDITIONAL, "Some commercial BBQ sauces include Worcestershire sauce (anchovy); verify product."),
    "bbq tomato sauce": ("unspecified", CONDITIONAL, "Some commercial BBQ-style sauces include Worcestershire sauce (anchovy); verify product."),
    "soy garlic sauce": ("false", VERIFIED_ABSENT, None),
    "honey soy sauce": ("true", VERIFIED_PRESENT, "Honey is bee-derived."),
    "teriyaki sauce": ("false", VERIFIED_ABSENT, None),
    "chocolate": ("true", CONDITIONAL, "Follows the DAIRY_MILK assessment: milk chocolate is common."),
    "choc chip": ("true", CONDITIONAL, "Follows the DAIRY_MILK assessment: milk chocolate chips are common."),
    "caramel": ("true", CONDITIONAL, "Follows the DAIRY_MILK assessment: traditional caramel uses butter/cream."),
    "vanilla": ("false", VERIFIED_ABSENT, None),
    "sultana": ("false", VERIFIED_ABSENT, None),
    "sultana oat": ("false", VERIFIED_ABSENT, None),
    "baked beans": None,  # already states ANIMAL_DERIVED explicitly
    "couscous": ("false", VERIFIED_ABSENT, None),
    "hummus": None,  # already explicit
    "coconut milk": None,  # already explicit
}
for _term, _backfill in _ANIMAL_DERIVED_BACKFILL.items():
    if _backfill is None:
        continue
    _existing = EXACT_RULES.get(_term, [])
    if not any(a["attribute_code"] == "ANIMAL_DERIVED" for a in _existing):
        _value, _state, _note = _backfill
        EXACT_RULES.setdefault(_term, []).append(attr("ANIMAL_DERIVED", _value, _state, _note))

# Flour / bread / oat family -- shared wheat and oat rules by substring, applied
# after exact matches. Order matters: oats checked separately from plain wheat.
BREAD_FAMILY = ["bread", "bread rolls", "english muffins", "pita bread", "wraps"]
WHEAT_TERMS = ["plain flour", "self-raising flour", "wholemeal flour", "breadcrumbs", "crackers"] + BREAD_FAMILY
OAT_TERMS = ["rolled oats", "oat flour"]

for term in WHEAT_TERMS:
    EXACT_RULES.setdefault(term, []).extend([
        attr("ALLERGEN_WHEAT", "true", VERIFIED_PRESENT if term != "crackers" else CONDITIONAL,
             None if term != "crackers" else "Most crackers are wheat-based but gluten-free crackers exist; verify product."),
        attr("GLUTEN_CEREAL_WHEAT", "true", VERIFIED_PRESENT if term != "crackers" else CONDITIONAL),
    ])
for term in OAT_TERMS:
    EXACT_RULES.setdefault(term, []).extend([
        attr("ALLERGEN_OATS", "true", VERIFIED_PRESENT, AU_OATS_NOTE),
        attr("GLUTEN_CEREAL_OATS", "true", VERIFIED_PRESENT, AU_OATS_NOTE),
    ])
EXACT_RULES["crackers or oats"] = [
    attr("ALLERGEN_WHEAT", "unspecified", CONDITIONAL, "Crackers alternative is typically wheat-based; oats alternative falls under the AU oats claim boundary."),
    attr("ALLERGEN_OATS", "unspecified", CONDITIONAL, AU_OATS_NOTE),
    attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT),
]

# ANIMAL_DERIVED for the flour/bread/oat/cracker family: all plant-based, but
# commercial bread-family products commonly include milk powder or an egg
# glaze that a plain ingredient name doesn't reveal -- flagged, not assumed.
for term in ["plain flour", "self-raising flour", "wholemeal flour", "breadcrumbs", "crackers", "rolled oats", "oat flour"]:
    EXACT_RULES[term].append(attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT))
for term in BREAD_FAMILY:
    EXACT_RULES[term].append(attr("ANIMAL_DERIVED", "unspecified", CONDITIONAL,
                                   "Commercial bread/wraps/muffins commonly contain milk powder or an egg glaze not implied by the plain ingredient name. Verify product for a dairy-free/vegan requirement."))
    EXACT_RULES[term].append(attr("DAIRY_MILK", "unspecified", CONDITIONAL,
                                   "Commercial bread-family products commonly contain milk powder. Verify product."))

_ALL_INGREDIENT_TERMS_WITH_RULES = set(EXACT_RULES)
_MISSING_ANIMAL_DERIVED = [t for t in _ALL_INGREDIENT_TERMS_WITH_RULES
                            if not any(a["attribute_code"] == "ANIMAL_DERIVED" for a in EXACT_RULES[t])]
assert not _MISSING_ANIMAL_DERIVED, f"Every EXACT_RULES entry must resolve ANIMAL_DERIVED explicitly; missing for: {_MISSING_ANIMAL_DERIVED}"


def classify_atomic(term):
    """Return the attribute list for a single (non-compound) ingredient term."""
    term = term.strip().lower()
    if term in EXACT_RULES:
        return list(EXACT_RULES[term])
    # Default: no evidence of animal origin for a plain generic produce/pantry
    # term not covered above (fruit, vegetables, plain grains, sweeteners,
    # herbs/spices, condiments not listed as hidden-risk above).
    return [attr("ANIMAL_DERIVED", "false", VERIFIED_ABSENT,
                 "No animal-derived component identified in this generic ingredient name.")]


def merge_alternatives(name, parts):
    """Merge attribute lists from 'X or Y' alternatives. Attributes that agree
    keep that value; attributes present on only one side, or disagreeing,
    become CONDITIONAL so the actual household choice decides the outcome."""
    per_part = [{(a["attribute_code"]): a for a in classify_atomic(p)} for p in parts]
    codes = set()
    for p in per_part:
        codes |= set(p.keys())
    merged = []
    for code in sorted(codes):
        values = [p.get(code) for p in per_part]
        present = [v for v in values if v is not None]
        values_set = {v["attribute_value"] for v in present}
        if len(present) == len(parts) and len(values_set) == 1 and all(v["evidence_state"] in (VERIFIED_PRESENT, VERIFIED_ABSENT) for v in present):
            merged.append(present[0])
        else:
            alt_desc = "; ".join(f"'{p}' -> {pv['attribute_value'] if pv else 'not identified'}" for p, pv in zip(parts, values))
            merged.append(attr(code, "depends_on_choice", CONDITIONAL,
                                f"Swap-flexible ingredient line ('{name}'): {alt_desc}. Household's actual choice determines this attribute.",
                                source="derived from 'X or Y' alternatives in the recipe bank"))
    return merged


def classify(name):
    name = name.strip().lower()
    if " or " in name and name not in EXACT_RULES:
        parts = [p.strip() for p in name.split(" or ")]
        return merge_alternatives(name, parts), True
    return classify_atomic(name), False


def load_ingredient_names():
    text = DATA_JS.read_text()
    payload = text[text.index("=") + 1:].strip().rstrip(";")
    data = json.loads(payload)
    names = {}
    for r in data["recipes"]:
        for ing in r["ingredients"]:
            name = ing["ingredient"].strip().lower()
            info = names.setdefault(name, {"groups": set(), "swap_groups": set(), "units": set(), "line_count": 0})
            info["groups"].add(ing.get("group", ""))
            info["swap_groups"].add(ing.get("swapGroup", ""))
            info["units"].add(ing.get("unit", ""))
            info["line_count"] += 1
    return names


HIDDEN_ONION_GARLIC_NOTE = (
    "Commercial sauces, dressings and seasoning blends commonly include onion "
    "and/or garlic powder even when not named. Not confirmed for this specific "
    "ingredient text -- verify product for an onion/garlic-free requirement."
)


def add_generic_sauce_seasoning_onion_garlic_risk(name, info, attributes):
    """Sauces and herb/spice-blend ingredients are a well-known hidden source of
    onion/garlic even when not named (bottled sauces, seasoning mixes). Applied
    by category (recipe group / swap group), not per exact ingredient name, to
    avoid hand-enumerating dozens of sauce/seasoning entries individually --
    it only fires where an ingredient doesn't already carry an explicit
    ONION_CONTENT/GARLIC_CONTENT verdict from EXACT_RULES."""
    is_sauce_or_seasoning = "sauce" in info["groups"] or "Herbs/Spices" in info["swap_groups"]
    if not is_sauce_or_seasoning:
        return attributes
    codes_present = {a["attribute_code"] for a in attributes}
    extra = []
    if "ONION_CONTENT" not in codes_present:
        extra.append(attr("ONION_CONTENT", "unspecified", CONDITIONAL, HIDDEN_ONION_GARLIC_NOTE,
                           source="recipe group/swap group heuristic (sauce or Herbs/Spices), not a specific product check"))
    if "GARLIC_CONTENT" not in codes_present:
        extra.append(attr("GARLIC_CONTENT", "unspecified", CONDITIONAL, HIDDEN_ONION_GARLIC_NOTE,
                           source="recipe group/swap group heuristic (sauce or Herbs/Spices), not a specific product check"))
    return attributes + extra


def add_lactose_content(attributes):
    """LACTOSE_FREE and DAIRY_FREE are different requirements (lactose-free milk
    is still dairy -- it still carries the milk allergen -- it's just had the
    lactose sugar removed). Every ordinary dairy ingredient in this recipe bank
    is regular dairy, so LACTOSE_CONTENT mirrors DAIRY_MILK here; the
    distinction only matters once a specific lactose-reduced *substitute*
    enters the picture (Phase 2.5's substitution catalogue), which is exactly
    why this code needed to exist as its own attribute rather than being
    folded into DAIRY_MILK."""
    dairy_row = next((a for a in attributes if a["attribute_code"] == "DAIRY_MILK"), None)
    if dairy_row is None:
        return attributes
    return attributes + [attr("LACTOSE_CONTENT", dairy_row["attribute_value"], dairy_row["evidence_state"],
                               "Mirrors this ingredient's DAIRY_MILK assessment (ordinary dairy, not a lactose-reduced product).")]


def main():
    names = load_ingredient_names()
    records = []
    for name in sorted(names):
        info = names[name]
        attributes, is_compound = classify(name)
        attributes = add_generic_sauce_seasoning_onion_garlic_risk(name, info, attributes)
        attributes = add_lactose_content(attributes)
        records.append({
            "ingredient_key": name,
            "recipe_groups": sorted(info["groups"]),
            "swap_groups": sorted(info["swap_groups"]),
            "recipe_units": sorted(info["units"]),
            "ingredient_line_count": info["line_count"],
            "is_compound_alternative": is_compound,
            "attributes": attributes,
        })
    out = {
        "schema_version": "1.2",
        "change_log": [
            {"version": "1.1", "change": "Phase 2.4 addendum: added CAFFEINE_CONTENT (coffee, chocolate, "
                                          "choc chip, cocoa oat), ONION_CONTENT and GARLIC_CONTENT "
                                          "(onion, garlic seasoning, creamy garlic sauce, soy garlic sauce, "
                                          "pesto veg sauce exact matches, plus a generic CONDITIONAL flag for "
                                          "any sauce-group or Herbs/Spices-swap-group ingredient) -- needed to "
                                          "derive CAFFEINE_FREE/ONION_FREE/GARLIC_FREE per-recipe classification."},
            {"version": "1.2", "change": "Phase 2.5 addendum: added LACTOSE_CONTENT, mirroring DAIRY_MILK on "
                                          "every dairy ingredient in this table. Needed once the substitution "
                                          "catalogue introduced 'lactose-free milk' as a real substitute option: "
                                          "it is DAIRY_MILK=true (still carries the milk allergen) but "
                                          "LACTOSE_CONTENT=false, a distinction DAIRY_MILK alone cannot express."},
        ],
        "keying": "INTERIM: keyed by normalised ingredient_key (lowercased ingredient text), "
                  "not canonical ingredient_id. Re-key onto ingredients.ingredient_id "
                  "(schema/001_initial_schema.sql) when Phase 4 assigns canonical IDs.",
        "attribute_dictionary": "See INGREDIENT_ATTRIBUTE_CODES.md for attribute_code definitions and evidence_state semantics.",
        "ingredient_count": len(records),
        "ingredients": records,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2))
    total_attrs = sum(len(r["attributes"]) for r in records)
    conditional = sum(1 for r in records for a in r["attributes"] if a["evidence_state"] == CONDITIONAL)
    unverified = sum(1 for r in records for a in r["attributes"] if a["evidence_state"] == UNVERIFIED)
    print(f"{len(records)} ingredients, {total_attrs} attribute records "
          f"({conditional} CONDITIONAL, {unverified} UNVERIFIED).")


if __name__ == "__main__":
    main()
