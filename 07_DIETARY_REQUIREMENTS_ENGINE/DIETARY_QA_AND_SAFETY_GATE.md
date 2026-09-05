# Phase 2 Dietary QA & Safety Gate

## Exact chronological order

### Phase 2.1 — Freeze Dietary Taxonomy & Claim Boundaries — NEXT
- approve the taxonomy in `DIETARY_REQUIREMENTS_MASTER_BLUEPRINT.md`;
- approve the four suitability states;
- approve the distinction between hard safety requirements and preferences;
- approve custom requirement/exclusion support;
- freeze wording for “compatible”, “adaptable”, “verified”, “unverified” and certification claims.

**GREEN gate:** taxonomy and language are internally consistent and do not imply medical, allergy, coeliac, religious-certification or dysphagia safety without evidence.

### Phase 2.2 — Canonical Ingredient Dietary Attribute Model
For every canonical ingredient, support attributes including:
- animal-derived / meat / poultry / fish / shellfish;
- dairy/milk;
- egg;
- honey/bee-derived where relevant to vegan mode;
- Australia allergen declarations;
- cereal/gluten attributes;
- alcohol;
- pork/beef source;
- potential hidden-source flags where ingredient derivation matters;
- custom attribute extension.

**GREEN gate:** the model can express all locked requirement classes without relying only on ingredient-name string matching.

### Phase 2.3 — Household Member Requirement Model
Implement household members, member requirements, enforcement level and source/provenance.

**GREEN gate:** different members can carry conflicting requirements without one profile overwriting another.

### Phase 2.4 — Recipe Classification of all 800 Recipes
Audit each recipe against each applicable requirement family. Do not infer high-consequence claims from recipe name alone.

**GREEN gate:** every launch recipe has a versioned classification record or remains explicitly `UNVERIFIED`.

### Phase 2.5 — Substitution Safety & Cost Recalculation
Map approved substitutions by function and dietary attributes. Ensure a proposed substitute never violates another household member’s hard exclusion.

**GREEN gate:** every displayed adaptation changes both the ingredient list and the affordability calculation.

### Phase 2.6 — Medical / Professional-Plan Boundaries
Implement clinician/dietitian/care-plan supplied targets only as supplied values. Do not diagnose, prescribe or invent therapeutic targets.

**GREEN gate:** medical modes cannot activate from an AI inference about the user’s health; they require explicit user/professional-plan configuration.

### Phase 2.7 — Texture / IDDSI Boundary
If IDDSI is supported, store the requested level from an appropriate care/clinical source and require recipe/preparation verification before claiming suitability.

**GREEN gate:** no recipe is called IDDSI-compliant from description alone.

### Phase 2.8 — Full Phase 2 Recipe/Content QA
Complete culinary QA: quantities, timings, scaling edge cases, allergen/adaptation language, and exclude unresolved launch recipes.

**GREEN gate:** no unsafe/misleading dietary claims; all public launch recipes have reviewed content; unresolved recipes stay out of the launch set or remain visibly unverified.
