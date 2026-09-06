#!/usr/bin/env python3
"""Generate the Phase 5 Neon seed SQL from the frozen pack data files.

The generated SQL is deliberately dictionary-encoded: repeated text (method
steps, explanations, ingredient names) is emitted once into a staging
dictionary table and referenced by integer, then joined back in a single
INSERT ... SELECT. Foreign keys to ingredients are resolved in SQL by
canonical_name rather than by embedding UUIDs.

Usage:  python3 build_seed_sql.py [output_dir]
"""

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "04_PRODUCTION_STARTER", "seed_out")

# Keep each generated file small enough to move through a single tool call.
CHUNK_BYTES = 20000


def q(value):
    """SQL literal for a text/None value."""
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def load(*parts):
    with open(os.path.join(REPO, *parts)) as fh:
        return json.load(fh)


def write(name, sql):
    path = os.path.join(OUT, name)
    with open(path, "w") as fh:
        fh.write(sql if sql.endswith("\n") else sql + "\n")
    return path


def write_chunked(prefix, header, tuples, footer=""):
    """Emit `header VALUES <tuples>;` split across files under CHUNK_BYTES."""
    files, batch, size, idx = [], [], 0, 0
    for tup in tuples:
        if batch and size + len(tup) > CHUNK_BYTES:
            files.append(write(f"{prefix}_{idx:02d}.sql", header + ",".join(batch) + footer + ";"))
            batch, size, idx = [], 0, idx + 1
        batch.append(tup)
        size += len(tup) + 1
    if batch:
        files.append(write(f"{prefix}_{idx:02d}.sql", header + ",".join(batch) + footer + ";"))
    return files


class Dict1:
    """Assigns a stable integer to each distinct value, preserving first-seen order."""

    def __init__(self):
        self.index = {}
        self.values = []

    def __call__(self, value):
        if value is None:
            return None
        if value not in self.index:
            self.index[value] = len(self.values)
            self.values.append(value)
        return self.index[value]

    def rows(self, kind):
        return [f"({q(kind)},{i},{q(v)})" for i, v in enumerate(self.values)]


def canonical_keys():
    """The frozen canonical ingredient keys -- these are the ingredients.canonical_name values."""
    canonical = load("08_CANONICAL_INGREDIENT_MODEL", "canonical_ingredients_v1.json")
    return {c["ingredient_key"] for c in canonical["ingredients"]}


def blank_to_none(value):
    value = (value or "").strip()
    return value or None


def yes(value):
    return "true" if value == "Yes" else "false"


# --------------------------------------------------------------------------
# recipes
# --------------------------------------------------------------------------
def load_launch_readiness():
    """The Phase 2.8 launch/hold verdict, keyed by recipe_id -- the
    authoritative source for `recipes.public_launch_approved`. See
    02_RECIPE_CONTENT/PHASE_2_8_LAUNCH_READINESS_REPORT.md: LAUNCH_READY
    recipes have zero open QA flags and a complete dietary classification;
    HELD_FOR_KITCHEN_TEST recipes are real, distinct recipes that still need
    a human scaling/kitchen-test pass and must stay out of the launch set
    (CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md Phase 2.8 GREEN gate) until then.
    This is a different gate to dietary-claim review ("the Launch Rule" for
    MEETS claims in recipe_requirement_assessments) -- a recipe can be
    launch-approved for display while every one of its dietary assessments
    is still UNVERIFIED pending human sign-off.
    """
    readiness = load("02_RECIPE_CONTENT", "recipe_launch_readiness_v1.json")
    by_id = {r["recipe_id"]: r["status"] for r in readiness["recipes"]}
    assert len(by_id) == len(readiness["recipes"]), "duplicate recipe_id in launch readiness file"
    for status in by_id.values():
        assert status in ("LAUNCH_READY", "HELD_FOR_KITCHEN_TEST"), f"unknown launch status {status}"
    approved_count = sum(1 for s in by_id.values() if s == "LAUNCH_READY")
    assert approved_count == readiness["launch_ready_count"], (
        f"LAUNCH_READY count {approved_count} does not match "
        f"recorded launch_ready_count {readiness['launch_ready_count']}"
    )
    return by_id


