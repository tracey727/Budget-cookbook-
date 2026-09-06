#!/usr/bin/env python3
"""Phase 2.4 -- Recipe Classification of all 800 Recipes.

Audits every recipe in the V1 baseline against every "applicable" requirement
family from DIETARY_TAXONOMY.json v1.1, using the Phase 2.2 ingredient
attribute table (ingredient_dietary_attributes_v1.json) -- never inferring a
high-consequence claim from a recipe's name or category alone, per this
phase's own gate text.

Produces recipe_requirement_assessments_v1.json, one row per
(recipe_id, requirement_code) for the requirement codes this phase can
actually derive from ingredient evidence (see PHASE_2_4_RECIPE_CLASSIFICATION_REPORT.md
"Scope" section for the full accounting of every taxonomy code as either
"classified here" or "blanket UNVERIFIED, out of scope for this phase" --
the latter are NOT expanded into 800 redundant identical rows; they're listed
once in this file's `blanket_unverified_requirement_codes`).

Launch Rule (DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md): "No dietary flag
becomes a public MEETS claim ... until the Phase 2 dietary QA gate has
reviewed the relevant ingredient/recipe mapping. Unreviewed recipes remain
UNVERIFIED for that requirement." This script's output is a *candidate*
classification -- every row is written with reviewed=false, review_source
naming this automated pass. `public_suitability_state()` implements the
gating the rule requires: a computed MEETS is not shown publicly until a
human reviewer flips `reviewed=true`; a computed EXCLUDED is never hidden
behind that gate (surfacing a real exclusion is never the "optimistic" claim
the rule is guarding against).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "03_WORKING_PROTOTYPE" / "data.js"
ATTR_JSON = ROOT / "07_DIETARY_REQUIREMENTS_ENGINE" / "ingredient_dietary_attributes_v1.json"
OUT_JSON = ROOT / "07_DIETARY_REQUIREMENTS_ENGINE" / "recipe_requirement_assessments_v1.json"

MEETS, ADAPTABLE, EXCLUDED, UNVERIFIED = "MEETS", "ADAPTABLE", "EXCLUDED", "UNVERIFIED"
VERIFIED_PRESENT, VERIFIED_ABSENT = "VERIFIED_PRESENT", "VERIFIED_ABSENT"
CONDITIONAL, UNVERIFIED_EV = "CONDITIONAL", "UNVERIFIED"

REVIEW_SOURCE = "automated_ingredient_attribute_audit_v1 (Phase 2.4, unreviewed)"

# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

def load_recipes():
    text = DATA_JS.read_text()
    payload = text[text.index("=") + 1:].strip().rstrip(";")
    return json.loads(payload)["recipes"]


def load_attribute_lookup():
    data = json.loads(ATTR_JSON.read_text())
    return {r["ingredient_key"]: r["attributes"] for r in data["ingredients"]}


# --------------------------------------------------------------------------
# Shared evidence-aggregation primitives
# --------------------------------------------------------------------------

def code_presence(attr_lookup, keys, codes):
    """Across a recipe's ingredient keys, does any attribute row for `codes`
    indicate presence, and how confidently? Returns ('definite'|'maybe'|'none', contributing)."""
    definite_hit = False
    maybe_hit = False
    contributing = []
    for key in keys:
        for row in attr_lookup.get(key, []):
            if row["attribute_code"] in codes and row["attribute_value"] != "false":
                contributing.append((key, row))
                if row["evidence_state"] == VERIFIED_PRESENT:
                    definite_hit = True
                elif row["evidence_state"] in (CONDITIONAL, UNVERIFIED_EV):
                    maybe_hit = True
    if definite_hit:
        return "definite", contributing
    if maybe_hit:
        return "maybe", contributing
    return "none", contributing


def names_from(contributing):
    return sorted({key for key, _ in contributing})


def direct_code_requirement(codes, subject_label):
    """Factory for the common case: violates the requirement iff any of `codes`
    is present (VERIFIED_PRESENT -> EXCLUDED, CONDITIONAL/UNVERIFIED -> UNVERIFIED,
    absent everywhere -> MEETS)."""
    def evaluator(attr_lookup, keys):
        presence, contributing = code_presence(attr_lookup, keys, codes)
        names = names_from(contributing)
        if presence == "definite":
            return EXCLUDED, f"Contains {subject_label} ({', '.join(names)})."
        if presence == "maybe":
            return UNVERIFIED, (
                f"May contain {subject_label} depending on an unspecified ingredient/product "
                f"choice or hidden-source risk ({', '.join(names)}); verify before relying on this."
            )
        return MEETS, f"No {subject_label}-containing ingredient identified in this recipe."
    return evaluator


def ingredient_flesh_state(attrs, allow_fish):
    """Is a single ingredient's own attribute set flesh-derived (for vegetarian/
    pescatarian purposes)? Returns 'definite' | 'maybe' | None."""
    flesh_codes = {"MEAT_BEEF", "MEAT_PORK", "POULTRY"}
    non_flesh_animal_codes = {"DAIRY_MILK", "EGG", "HONEY_BEE_DERIVED"}
    if not allow_fish:
        flesh_codes |= {"FISH", "SHELLFISH_CRUSTACEAN", "SHELLFISH_MOLLUSC"}
    else:
        non_flesh_animal_codes |= {"FISH", "SHELLFISH_CRUSTACEAN", "SHELLFISH_MOLLUSC"}
    by_code = {a["attribute_code"]: a for a in attrs}

    for code in flesh_codes:
        row = by_code.get(code)
        if row and row["attribute_value"] != "false":
            if row["evidence_state"] == VERIFIED_PRESENT:
                return "definite"
    for code in flesh_codes:
        row = by_code.get(code)
        if row and row["attribute_value"] != "false" and row["evidence_state"] in (CONDITIONAL, UNVERIFIED_EV):
            return "maybe"

    animal = by_code.get("ANIMAL_DERIVED")
    if animal and animal["attribute_value"] != "false":
        has_non_flesh = any(
            (by_code.get(c) or {}).get("attribute_value") not in (None, "false") for c in non_flesh_animal_codes
        )
        if not has_non_flesh:
            if animal["evidence_state"] == VERIFIED_PRESENT:
                return "definite"
            if animal["evidence_state"] in (CONDITIONAL, UNVERIFIED_EV):
                return "maybe"
    return None


def lifestyle_evaluator(allow_fish, label):
    def evaluator(attr_lookup, keys):
        definite_names, maybe_names = [], []
        for key in keys:
            result = ingredient_flesh_state(attr_lookup.get(key, []), allow_fish)
            if result == "definite":
                definite_names.append(key)
            elif result == "maybe":
                maybe_names.append(key)
        if definite_names:
            return EXCLUDED, f"Contains {label}-excluded animal ingredient(s): {', '.join(sorted(set(definite_names)))}."
        if maybe_names:
            return UNVERIFIED, (
                f"May contain a {label}-excluded animal ingredient depending on an unspecified "
                f"product/meat-type choice: {', '.join(sorted(set(maybe_names)))}."
            )
        return MEETS, f"No animal ingredient identified that would exclude this recipe from {label}."
    return evaluator


def vegan_evaluator(attr_lookup, keys):
    presence, contributing = code_presence(attr_lookup, keys, {"ANIMAL_DERIVED"})
    names = names_from(contributing)
    if presence == "definite":
        return EXCLUDED, f"Contains animal-derived ingredient(s): {', '.join(names)}."
    if presence == "maybe":
        return UNVERIFIED, f"May contain an animal-derived ingredient depending on an unspecified choice: {', '.join(names)}."
    return MEETS, "No animal-derived ingredient identified in this recipe."


def coeliac_style_evaluator(label):
    def evaluator(attr_lookup, keys):
        wheat, _ = code_presence(attr_lookup, keys, {"GLUTEN_CEREAL_WHEAT"})
        barley, _ = code_presence(attr_lookup, keys, {"GLUTEN_CEREAL_BARLEY"})
        rye, _ = code_presence(attr_lookup, keys, {"GLUTEN_CEREAL_RYE"})
        oats, oats_c = code_presence(attr_lookup, keys, {"GLUTEN_CEREAL_OATS"})
        if "definite" in (wheat, barley, rye):
            which = [n for n, s in (("wheat", wheat), ("barley", barley), ("rye", rye)) if s == "definite"]
            return EXCLUDED, f"Contains a gluten-containing cereal ({', '.join(which)})."
        if "maybe" in (wheat, barley, rye):
            return UNVERIFIED, "Wheat/barley/rye content is not fully confirmed from the ingredient text; verify before relying on this."
        if oats != "none":
            names = names_from(oats_c)
            return UNVERIFIED, (
                f"Contains oats ({', '.join(names)}). Per the Australian gluten-free claim boundary "
                f"(07_DIETARY_REQUIREMENTS_ENGINE/REFERENCE_SOURCES.md), oats require a verified "
                f"gluten-free-certified source before a {label} claim -- not assumed safe."
            )
        return MEETS, "No wheat, barley, rye or oats identified in this recipe's ingredients."
    return evaluator


def oat_exclude_evaluator(attr_lookup, keys):
    presence, contributing = code_presence(attr_lookup, keys, {"GLUTEN_CEREAL_OATS"})
    names = names_from(contributing)
    if presence == "definite":
        return EXCLUDED, f"Contains oats ({', '.join(names)})."
    if presence == "maybe":
        return UNVERIFIED, f"May contain oats depending on an unspecified ingredient choice: {', '.join(names)}."
    return MEETS, "No oats identified in this recipe."


def pork_free_evaluator(attr_lookup, keys):
    return direct_code_requirement({"MEAT_PORK"}, "pork")(attr_lookup, keys)


def halal_evaluator(attr_lookup, keys):
    pork, _ = code_presence(attr_lookup, keys, {"MEAT_PORK"})
    other_meat, _ = code_presence(attr_lookup, keys, {"MEAT_BEEF", "POULTRY", "FISH"})
    alcohol, _ = code_presence(attr_lookup, keys, {"ALCOHOL_CONTENT"})
    if pork == "definite":
        return EXCLUDED, "Contains pork, which is not halal."
    if pork == "maybe":
        return UNVERIFIED, "May contain pork depending on an unspecified ingredient/product choice."
    if alcohol == "definite":
        return EXCLUDED, "Contains alcohol, which is not halal."
    if other_meat != "none" or alcohol == "maybe":
        return UNVERIFIED, (
            "Contains meat/poultry/fish and/or an alcohol-adjacent ingredient; halal slaughter-method "
            "or alcohol-content verification is not available from generic ingredient text."
        )
    return MEETS, (
        "No pork, alcohol-adjacent ingredient, or other meat/poultry/fish requiring slaughter-method "
        "verification identified. Compatible as reviewed -- not a halal certification."
    )


def kosher_evaluator(attr_lookup, keys):
    pork, _ = code_presence(attr_lookup, keys, {"MEAT_PORK"})
    shellfish, _ = code_presence(attr_lookup, keys, {"SHELLFISH_CRUSTACEAN", "SHELLFISH_MOLLUSC"})
    meat, _ = code_presence(attr_lookup, keys, {"MEAT_BEEF", "POULTRY"})
    fish, _ = code_presence(attr_lookup, keys, {"FISH"})
    dairy, _ = code_presence(attr_lookup, keys, {"DAIRY_MILK"})
    if pork == "definite" or shellfish == "definite":
        return EXCLUDED, "Contains pork and/or shellfish, which are not kosher."
    if pork == "maybe" or shellfish == "maybe":
        return UNVERIFIED, "May contain pork or shellfish depending on an unspecified ingredient/product choice."
    if meat != "none" and dairy != "none":
        state = EXCLUDED if meat == "definite" and dairy == "definite" else UNVERIFIED
        return state, "Combines a meat/poultry ingredient with a dairy ingredient in the same dish, which kosher rules do not permit together."
    if meat != "none" or fish != "none":
        return UNVERIFIED, "Contains meat/poultry and/or fish; kosher slaughter-method/species certification cannot be confirmed from generic ingredient text."
    return MEETS, "No pork, shellfish, or meat-and-dairy combination identified. Compatible as reviewed -- not a kosher certification."


# --------------------------------------------------------------------------
# Requirement registry -- every code here gets a real per-recipe row.
# --------------------------------------------------------------------------

ALLERGEN_CODE_MAP = [
    ("ALLERGY_WHEAT", "ALLERGEN_WHEAT", "wheat"),
    ("ALLERGY_FISH", "ALLERGEN_FISH", "fish"),
    ("ALLERGY_CRUSTACEAN", "ALLERGEN_CRUSTACEAN", "crustacean shellfish"),
    ("ALLERGY_MOLLUSC", "ALLERGEN_MOLLUSC", "molluscan shellfish"),
    ("ALLERGY_EGG", "ALLERGEN_EGG", "egg"),
    ("ALLERGY_MILK", "ALLERGEN_MILK", "milk"),
    ("ALLERGY_LUPIN", "ALLERGEN_LUPIN", "lupin"),
    ("ALLERGY_PEANUT", "ALLERGEN_PEANUT", "peanut"),
    ("ALLERGY_SOY", "ALLERGEN_SOY", "soy"),
    ("ALLERGY_SESAME", "ALLERGEN_SESAME", "sesame"),
    ("ALLERGY_ALMOND", "ALLERGEN_ALMOND", "almond"),
    ("ALLERGY_BRAZIL_NUT", "ALLERGEN_BRAZIL_NUT", "Brazil nut"),
    ("ALLERGY_CASHEW", "ALLERGEN_CASHEW", "cashew"),
    ("ALLERGY_HAZELNUT", "ALLERGEN_HAZELNUT", "hazelnut"),
    ("ALLERGY_MACADAMIA", "ALLERGEN_MACADAMIA", "macadamia"),
    ("ALLERGY_PECAN", "ALLERGEN_PECAN", "pecan"),
    ("ALLERGY_PISTACHIO", "ALLERGEN_PISTACHIO", "pistachio"),
    ("ALLERGY_PINE_NUT", "ALLERGEN_PINE_NUT", "pine nut"),
    ("ALLERGY_WALNUT", "ALLERGEN_WALNUT", "walnut"),
    ("ALLERGY_BARLEY", "ALLERGEN_BARLEY", "barley"),
    ("ALLERGY_OATS", "ALLERGEN_OATS", "oats"),
    ("ALLERGY_RYE", "ALLERGEN_RYE", "rye"),
    ("SULPHITES_CONTROL", "ALLERGEN_SULPHITES", "sulphites"),
]

REQUIREMENT_EVALUATORS = {
    "VEGETARIAN": lifestyle_evaluator(allow_fish=False, label="vegetarian"),
    "PESCATARIAN": lifestyle_evaluator(allow_fish=True, label="pescatarian"),
    "VEGAN": vegan_evaluator,
    "COELIAC_STRICT_GF": coeliac_style_evaluator("coeliac-strict gluten-free"),
    "GLUTEN_FREE_PREFERENCE": coeliac_style_evaluator("gluten-free-preference"),
    "WHEAT_FREE": direct_code_requirement({"GLUTEN_CEREAL_WHEAT"}, "wheat"),
    "RYE_FREE": direct_code_requirement({"GLUTEN_CEREAL_RYE"}, "rye"),
    "BARLEY_FREE": direct_code_requirement({"GLUTEN_CEREAL_BARLEY"}, "barley"),
    "OAT_EXCLUDE": oat_exclude_evaluator,
    "LACTOSE_FREE": direct_code_requirement({"LACTOSE_CONTENT"}, "lactose"),
    "DAIRY_FREE": direct_code_requirement({"DAIRY_MILK"}, "dairy"),
    "ALCOHOL_FREE": direct_code_requirement({"ALCOHOL_CONTENT"}, "alcohol"),
    "CAFFEINE_FREE": direct_code_requirement({"CAFFEINE_CONTENT"}, "caffeine"),
    "ONION_FREE": direct_code_requirement({"ONION_CONTENT"}, "onion"),
    "GARLIC_FREE": direct_code_requirement({"GARLIC_CONTENT"}, "garlic"),
    "PORK_FREE": pork_free_evaluator,
    "BEEF_FREE": direct_code_requirement({"MEAT_BEEF"}, "beef"),
    "HALAL_COMPATIBLE": halal_evaluator,
    "KOSHER_COMPATIBLE": kosher_evaluator,
}
for req_code, attr_code, label in ALLERGEN_CODE_MAP:
    REQUIREMENT_EVALUATORS[req_code] = direct_code_requirement({attr_code}, label)

# --------------------------------------------------------------------------
# Blanket-UNVERIFIED codes: real taxonomy codes this phase cannot derive from
# ingredient attributes alone. Documented once (not expanded into 800 rows
# each) -- see PHASE_2_4_RECIPE_CLASSIFICATION_REPORT.md for the full
# per-code rationale grouped by class.
# --------------------------------------------------------------------------

BLANKET_UNVERIFIED = {
    "FLEXITARIAN_PREFERENCE": "Preference-level code with no binary ingredient-exclusion criterion; not a recipe fact.",
    "PLANT_FORWARD_PREFERENCE": "Preference-level code with no binary ingredient-exclusion criterion; not a recipe fact.",
    "PURE_OAT_CLINICIAN_PLAN": "Requires a clinician-verified specific certified pure-oat product; not derivable from generic ingredient text.",
    "LOW_FODMAP_PROFESSIONAL_PLAN": "Explicitly a structured, personalised/professional-plan mode per policy -- not a generic per-recipe ingredient audit.",
    "LOW_SPICE": "Heat/spice level is a quantity and preparation judgement, not a binary ingredient-presence fact; belongs to culinary QA, not this model.",
}
for code in ["SODIUM_TARGET", "CARBOHYDRATE_TARGET", "ENERGY_TARGET", "PROTEIN_TARGET", "POTASSIUM_LIMIT",
             "PHOSPHATE_LIMIT", "FLUID_PLAN", "FAT_TARGET", "FIBRE_TARGET", "PKU_PHENYLALANINE_PLAN"]:
    BLANKET_UNVERIFIED[code] = "Clinician/professional-plan-supplied numeric target; this recipe bank has no nutrition data to evaluate it against, and none may be invented."
for code in ["REGULAR_TEXTURE", "EASY_TO_CHEW", "SAUCE_GRAVY_REQUIRED", "MOISTURE_REQUIRED"] + [f"IDDSI_LEVEL_{i}" for i in range(8)]:
    BLANKET_UNVERIFIED[code] = "Texture/swallowing safety depends on actual preparation and serving conditions, not ingredient list alone -- this is Phase 2.7's gate, not Phase 2.4's."
for code in ["PREGNANCY_CONSCIOUS", "BREASTFEEDING_PREFERENCE", "CHILD_FRIENDLY", "TODDLER_AGE_CHECK", "OLDER_PERSON_PREFERENCE"]:
    BLANKET_UNVERIFIED[code] = "Life-stage safety claims need authoritative Australian guidance review before enabling (MASTER_PRODUCT_BLUEPRINT.md section H), not yet done."
for code in ["NO_MIXED_TEXTURES", "SAUCE_SEPARATE", "PLAIN_MILD", "CRUNCHY_PREFERENCE", "SOFT_PREFERENCE", "TEMPERATURE_PREFERENCE", "NO_VISIBLE_VEGETABLES"]:
    BLANKET_UNVERIFIED[code] = "Sensory preference, not a safety exclusion; no binary ingredient fact to classify against."
for code in ["PANTRY_ONLY", "FREEZER_FRIENDLY", "LUNCHBOX_FRIENDLY", "ONE_POT", "MICROWAVE_ONLY", "NO_OVEN", "LOW_PREP",
             "BATCH_COOK", "LEFTOVER_FIRST", "USE_SOON", "SCHOOL_NUT_AWARE_PACKING"]:
    BLANKET_UNVERIFIED[code] = "Practical/logistical filter, not a dietary-content classification; freezer/lunchbox/one-pot are already direct recipe fields in the V1 data, handled by the existing engine, not this table."

CUSTOM_CODES_NOTE = (
    "CUSTOM_EXCLUSION/CUSTOM_REQUIREMENT/CUSTOM_PREFERENCE are open-ended per-household labels "
    "(see custom_dietary_rules), not a fixed taxonomy code with one meaning -- there is no single "
    "'does recipe X meet CUSTOM_EXCLUSION' answer to precompute. They are resolved at query time "
    "against a specific rule's canonical_ingredient_id, which is engine-runtime logic, not a "
    "per-recipe classification row."
)


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def main():
    recipes = load_recipes()
    attr_lookup = load_attribute_lookup()

    rows = []
    state_counts = {MEETS: 0, EXCLUDED: 0, UNVERIFIED: 0}
    public_state_counts = {MEETS: 0, EXCLUDED: 0, UNVERIFIED: 0}

    for recipe in recipes:
        ingredient_keys = sorted({ing["ingredient"].strip().lower() for ing in recipe["ingredients"]})
        for requirement_code, evaluator in REQUIREMENT_EVALUATORS.items():
            state, explanation = evaluator(attr_lookup, ingredient_keys)
            reviewed = False
            public_state = state if state != MEETS or reviewed else UNVERIFIED
            # (reviewed is always False in this automated pass, so public_state
            #  downgrades every computed MEETS to UNVERIFIED per the Launch Rule;
            #  EXCLUDED and UNVERIFIED pass through unchanged. Written out in
            #  full rather than short-circuited so a future reviewed=true pass
            #  is a one-line change, not a rewrite of this logic.)
            rows.append({
                "recipe_id": recipe["id"],
                "requirement_code": requirement_code,
                "suitability_state": state,
                "public_suitability_state": public_state,
                "explanation": explanation,
                "reviewed": reviewed,
                "reviewed_at": None,
                "review_source": REVIEW_SOURCE,
            })
            state_counts[state] += 1
            public_state_counts[public_state] += 1

    out = {
        "schema_version": "1.0",
        "keying": "recipe_id matches 03_WORKING_PROTOTYPE/data.js recipe ids (stable GEN-RCP-#### ids, "
                  "already reconciled to schema/001_initial_schema.sql's recipes.recipe_id). requirement_code "
                  "matches 07_DIETARY_REQUIREMENTS_ENGINE/DIETARY_TAXONOMY.json v1.1.",
        "launch_rule": "Per DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md: no computed MEETS is a public claim until "
                       "reviewed=true. public_suitability_state applies that gate; suitability_state is the "
                       "raw computed candidate for reviewer use.",
        "classified_requirement_codes": sorted(REQUIREMENT_EVALUATORS),
        "blanket_unverified_requirement_codes": BLANKET_UNVERIFIED,
        "custom_codes_not_applicable": {
            "codes": ["CUSTOM_EXCLUSION", "CUSTOM_REQUIREMENT", "CUSTOM_PREFERENCE"],
            "note": CUSTOM_CODES_NOTE,
        },
        "recipe_count": len(recipes),
        "requirement_code_count": len(REQUIREMENT_EVALUATORS),
        "row_count": len(rows),
        "state_counts": state_counts,
        "public_state_counts": public_state_counts,
        "assessments": rows,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(f"{len(recipes)} recipes x {len(REQUIREMENT_EVALUATORS)} requirement codes = {len(rows)} rows.")
    print("computed suitability_state counts:", state_counts)
    print("public_suitability_state counts (post Launch Rule gate):", public_state_counts)


if __name__ == "__main__":
    main()
