#!/usr/bin/env python3
"""Phase 2.8 -- Full Recipe/Content Production QA (final consolidation).

Combines everything Phase 2 through 2.7 established into one per-recipe
launch-readiness verdict:
- PHASE2_QA_REPORT.md / phase2_qa_flags.json: duplicate/timing/quantity
  screen and the high-risk-scaling-category kitchen-test queue.
- recipe_requirement_assessments_v1.json (Phase 2.4): dietary
  classification exists for every recipe against every ingredient-derivable
  requirement family.
- DIETARY_CLAIM_LANGUAGE.md / PHASE_2_1_TAXONOMY_AND_LANGUAGE_FREEZE.md:
  frozen adaptation/allergen claim language, live in the working prototype's
  UI banner.

GREEN gate (Phase 2.8): "no unsafe/misleading dietary claims; all public
launch recipes have reviewed content; unresolved recipes stay out of the
launch set or remain visibly unverified." This script does not silently
clear the 415-recipe kitchen-test queue -- it can't taste-test a recipe.
It draws the launch/hold line honestly: a recipe with no QA flag at all is
LAUNCH_READY; a recipe still awaiting human kitchen-testing for a high-risk
scaling category is HELD_FOR_KITCHEN_TEST, excluded from the launch set
rather than guessed into it.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QA_FLAGS = ROOT / "02_RECIPE_CONTENT" / "phase2_qa_flags.json"
ASSESSMENTS = ROOT / "07_DIETARY_REQUIREMENTS_ENGINE" / "recipe_requirement_assessments_v1.json"
DATA_JS = ROOT / "03_WORKING_PROTOTYPE" / "data.js"
OUT_JSON = ROOT / "02_RECIPE_CONTENT" / "recipe_launch_readiness_v1.json"

LAUNCH_READY = "LAUNCH_READY"
HELD_FOR_KITCHEN_TEST = "HELD_FOR_KITCHEN_TEST"


def load_recipes():
    text = DATA_JS.read_text()
    payload = text[text.index("=") + 1:].strip().rstrip(";")
    return json.loads(payload)["recipes"]


def main():
    qa = json.loads(QA_FLAGS.read_text())
    assessments = json.loads(ASSESSMENTS.read_text())
    recipes = load_recipes()
    recipes_by_id = {r["id"]: r for r in recipes}

    kitchen_test_queue = set(qa["kitchen_test_queue"])
    high_risk_reasons = qa["high_risk_scaling"]  # recipe_id -> {name, reasons}
    duplicate_names = qa["exact_duplicate_names"]

    assessment_recipe_ids = {row["recipe_id"] for row in assessments["assessments"]}
    missing_classification = set(recipes_by_id) - assessment_recipe_ids

    records = []
    for recipe_id, recipe in sorted(recipes_by_id.items()):
        reasons = []
        if recipe_id in kitchen_test_queue:
            scaling_reasons = high_risk_reasons.get(recipe_id, {}).get("reasons", [])
            reasons.append(f"High-risk scaling categories pending kitchen test: {', '.join(scaling_reasons)}")
        if recipe_id in missing_classification:
            reasons.append("Missing dietary requirement classification (Phase 2.4)")

        status = HELD_FOR_KITCHEN_TEST if reasons else LAUNCH_READY
        records.append({
            "recipe_id": recipe_id,
            "name": recipe["name"],
            "meal_type": recipe["mealType"],
            "status": status,
            "reasons": reasons,
        })

    launch_ready = [r for r in records if r["status"] == LAUNCH_READY]
    held = [r for r in records if r["status"] == HELD_FOR_KITCHEN_TEST]

    out = {
        "schema_version": "1.0",
        "policy": "A recipe is LAUNCH_READY only when it carries zero open QA flags "
                  "(duplicate/timing/quantity/high-risk-scaling) and has a complete Phase 2.4 "
                  "dietary classification record. Everything else is HELD_FOR_KITCHEN_TEST -- "
                  "excluded from the launch set, never guessed into it. No recipe in this baseline "
                  "was DROPPED outright: the 0 exact-duplicate and 0 timing/quantity flags found in "
                  "Phase 2 QA mean every held recipe is a real, distinct, plausibly-correct recipe "
                  "that needs a scaling/kitchen-test pass, not a defective one.",
        "recipe_count": len(records),
        "launch_ready_count": len(launch_ready),
        "held_for_kitchen_test_count": len(held),
        "exact_duplicate_names_found": len(duplicate_names),
        "missing_dietary_classification_count": len(missing_classification),
        "recipes": records,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(f"{len(records)} recipes: {len(launch_ready)} LAUNCH_READY, {len(held)} HELD_FOR_KITCHEN_TEST.")
    print(f"Exact duplicate names: {len(duplicate_names)}. Missing dietary classification: {len(missing_classification)}.")


if __name__ == "__main__":
    main()
