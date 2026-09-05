# Phase 2.1 — Freeze Dietary Taxonomy & Claim Boundaries

Gate: `01_MASTER_BLUEPRINT/CHRONOLOGICAL_BUILD_AND_GREEN_GATES.md` Phase 2.1.
Reviewed against the full `07_DIETARY_REQUIREMENTS_ENGINE/` folder and
`04_PRODUCTION_STARTER/schema/002_dietary_requirements.sql`, per the V2 pack's
continuation instructions.

## 1. Taxonomy — approved with two content gaps closed (v1.1)

`DIETARY_TAXONOMY.json` is approved as the frozen requirement-code list, with
three corrections made during this review before freezing (now v1.1):

1. **`ALCOHOL_FREE` duplicate removed.** v1.0 listed `ALCOHOL_FREE` under both
   `intolerance_sensitivity` and `religious_cultural`. `dietary_requirement_definitions`
   in the schema uses `requirement_code` as its primary key with a single
   `requirement_class` column — a code cannot carry two classes in the seed
   data. Canonical home is now `intolerance_sensitivity`; a member selecting
   it for religious reasons records that in `notes`/`source_type`, not via a
   second class. Behaviourally identical either way (it's a `HARD_EXCLUDE` on
   alcohol), so nothing about enforcement changes.
2. **`SCHOOL_NUT_AWARE_PACKING` added to `practical`.** The prose blueprint
   (section J) calls out school/nut-aware packing mode with an explicit claim
   boundary ("must not claim a school is 'nut-free' without the school
   policy"), but v1.0's JSON had no code for it, so that boundary had nothing
   to attach to. Added as a first-class practical code carrying the same
   claim boundary as an allergen `INFORMATION_ONLY`/`PREFER` signal, never a
   `MEETS` guarantee.
3. **`SAUCE_GRAVY_REQUIRED` and `MOISTURE_REQUIRED` added to `texture_swallowing`.**
   The prose blueprint (section G) lists "sauce/gravy requirement" and
   "moisture requirement" as texture/swallowing needs distinct from the
   sensory preference `SAUCE_SEPARATE` (which is about plating preference,
   not swallowing safety). These are safety-relevant like the IDDSI levels,
   so they belong in `texture_swallowing`, not folded into a generic custom
   note where the dysphagia safety boundary in `RECIPE_SUITABILITY_STATE_CONTRACT.md`
   would not visibly apply to them.

No other inconsistencies found: every other prose item in
`DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md` either has a matching code or is
intentionally left to `CUSTOM_EXCLUSION`/`CUSTOM_REQUIREMENT`/`CUSTOM_PREFERENCE`
per the extensibility requirement (e.g. "ingredient dislikes/favourites",
"age-based custom exclusions"). Meal/weekly budget ceilings are correctly
*not* modelled as dietary requirement codes — they're numeric engine inputs
(`mealBudget`, a future weekly ceiling), not boolean dietary flags.

## 2. Four suitability states — approved

`MEETS` / `ADAPTABLE` / `EXCLUDED` / `UNVERIFIED` as defined in
`RECIPE_SUITABILITY_STATE_CONTRACT.md`, with the stated precedence order
(unresolved high-consequence → `UNVERIFIED`; hard conflict with no substitute
→ `EXCLUDED`; substitution needed → `ADAPTABLE`; fully satisfied → `MEETS`).
`schema/002_dietary_requirements.sql` enforces exactly these four values via
`CHECK` constraints on `recipe_requirement_assessments.suitability_state` and
`dietary_substitution_rules.suitability_state`. Consistent, approved as-is.

## 3. Hard safety requirements vs. preferences — approved

The four enforcement levels (`HARD_EXCLUDE`, `REQUIRE_VERIFIED`, `PREFER`,
`INFORMATION_ONLY`) are defined once in `HOUSEHOLD_MEMBER_PROFILE_CONTRACT.md`
and enforced by the same `CHECK` constraint on both
`member_dietary_requirements.enforcement_level` and
`custom_dietary_rules.enforcement_level` — one household member's
`HARD_EXCLUDE` cannot be silently downgraded to a `PREFER` by another
member's row, since enforcement is stored per member, per requirement.
Approved.

## 4. Custom requirement/exclusion support — approved

`CUSTOM_EXCLUSION` / `CUSTOM_REQUIREMENT` / `CUSTOM_PREFERENCE` are modelled
as first-class rows in `custom_dietary_rules` (own table, own enforcement
level, optional link to a canonical ingredient), not as free-text notes the
recommendation engine would ignore. Matches the extensibility requirement.
Approved.

## 5. Frozen claim-boundary language

This supersedes `02_RECIPE_CONTENT/DIETARY_CLAIM_LANGUAGE.md` (which only
covered the V1 GF/DF badge) as the canonical wording for the full taxonomy.
The V1 file stays as-is for its historical GF/DF-specific context but the
product must use this wording going forward for every requirement class.

| Term | Frozen meaning | Must never be read as |
|---|---|---|
| **Compatible** | The recipe's listed ingredients and preparation, as reviewed, do not conflict with the requirement. | Certified, guaranteed, or safe regardless of the specific product/brand used. |
| **Adaptable** | The recipe's structure can meet the requirement after a specific, shown substitution or preparation change. | Allergy-safe, coeliac-safe, or already meeting the requirement without the change being made. |
| **Verified** | Evidence (ingredient label, product spec, or equivalent) has actually been checked and recorded, with a date/source. | A default state, or something implied by a recipe simply looking suitable. |
| **Unverified** | Evidence is incomplete, ambiguous, or depends on a packaged product/process GENEVIEVE has not checked. This state outranks a reassuring guess — it is the default until evidence exists. | A minor caveat that can be waved away to show more results. |
| **Halal-compatible / Kosher-compatible** | Ingredients/preparation are compatible with the practice, as reviewed. | "Halal certified" / "Kosher certified" — never used unless a real certification record for that specific product/process is on file. |
| **[Any professional-plan target]** (sodium, carbohydrate, IDDSI level, etc.) | A value supplied by the user or their clinician/care plan, stored and applied as given. | A diagnosis, prescription, or therapeutic recommendation generated by GENEVIEVE. The app never invents or infers these targets. |

Required user-facing disclaimer (extends the V1 GF/DF banner in
`03_WORKING_PROTOTYPE/index.html` to the full taxonomy once dietary filters
ship in the UI):

> **Adaptable and compatible are not certification.** These labels describe
> GENEVIEVE's review of listed ingredients and preparation — not a
> guarantee for any specific product, and not medical, allergy, coeliac,
> religious-certification or swallowing-safety advice. Always check
> packaged product labels and, for medical or swallowing needs, follow your
> clinician or care plan.

## Gate status

**GREEN.** Taxonomy (v1.1) and language above are internally consistent, the
three defects found during review are fixed rather than deferred, and no
wording claims medical, allergy, coeliac, religious-certification or
dysphagia safety without evidence. Phase 2.2 (canonical ingredient dietary
attribute model) can proceed against this frozen taxonomy.
