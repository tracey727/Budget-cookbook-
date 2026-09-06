#!/usr/bin/env python3
"""Phase 2 recipe/content QA analysis for the GENEVIEVE Family Budget Cookbook V1 baseline.

Reads the sealed 800-recipe catalogue from 03_WORKING_PROTOTYPE/data.js and runs the
automatable checks from 01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md
Phase 2 (items 1-4 and 7). Writes PHASE2_QA_REPORT.md (human-readable findings) and
phase2_qa_flags.json (machine-readable per-recipe flags) into this folder.

Does NOT and CANNOT satisfy items 5-6 (freezing disclaimer language, shipping it in
the UX) or perform the culinary/kitchen-testing judgement the gate ultimately requires
-- those need a human reviewer. This script only narrows down what needs that review.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "03_WORKING_PROTOTYPE" / "data.js"

HIGH_RISK_SWAP_GROUPS = {"Egg", "Raising Agent", "Herbs/Spices", "Cooking Fat"}
CAN_PACK_KEYWORDS = ("canned", "tin", "packet", "jar", "tub", "block", "bottle")

# Per-serve upper bounds (baseQty / baseServes) before a quantity is flagged as an
# unusual scaling risk. Thresholds are deliberately loose -- this is a screen for
# human review, not an automatic verdict.
PER_SERVE_LIMITS = {
    "Raising Agent": {"tsp": 1.5, "tbsp": 0.5},
    "Herbs/Spices": {"tsp": 2.0, "tbsp": 1.0},
    "Cooking Fat": {"tbsp": 2.0, "cup": 0.25},
    "Egg": {"each": 2.0, "large": 2.0},
}

COOK_VERB_MIN_COOKMIN = {
    "bake": 10, "roast": 15, "simmer": 5, "fry": 3, "grill": 5,
    "boil": 3, "saute": 3, "sauté": 3, "braise": 20, "poach": 3,
}


def load_recipes():
    text = DATA_JS.read_text()
    payload = text[text.index("=") + 1:].strip().rstrip(";")
    return json.loads(payload)["recipes"]


def check_duplicate_names(recipes):
    by_name = defaultdict(list)
    for r in recipes:
        by_name[r["name"].strip().lower()].append(r["id"])
    exact_dupes = {name: ids for name, ids in by_name.items() if len(ids) > 1}

    by_family = defaultdict(list)
    for r in recipes:
        by_family[(r["mealType"], r["family"].strip().lower())].append(r)
    dense_families = {
        fam: [r["id"] for r in items]
        for fam, items in by_family.items()
        if len(items) > 12
    }
    return exact_dupes, dense_families


def check_method_timing(recipes):
    flags = []
    for r in recipes:
        method_lower = r["method"].lower()
        cook_min = r["cookMin"]
        for verb, min_expected in COOK_VERB_MIN_COOKMIN.items():
            if verb in method_lower and cook_min < min_expected:
                flags.append({
                    "id": r["id"], "name": r["name"], "mealType": r["mealType"],
                    "issue": f"method mentions '{verb}' but cookMin={cook_min} "
                             f"(< {min_expected})",
                })
        if r["prepMin"] == 0 and r["cookMin"] == 0:
            flags.append({
                "id": r["id"], "name": r["name"], "mealType": r["mealType"],
                "issue": "prepMin and cookMin are both 0",
            })
    return flags


def check_quantity_realism(recipes):
    flags = []
    for r in recipes:
        base_serves = r["baseServes"]
        for ing in r["ingredients"]:
            if ing.get("optional"):
                continue
            swap_group = ing.get("swapGroup", "")
            limits = PER_SERVE_LIMITS.get(swap_group)
            if not limits:
                continue
            unit = ing.get("unit", "")
            limit = limits.get(unit)
            if limit is None:
                continue
            per_serve = ing["baseQty"] / base_serves
            if per_serve > limit:
                flags.append({
                    "id": r["id"], "name": r["name"],
                    "ingredient": ing["ingredient"],
                    "issue": f"{per_serve:.2f} {unit}/serve of a {swap_group} "
                             f"ingredient exceeds screening limit {limit} {unit}/serve",
                })
    return flags


def check_high_risk_scaling(recipes):
    """Flag every recipe touching a swap group or keyword the blueprint calls out
    as needing a special (non-linear) scaling rule rather than blind multiplication."""
    flags = {}
    for r in recipes:
        reasons = set()
        for ing in r["ingredients"]:
            swap_group = ing.get("swapGroup", "")
            if swap_group in HIGH_RISK_SWAP_GROUPS:
                reasons.add(swap_group)
            name_lower = ing["ingredient"].lower()
            if any(k in name_lower for k in CAN_PACK_KEYWORDS):
                reasons.add("Cans/packs")
        if reasons:
            flags[r["id"]] = {"name": r["name"], "reasons": sorted(reasons)}
    return flags


def build_report(recipes):
    exact_dupes, dense_families = check_duplicate_names(recipes)
    timing_flags = check_method_timing(recipes)
    quantity_flags = check_quantity_realism(recipes)
    high_risk = check_high_risk_scaling(recipes)

    kitchen_test_ids = sorted(
        set(high_risk)
        | {f["id"] for f in timing_flags}
        | {f["id"] for f in quantity_flags}
    )

    lines = []
    lines.append("# Phase 2 Recipe/Content QA Report — V1 800-recipe baseline")
    lines.append("")
    lines.append(
        "Automated screen only. Produces the review queue this gate needs; it does "
        "not replace culinary/kitchen-tested sign-off. See `01_MASTER_BLUEPRINT/"
        "CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 2 for the full gate."
    )
    lines.append("")
    lines.append(f"Recipes scanned: **{len(recipes)}**")
    lines.append("")

    lines.append("## 1. Duplicate / near-duplicate names")
    lines.append("")
    if exact_dupes:
        lines.append(f"Exact duplicate names found: {len(exact_dupes)}")
        for name, ids in sorted(exact_dupes.items()):
            lines.append(f"- \"{name}\" — {', '.join(ids)}")
    else:
        lines.append("No exact duplicate recipe names found.")
    lines.append("")
    lines.append(
        f"Families with more than 12 recipes (review for repetitive/near-duplicate "
        f"variants within the family): {len(dense_families)}"
    )
    for (meal_type, family), ids in sorted(dense_families.items(), key=lambda x: -len(x[1])):
        lines.append(f"- {meal_type} / \"{family}\" — {len(ids)} recipes")
    lines.append("")
    lines.append(
        "Spot-check (`build_recipe_bank.py` generates these families by combining a "
        "flavour/sauce variant with a protein, e.g. \"Tomato Herb Chicken Pasta\", "
        "\"Creamy Garlic Chicken Pasta\") confirms these are deliberate templated "
        "variants, not accidental duplicates. They still need a human read for "
        "whether every flavour × protein combination is actually a distinct, "
        "sensible dish (Phase 2 item 1) — the generator pattern alone doesn't prove "
        "that."
    )
    lines.append("")

    lines.append("## 2. Method / timing sanity")
    lines.append("")
    lines.append(f"Flags: {len(timing_flags)}")
    for f in timing_flags:
        lines.append(f"- `{f['id']}` {f['name']} ({f['mealType']}): {f['issue']}")
    lines.append("")

    lines.append("## 3. Quantity realism screen (per-serve, base-serves=4 baseline)")
    lines.append("")
    lines.append(f"Flags: {len(quantity_flags)}")
    for f in quantity_flags:
        lines.append(f"- `{f['id']}` {f['name']} — {f['ingredient']}: {f['issue']}")
    lines.append("")

    lines.append(
        "## 4. High-risk scaling categories "
        "(eggs, raising agents, strong spices, pan oil/fat, cans/packs)"
    )
    lines.append("")
    lines.append(
        f"{len(high_risk)} of {len(recipes)} recipes contain at least one ingredient "
        "in a category the blueprint says must not be scaled by blind multiplication "
        "(MASTER_PRODUCT_BLUEPRINT.md rule 7). These need an explicit non-linear "
        "scaling rule in Phase 8 (engine productionisation), not necessarily a content "
        "rewrite now."
    )
    lines.append("")
    reason_counts = defaultdict(int)
    for info in high_risk.values():
        for reason in info["reasons"]:
            reason_counts[reason] += 1
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {reason}: {count} recipes")
    lines.append("")

    lines.append("## 5. GF/DF adaptable vs allergen-safe language — FROZEN")
    lines.append("")
    lines.append(
        "See `DIETARY_CLAIM_LANGUAGE.md` in this folder for the frozen wording. "
        "Summary: `gfAdaptable`/`dfAdaptable: Yes` means the recipe **structure** "
        "can be made GF/DF by swapping the flagged ingredient(s); it is never an "
        "allergen-safety, cross-contamination or certified-free claim."
    )
    lines.append("")

    lines.append("## 6. Allergen/adaptation disclaimer in product UX")
    lines.append("")
    lines.append(
        "Added to the working prototype (`03_WORKING_PROTOTYPE/index.html`) as a "
        "persistent banner, and repeated on every recipe detail view next to the "
        "GF/DF badges."
    )
    lines.append("")

    lines.append("## 7. Recipes requiring real kitchen testing before public launch")
    lines.append("")
    lines.append(
        f"{len(kitchen_test_ids)} recipes are queued for human kitchen-testing / "
        "culinary review before launch, because they hit a high-risk scaling "
        "category, a method/timing flag, or a quantity-realism flag above. This "
        "list is a screening aid, not a completed review — an AI text pass cannot "
        "certify a recipe as kitchen-tested."
    )
    lines.append("")
    lines.append(
        "Full ID list is in `phase2_qa_flags.json` (`kitchen_test_queue`) to keep "
        "this report readable."
    )
    lines.append("")

    lines.append("## Gate status")
    lines.append("")
    lines.append(
        "**NOT GREEN.** The automatable parts of Phase 2 (duplicate screen, "
        "timing/quantity screen, high-risk scaling inventory, frozen dietary-claim "
        "language, UX disclaimer) are done. Items 3 and 7 of the phase — realistic-"
        "quantity judgement calls and kitchen-testing sign-off — need a human "
        "reviewer with the flagged queue above before this phase can be marked "
        "GREEN and Phase 3 (production repository) proceeds with launch-ready "
        "content."
    )
    lines.append("")

    report_md = "\n".join(lines)

    flags_json = {
        "recipes_scanned": len(recipes),
        "exact_duplicate_names": exact_dupes,
        "dense_families": {f"{k[0]} / {k[1]}": v for k, v in dense_families.items()},
        "method_timing_flags": timing_flags,
        "quantity_realism_flags": quantity_flags,
        "high_risk_scaling": high_risk,
        "kitchen_test_queue": kitchen_test_ids,
    }
    return report_md, flags_json


def main():
    recipes = load_recipes()
    report_md, flags_json = build_report(recipes)
    (ROOT / "02_RECIPE_CONTENT" / "PHASE2_QA_REPORT.md").write_text(report_md)
    (ROOT / "02_RECIPE_CONTENT" / "phase2_qa_flags.json").write_text(
        json.dumps(flags_json, indent=2)
    )
    print(f"Scanned {len(recipes)} recipes.")
    print(f"Kitchen-test queue: {len(flags_json['kitchen_test_queue'])} recipes.")


if __name__ == "__main__":
    main()
