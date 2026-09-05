# GENEVIEVE Family Budget Cookbook™ — Dietary Requirements & Restrictions Engine

**Version:** V1 dietary-engine blueprint  
**Pack:** Complete Build Pack V2  
**Prepared:** 5 September 2026 — Australia/Brisbane

## Purpose
Make dietary requirements a first-class part of recipe selection, scaling, substitutions, affordability and household planning. The engine must support different requirements for different household members and must never treat a casual substitution flag as proof that a recipe is allergy-safe, coeliac-safe, medically appropriate, halal-certified or kosher-certified.

## Core household use case
The household may contain several people with different needs. GENEVIEVE must combine those needs before recommending a shared meal.

Example:
- Member A: vegetarian + lactose avoidance.
- Member B: no dietary restriction.
- Member C: peanut allergy.
- Member D: sensory preference — sauces separate.

The engine must return one of four recipe states:
1. **MEETS** — the reviewed recipe meets all selected requirements at recipe/ingredient level.
2. **ADAPTABLE** — it can meet requirements only after explicit approved substitutions or preparation changes.
3. **EXCLUDED** — it contains or requires something prohibited for at least one selected requirement.
4. **UNVERIFIED** — GENEVIEVE does not have enough verified ingredient/product/process evidence to make a safe suitability claim.

## Mandatory principle
**ADAPTABLE does not mean allergy-safe.**

For allergy, coeliac and other high-consequence restrictions, packaged ingredient labels, cross-contact information and preparation controls remain relevant. When evidence is incomplete, the engine must prefer **UNVERIFIED** over a reassuring guess.

## Requirement taxonomy

### A. Ethical / lifestyle
- Vegetarian
- Vegan
- Pescatarian
- Flexitarian preference
- Meat-free meal preference
- Plant-forward preference

### B. Australia allergen / declaration controls
Treat each separately in the data model rather than collapsing all tree nuts or cereals into one checkbox:
- Wheat
- Fish
- Crustacean
- Mollusc
- Egg
- Milk
- Lupin
- Peanut
- Soy / soya / soybean
- Sesame
- Almond
- Brazil nut
- Cashew
- Hazelnut
- Macadamia
- Pecan
- Pistachio
- Pine nut
- Walnut
- Barley where gluten declaration applies
- Oats where gluten declaration applies
- Rye where gluten declaration applies
- Sulphites where relevant to regulated declaration thresholds

Also support:
- custom allergen/exclusion entry;
- precautionary-label / cross-contact evidence state;
- ingredient-label verification status;
- last verification date/source.

### C. Gluten / cereal requirements
- Coeliac / strict gluten-free requirement — **specialist safety class**
- Gluten-free preference/non-coeliac setting
- Wheat-free
- Rye-free
- Barley-free
- Oat exclusion
- Clinician-supervised pure-oat trial marker where applicable

**Australian claim boundary:** do not call an oat-containing recipe “gluten free” merely because an overseas ingredient/product uses that wording. Australian rules and current Coeliac Australia guidance require special handling of oats. The app must model oats separately and preserve an **UNVERIFIED** state when product suitability is not established.

### D. Intolerances / sensitivities / exclusions
- Lactose-free / lactose reduction
- Dairy-free
- Fructose-sensitive custom plan
- Low-FODMAP **clinician/dietitian-directed mode**
- Caffeine-free
- Alcohol-free
- Low-spice / chilli-free
- Onion-free
- Garlic-free
- Any custom ingredient exclusion
- Any custom ingredient preference

Low-FODMAP must not be presented as a permanent generic “healthy diet.” The production mode must support a professional-plan boundary and personalised reintroduction/tolerance settings rather than a crude permanent blacklist.

### E. Religious / cultural compatibility
- Pork-free
- Beef-free
- Alcohol-free
- Halal-compatible ingredient/preparation preference
- Kosher-compatible ingredient/preparation preference
- Custom cultural/religious exclusions

**Claim boundary:** GENEVIEVE may describe ingredient/preparation compatibility when verified; it must not say “halal certified” or “kosher certified” unless certification evidence for the relevant product/process is actually recorded.

### F. Clinician-directed nutritional controls
These settings must be clearly labelled **professional-plan / clinician-directed** and must not diagnose or prescribe:
- Sodium limit / low-sodium plan
- Carbohydrate target/counting plan
- Energy target / energy-dense plan
- Protein target / high-protein or restricted-protein plan
- Potassium limit
- Phosphate/phosphorus limit
- Fluid-related meal planning marker
- Fat target / low-fat plan
- Fibre target / low-fibre / high-fibre plan
- Phenylalanine/PKU specialist plan
- Other prescribed nutrient limit entered as a custom professional plan