def build_recipes(manifest):
    catalog = load("04_PRODUCTION_STARTER", "data", "recipe_catalog_v1.json")
    recipes = catalog["recipes"]
    launch_status = load_launch_readiness()

    for i, r in enumerate(recipes, start=1):
        assert r["id"] == f"GEN-RCP-{i:04d}", f"recipe ids are not sequential at {r['id']}"
    assert {r["budgetTier"] for r in recipes} == {"$"}, "budget_tier is no longer constant"
    assert set(launch_status) == {r["id"] for r in recipes}, (
        "recipe_launch_readiness_v1.json ids do not match recipe_catalog_v1.json ids exactly"
    )

    d_meal, d_fam, d_prot, d_carb, d_focus, d_meth, d_swap = (Dict1() for _ in range(7))
    numbers, bools = Dict1(), Dict1()

    rows = []
    approved_rows = 0
    for r in recipes:
        num = numbers(f"{r['baseServes']}|{r['prepMin']}|{r['cookMin']}")
        launch_approved = launch_status[r["id"]] == "LAUNCH_READY"
        if launch_approved:
            approved_rows += 1
        flags = bools("|".join(
            [yes(r[k]) for k in ("freezer", "lunchbox", "vegetarian", "gfAdaptable", "dfAdaptable", "onePot")]
            + ["true" if launch_approved else "false"]
        ))
        parts = [
            str(int(r["id"].split("-")[-1])),
            q(r["name"]),
            str(d_meal(r["mealType"])),
            str(d_fam(r["family"])),
            "NULL" if blank_to_none(r["protein"]) is None else str(d_prot(blank_to_none(r["protein"]))),
            "NULL" if blank_to_none(r["carb"]) is None else str(d_carb(blank_to_none(r["carb"]))),
            "NULL" if blank_to_none(r["focus"]) is None else str(d_focus(blank_to_none(r["focus"]))),
            str(d_meth(r["method"])),
            str(d_swap(r["swapNotes"])),
            str(num),
            str(flags),
        ]
        rows.append("(" + ",".join(parts) + ")")

    write("10_recipes_ddl.sql", """
CREATE TABLE IF NOT EXISTS _seed_dict (kind text NOT NULL, i int NOT NULL, v text NOT NULL, PRIMARY KEY (kind, i));
CREATE TABLE IF NOT EXISTS _seed_recipe (
  n int PRIMARY KEY, nm text NOT NULL, meal int NOT NULL, fam int NOT NULL,
  prot int, carb int, focus int, meth int NOT NULL, swp int NOT NULL,
  num int NOT NULL, flags int NOT NULL
);
""".strip())

    dict_rows = []
    for kind, d in (("meal", d_meal), ("fam", d_fam), ("prot", d_prot), ("carb", d_carb),
                    ("focus", d_focus), ("meth", d_meth), ("swap", d_swap),
                    ("num", numbers), ("flags", bools)):
        dict_rows.extend(d.rows(kind))
    write_chunked("11_recipes_dict", "INSERT INTO _seed_dict (kind,i,v) VALUES ", dict_rows)

    write_chunked(
        "12_recipes_rows",
        "INSERT INTO _seed_recipe (n,nm,meal,fam,prot,carb,focus,meth,swp,num,flags) VALUES ",
        rows,
    )

    # public_launch_approved comes from the Phase 2.8 launch-readiness verdict
    # (recipe_launch_readiness_v1.json), folded into the `flags` dictionary
    # above as its 7th '|'-separated field -- this is a display gate, distinct
    # from the dietary-claim "Launch Rule" applied separately in
    # build_assessments() below.
    write("13_recipes_materialise.sql", """
INSERT INTO recipes (
  recipe_id, meal_type, recipe_name, base_family, base_serves, prep_min, cook_min,
  budget_tier, primary_protein, carb_base, produce_focus, freezer_friendly,
  lunchbox_friendly, vegetarian_base, gf_adaptable, df_adaptable, one_pan_pot,
  method_text, mix_change_notes, public_launch_approved)
SELECT
  'GEN-RCP-' || lpad(s.n::text, 4, '0'),
  dmeal.v, s.nm, dfam.v,
  split_part(dnum.v, '|', 1)::numeric,
  split_part(dnum.v, '|', 2)::int,
  split_part(dnum.v, '|', 3)::int,
  '$',
  dprot.v, dcarb.v, dfocus.v,
  split_part(dflag.v, '|', 1)::boolean,
  split_part(dflag.v, '|', 2)::boolean,
  split_part(dflag.v, '|', 3)::boolean,
  split_part(dflag.v, '|', 4)::boolean,
  split_part(dflag.v, '|', 5)::boolean,
  split_part(dflag.v, '|', 6)::boolean,
  dmeth.v, dswap.v,
  split_part(dflag.v, '|', 7)::boolean
FROM _seed_recipe s
JOIN _seed_dict dmeal ON dmeal.kind = 'meal'  AND dmeal.i = s.meal
JOIN _seed_dict dfam  ON dfam.kind  = 'fam'   AND dfam.i  = s.fam
JOIN _seed_dict dmeth ON dmeth.kind = 'meth'  AND dmeth.i = s.meth
JOIN _seed_dict dswap ON dswap.kind = 'swap'  AND dswap.i = s.swp
JOIN _seed_dict dnum  ON dnum.kind  = 'num'   AND dnum.i  = s.num
JOIN _seed_dict dflag ON dflag.kind = 'flags' AND dflag.i = s.flags
LEFT JOIN _seed_dict dprot  ON dprot.kind  = 'prot'  AND dprot.i  = s.prot
LEFT JOIN _seed_dict dcarb  ON dcarb.kind  = 'carb'  AND dcarb.i  = s.carb
LEFT JOIN _seed_dict dfocus ON dfocus.kind = 'focus' AND dfocus.i = s.focus
ON CONFLICT (recipe_id) DO NOTHING;
""".strip())

    manifest["recipes"] = {
        "rows": len(rows),
        "dict_rows": len(dict_rows),
        "public_launch_approved_rows": approved_rows,
    }