The engine should store the user-entered or clinician-provided target. It must not invent a therapeutic target.

### G. Texture / swallowing
- Regular texture
- Easy-to-chew preference
- IDDSI food/drink level where selected by an appropriate clinician or care plan
- Sauce/gravy requirement
- Moisture requirement
- Texture-modified preparation notes

**Safety boundary:** IDDSI suitability cannot be inferred only from a recipe name. Final food/drink characteristics depend on preparation and serving conditions and need appropriate testing/clinical direction where dysphagia is involved.

### H. Life-stage / age suitability
- Pregnancy-conscious ingredient/preparation checks
- Breastfeeding preferences
- Child-friendly
- Toddler/young-child age-suitability checks
- Older-person meal preferences
- Age-based custom exclusions

Production launch must review any age/pregnancy safety claims against authoritative Australian guidance before enabling those flags as “safe”. Until verified, use **UNVERIFIED / check guidance** rather than a safety guarantee.

### I. Sensory / preference / feeding-style controls
- No mixed textures
- Sauce separate
- Plain/mild food
- Crunchy preference
- Soft preference
- Temperature preference
- No visible vegetables
- Ingredient dislikes
- Ingredient favourites
- Custom sensory rule

These are preference controls and must remain separate from allergy/medical safety controls.

### J. Practical household controls that interact with diet
- Pantry-only
- Meal budget ceiling
- Total weekly budget ceiling
- Freezer-friendly
- Lunchbox-friendly
- One-pot / one-pan
- Microwave-only
- No-oven
- Low-prep
- Batch cooking
- Leftover-first
- Use-soon ingredients
- School/nut-aware packing mode (must not claim a school is “nut-free” without the school policy)

## Household-member model
Each household can have zero or more members. Each member may have zero or more requirements. Requirements carry:
- requirement code;
- requirement class (allergy, medical, ethical, religious, sensory, preference, practical);
- severity/enforcement (`HARD_EXCLUDE`, `REQUIRE_VERIFIED`, `PREFER`, `INFORMATION_ONLY`);
- source (`USER`, `CLINICIAN_PLAN`, `CARE_PLAN`, `SYSTEM_DEFAULT`);
- optional notes;
- start/end date;
- verification date where relevant.

## Recipe evaluation order
1. Resolve selected household members for the meal.
2. Combine **hard exclusions** first.
3. Check recipe ingredient attributes and preparation requirements.
4. Check product-level or cross-contact evidence when a high-consequence rule requires it.
5. Search only substitutions that do not violate any member’s hard exclusions.
6. Recalculate recipe quantities for household size.
7. Recalculate the adapted recipe cost using the actual substitution.
8. Apply nutritional/professional targets where explicitly supplied.
9. Apply preferences and practical filters.
10. Return `MEETS`, `ADAPTABLE`, `EXCLUDED` or `UNVERIFIED` with an explanation for every member-relevant rule.

## Substitution rule
A substitution is only eligible if:
- it is mapped to the ingredient function needed by the recipe;
- it does not conflict with any hard exclusion;
- its dietary attributes are known enough for the requested requirement;
- it preserves any required preparation/texture boundary;
- the user is shown the change;
- the budget engine recalculates using the substitute’s price/pack data.

## Cost integration
Dietary substitutions are not “free” in the maths. The cost engine must calculate the **actual adapted version** of the meal. A dairy-free cheese, GF pasta, tofu, seed butter or other substitute may change the basket cost. Ranking must use the adapted cost rather than the original recipe cost.

## No false safety claims
Never use the following as automatic equivalents:
- “adaptable” = allergy-safe;
- “wheat-free” = coeliac-safe;
- “dairy-free” = lactose-free or vice versa;
- “plant-based” = vegan;
- “meat-free” = vegetarian if fish/animal-derived ingredients remain;
- “halal-compatible” = halal-certified;
- “kosher-compatible” = kosher-certified;
- “soft” = verified IDDSI level;
- “low-FODMAP ingredients” = a personalised therapeutic diet plan.

## Extensibility requirement
No fixed list can cover every rare allergy, intolerance, prescribed diet, cultural rule or sensory need. The engine therefore **must include CUSTOM_EXCLUSION, CUSTOM_REQUIREMENT and CUSTOM_PREFERENCE as first-class records**, not as free-text notes that the recommendation engine ignores.

## Launch rule
No dietary flag becomes a public “MEETS” claim across the 800-recipe catalogue until the Phase 2 dietary QA gate has reviewed the relevant ingredient/recipe mapping. Unreviewed recipes remain `UNVERIFIED` for that requirement.