# --------------------------------------------------------------------------
# swap_groups / swap_options
# --------------------------------------------------------------------------
def build_swap_groups(manifest):
    """recipe_catalog_v1.json's `swapMap` is the only source for swap_groups/
    swap_options -- there is no separately-authored group code, so the
    swapMap key is used as both swap_group_code and display_name (same
    approach as the mechanical dietary requirement_definitions.display_name
    below, for the same reason: no authored copy exists yet).

    PHASE_5_NEON_DATABASE_FOUNDATION_REPORT.md already flagged that only 20
    of the ~43 distinct swap_group_code values referenced by
    recipe_ingredients rows have an entry in swapMap at all -- that's a
    content gap in the V1 pack, not something this generator can fix by
    itself (the missing option lists don't exist anywhere in the source).
    This function seeds the 20 that do exist; it does not invent the rest.
    """
    catalog = load("04_PRODUCTION_STARTER", "data", "recipe_catalog_v1.json")
    swap_map = catalog["swapMap"]
    assert len(swap_map) == 20, f"expected 20 swap groups, got {len(swap_map)}"

    group_rows = [f"({q(code)},{q(code)})" for code in swap_map]
    write_chunked(
        "60_swap_groups",
        "INSERT INTO swap_groups (swap_group_code, display_name) VALUES ",
        group_rows,
        footer=" ON CONFLICT (swap_group_code) DO NOTHING",
    )

    option_rows = []
    for code, options in swap_map.items():
        for order, ingredient_name in enumerate(options, start=1):
            option_rows.append(f"({q(code)},{order},{q(ingredient_name)})")
    write_chunked(
        "61_swap_options",
        "INSERT INTO swap_options (swap_group_code, option_order, ingredient_name) VALUES ",
        option_rows,
        footer=" ON CONFLICT (swap_group_code, option_order) DO NOTHING",
    )

    manifest["swap_groups"] = {"rows": len(group_rows)}
    manifest["swap_options"] = {"rows": len(option_rows)}


# --------------------------------------------------------------------------
# dietary_requirement_definitions
# --------------------------------------------------------------------------
ACRONYMS = {"GF": "GF", "IDDSI": "IDDSI", "FODMAP": "FODMAP", "PKU": "PKU", "BBQ": "BBQ"}

# Sourced, not invented:
#  - texture codes from HIGH_CONSEQUENCE_TEXTURE_CODES in src/dietary/textureVerification.ts
#  - clinician-directed codes from NAMED_CLINICIAN_DIRECTED_CODES in src/dietary/professionalTargets.ts
#  - allergy and coeliac from DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md: "For allergy,
#    coeliac and other high-consequence restrictions..."
HIGH_CONSEQUENCE_TEXTURE = {"SAUCE_GRAVY_REQUIRED", "MOISTURE_REQUIRED"} | {f"IDDSI_LEVEL_{n}" for n in range(8)}
NAMED_CLINICIAN_DIRECTED = {
    "SODIUM_TARGET", "CARBOHYDRATE_TARGET", "ENERGY_TARGET", "PROTEIN_TARGET",
    "POTASSIUM_LIMIT", "PHOSPHATE_LIMIT", "FLUID_PLAN", "FAT_TARGET",
    "FIBRE_TARGET", "PKU_PHENYLALANINE_PLAN",
}
# Codes whose own name states that they exist only under a professional plan.
NAMED_PROFESSIONAL_PLAN = {"LOW_FODMAP_PROFESSIONAL_PLAN", "PURE_OAT_CLINICIAN_PLAN"}

DISPLAY_NOTE = ("Display name derived mechanically from the requirement code by the Phase 5 seed "
                "generator; it is not reviewed launch copy.")


def display_name(code):
    """Mechanical, reproducible label. Deliberately not authored marketing copy."""
    body = code
    prefix = ""
    if body.startswith("ALLERGY_"):
        prefix, body = "Allergy: ", body[len("ALLERGY_"):]
    words = [ACRONYMS.get(w, w.capitalize()) for w in body.split("_")]
    return prefix + " ".join(words)


def build_requirement_definitions(manifest):
    taxonomy = load("07_DIETARY_REQUIREMENTS_ENGINE", "DIETARY_TAXONOMY.json")

    codes, seen = [], set()
    for class_code, class_codes in taxonomy["requirement_classes"].items():
        for code in class_codes:
            assert code not in seen, f"duplicate requirement code {code}"
            seen.add(code)
            high = (
                class_code == "allergen"
                or code == "COELIAC_STRICT_GF"
                or code in HIGH_CONSEQUENCE_TEXTURE
                or code in NAMED_CLINICIAN_DIRECTED
                or code in NAMED_PROFESSIONAL_PLAN
            )
            professional = code in NAMED_CLINICIAN_DIRECTED or code in NAMED_PROFESSIONAL_PLAN
            codes.append((code, class_code, display_name(code), high, professional, DISPLAY_NOTE))

    assert len(codes) == 95, f"expected 95 requirement codes, got {len(codes)}"

    tuples = [
        "(" + ",".join([q(c), q(cls), q(name),
                        "true" if hc else "false",
                        "true" if pro else "false",
                        q(notes)]) + ")"
        for c, cls, name, hc, pro, notes in codes
    ]
    write_chunked(
        "20_requirement_definitions",
        "INSERT INTO dietary_requirement_definitions "
        "(requirement_code, requirement_class, display_name, high_consequence, "
        "professional_plan_only, claim_notes) VALUES ",
        tuples,
        footer=" ON CONFLICT (requirement_code) DO NOTHING",
    )
    manifest["dietary_requirement_definitions"] = {"rows": len(tuples)}
    return {c for c, *_ in codes}


# --------------------------------------------------------------------------
# ingredient_dietary_attributes
# --------------------------------------------------------------------------
def build_ingredient_attributes(manifest):
    data = load("07_DIETARY_REQUIREMENTS_ENGINE", "ingredient_dietary_attributes_v1.json")
    entries = data["ingredients"]
    known = canonical_keys()

    d_note, d_src = Dict1(), Dict1()
    rows, missing = [], []
    for entry in entries:
        name = entry["ingredient_key"]
        if name not in known:
            missing.append(name)
        for attr in entry["attributes"]:
            note = attr.get("notes")
            src = attr.get("source_reference")
            rows.append("(" + ",".join([
                q(name), q(attr["attribute_code"]), q(attr["attribute_value"]),
                q(attr["evidence_state"]),
                "NULL" if src is None else str(d_src(src)),
                "NULL" if note is None else str(d_note(note)),
            ]) + ")")
    assert not missing, f"ingredients with attributes but no canonical row: {sorted(set(missing))}"

    write("30_ingredient_attributes_ddl.sql", """
CREATE TABLE IF NOT EXISTS _seed_dict (kind text NOT NULL, i int NOT NULL, v text NOT NULL, PRIMARY KEY (kind, i));
CREATE TABLE IF NOT EXISTS _seed_ing_attr (
  canonical_name text NOT NULL, attribute_code text NOT NULL, attribute_value text NOT NULL,
  evidence_state text NOT NULL, src int, note int,
  PRIMARY KEY (canonical_name, attribute_code)
);
""".strip())

    dict_rows = d_src.rows("attr_src") + d_note.rows("attr_note")
    write_chunked("31_ingredient_attributes_dict", "INSERT INTO _seed_dict (kind,i,v) VALUES ", dict_rows)
    write_chunked(
        "32_ingredient_attributes_rows",
        "INSERT INTO _seed_ing_attr (canonical_name,attribute_code,attribute_value,evidence_state,src,note) VALUES ",
        rows,
    )
    write("33_ingredient_attributes_materialise.sql", """
INSERT INTO ingredient_dietary_attributes
  (ingredient_id, attribute_code, attribute_value, evidence_state, source_reference, verified_at)
SELECT i.ingredient_id, s.attribute_code, s.attribute_value, s.evidence_state,
       CASE WHEN s.src IS NULL AND s.note IS NULL THEN NULL
            ELSE trim(both ' | ' FROM concat_ws(' | ', dsrc.v, dnote.v)) END,
       NULL
FROM _seed_ing_attr s
JOIN ingredients i ON i.canonical_name = s.canonical_name
LEFT JOIN _seed_dict dsrc  ON dsrc.kind  = 'attr_src'  AND dsrc.i  = s.src
LEFT JOIN _seed_dict dnote ON dnote.kind = 'attr_note' AND dnote.i = s.note
ON CONFLICT (ingredient_id, attribute_code) DO NOTHING;
""".strip())
    manifest["ingredient_dietary_attributes"] = {"rows": len(rows), "dict_rows": len(dict_rows)}


# --------------------------------------------------------------------------
# recipe_ingredients
# --------------------------------------------------------------------------
def build_recipe_ingredients(manifest):
    catalog = load("04_PRODUCTION_STARTER", "data", "recipe_catalog_v1.json")
    known = canonical_keys()

    d_ing, d_unit, d_grp = Dict1(), Dict1(), Dict1()
    rows, unknown = [], set()
    for r in catalog["recipes"]:
        n = int(r["id"].split("-")[-1])
        for line in r["ingredients"]:
            # Recipe lines carry display casing ("BBQ sauce"); the canonical key
            # is the lower-cased form, which is what ingredients.canonical_name holds.
            name = line["ingredient"].lower()
            if name not in known:
                unknown.add(name)
            grp = blank_to_none(line.get("swapGroup"))
            rows.append("(" + ",".join([
                str(n), str(line["number"]), str(d_ing(name)),
                repr(float(line["baseQty"])), str(d_unit(line["unit"])),
                "true" if line.get("optional") else "false",
                "NULL" if grp is None else str(d_grp(grp)),
            ]) + ")")
    assert not unknown, f"recipe ingredients with no canonical row: {sorted(unknown)}"

    write("40_recipe_ingredients_ddl.sql", """
CREATE TABLE IF NOT EXISTS _seed_dict (kind text NOT NULL, i int NOT NULL, v text NOT NULL, PRIMARY KEY (kind, i));
CREATE TABLE IF NOT EXISTS _seed_recipe_ing (
  n int NOT NULL, line_no int NOT NULL, ing int NOT NULL, qty numeric(14,4) NOT NULL,
  unit int NOT NULL, optional boolean NOT NULL, grp int,
  PRIMARY KEY (n, line_no)
);
""".strip())

    dict_rows = d_ing.rows("ri_ing") + d_unit.rows("ri_unit") + d_grp.rows("ri_grp")
    write_chunked("41_recipe_ingredients_dict", "INSERT INTO _seed_dict (kind,i,v) VALUES ", dict_rows)
    write_chunked(
        "42_recipe_ingredients_rows",
        "INSERT INTO _seed_recipe_ing (n,line_no,ing,qty,unit,optional,grp) VALUES ",
        rows,
    )
    write("43_recipe_ingredients_materialise.sql", """
INSERT INTO recipe_ingredients (recipe_id, line_no, ingredient_id, base_qty, unit_code, optional, swap_group_code)
SELECT 'GEN-RCP-' || lpad(s.n::text, 4, '0'), s.line_no, i.ingredient_id, s.qty, dunit.v, s.optional, dgrp.v
FROM _seed_recipe_ing s
JOIN _seed_dict ding  ON ding.kind  = 'ri_ing'  AND ding.i  = s.ing
JOIN ingredients i    ON i.canonical_name = ding.v
JOIN _seed_dict dunit ON dunit.kind = 'ri_unit' AND dunit.i = s.unit
LEFT JOIN _seed_dict dgrp ON dgrp.kind = 'ri_grp' AND dgrp.i = s.grp
ON CONFLICT (recipe_id, line_no) DO NOTHING;
""".strip())

    groups = set(d_grp.values)
    manifest["recipe_ingredients"] = {
        "rows": len(rows),
        "dict_rows": len(dict_rows),
        "distinct_swap_groups_referenced": sorted(groups),
    }


# --------------------------------------------------------------------------
# recipe_requirement_assessments
# --------------------------------------------------------------------------
def build_assessments(manifest, valid_codes):
    data = load("07_DIETARY_REQUIREMENTS_ENGINE", "recipe_requirement_assessments_v1.json")
    rows = data["assessments"]

    codes = list(dict.fromkeys(r["requirement_code"] for r in rows[:42]))
    stride = len(codes)
    assert stride == 42, f"expected 42 requirement codes per recipe, got {stride}"
    unknown = [c for c in codes if c not in valid_codes]
    assert not unknown, f"assessment codes missing from the taxonomy: {unknown}"

    review_sources = {r["review_source"] for r in rows}
    assert len(review_sources) == 1, "review_source is no longer constant"
    assert all(r["reviewed"] is False for r in rows), "reviewed is no longer constant"
    assert all(r["reviewed_at"] is None for r in rows), "reviewed_at is no longer constant"
    review_source = review_sources.pop()

    explanations = list(dict.fromkeys(r["explanation"] for r in rows))
    exp_index = {e: i for i, e in enumerate(explanations)}
    assert len(explanations) < 1000, "explanation dictionary no longer fits a 3-digit index"
    state_char = {"MEETS": "M", "ADAPTABLE": "A", "EXCLUDED": "E", "UNVERIFIED": "U"}

    # Row i of the blob is (recipe i//42 + 1, codes[i % 42]); each row is one
    # state character followed by a zero-padded explanation index.
    blob = []
    for i, r in enumerate(rows):
        assert r["recipe_id"] == f"GEN-RCP-{i // stride + 1:04d}"
        assert r["requirement_code"] == codes[i % stride]
        blob.append(f"{state_char[r['suitability_state']]}{exp_index[r['explanation']]:03d}")
    blob = "".join(blob)

    write("50_assessments_ddl.sql", """
CREATE TABLE IF NOT EXISTS _seed_dict (kind text NOT NULL, i int NOT NULL, v text NOT NULL, PRIMARY KEY (kind, i));
CREATE TABLE IF NOT EXISTS _seed_blob (part int PRIMARY KEY, body text NOT NULL);
""".strip())

    dict_rows = [f"('rra_code',{i},{q(c)})" for i, c in enumerate(codes)]
    dict_rows += [f"('rra_exp',{i},{q(e)})" for i, e in enumerate(explanations)]
    write_chunked("51_assessments_dict", "INSERT INTO _seed_dict (kind,i,v) VALUES ", dict_rows)

    # The blob is split on a 4-character boundary so no encoded row is torn.
    per_part = (CHUNK_BYTES // 4) * 4
    parts = [blob[i:i + per_part] for i in range(0, len(blob), per_part)]
    for idx, part in enumerate(parts):
        write(f"52_assessments_blob_{idx:02d}.sql",
              f"INSERT INTO _seed_blob (part, body) VALUES ({idx},{q(part)});")

    write("53_assessments_materialise.sql", f"""
WITH joined AS (
  SELECT string_agg(body, '' ORDER BY part) AS blob FROM _seed_blob
), rows AS (
  SELECT gs AS i,
         substring(j.blob FROM gs * 4 + 1 FOR 1) AS state_ch,
         substring(j.blob FROM gs * 4 + 2 FOR 3)::int AS exp_i
  FROM joined j, generate_series(0, length(j.blob) / 4 - 1) AS gs
)
INSERT INTO recipe_requirement_assessments
  (recipe_id, requirement_code, suitability_state, explanation, reviewed, reviewed_at, review_source)
SELECT
  'GEN-RCP-' || lpad((r.i / {stride} + 1)::text, 4, '0'),
  dcode.v,
  CASE r.state_ch WHEN 'M' THEN 'MEETS' WHEN 'A' THEN 'ADAPTABLE'
                  WHEN 'E' THEN 'EXCLUDED' WHEN 'U' THEN 'UNVERIFIED' END,
  dexp.v,
  false,
  NULL,
  {q(review_source)}
FROM rows r
JOIN _seed_dict dcode ON dcode.kind = 'rra_code' AND dcode.i = r.i % {stride}
JOIN _seed_dict dexp  ON dexp.kind  = 'rra_exp'  AND dexp.i  = r.exp_i
ON CONFLICT (recipe_id, requirement_code) DO NOTHING;
""".strip())

    manifest["recipe_requirement_assessments"] = {
        "rows": len(rows),
        "distinct_explanations": len(explanations),
        "blob_chars": len(blob),
        "blob_parts": len(parts),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = {}
    build_recipes(manifest)
    build_swap_groups(manifest)
    valid_codes = build_requirement_definitions(manifest)
    build_ingredient_attributes(manifest)
    build_recipe_ingredients(manifest)
    build_assessments(manifest, valid_codes)

    write("99_drop_staging.sql",
          "DROP TABLE IF EXISTS _seed_recipe, _seed_ing_attr, _seed_recipe_ing, _seed_blob, _seed_dict;")

    total = 0
    for name in sorted(os.listdir(OUT)):
        total += os.path.getsize(os.path.join(OUT, name))
    manifest["_generated_bytes"] = total
    manifest["_generated_files"] = len(os.listdir(OUT))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
