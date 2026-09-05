# Feature Register

| Feature | V1 Prototype | Production target |
|---|---|---|
| 800 recipe catalogue | Built | Migrate + QA |
| Household serving scaler | Built | Harden + unit rules |
| Pantry entry | Built local | Persist securely |
| Price book | Built local | Persist + pack model |
| Missing ingredient calculation | Built | Preserve |
| Affordability state | Built | Preserve; add basket outlay |
| Meal/diet/use filters | Built | Preserve |
| Ranking engine | Built | Preserve + explainability |
| Recipe detail | Built | Production UI/API |
| Swap suggestions | Built | Canonical mapping |
| Retail pack conversion | Not built | Required |
| Shopping list | Not built | Required |
| Weekly meal planner | Not built | Required |
| Leftover/batch logic | Not built | Required after planner |
| Accounts/auth | Not built | Required for cloud persistence |
| Neon persistence | Not built | Required |
| Cloudflare Worker/API | Starter only | Required |
| Stripe | Not built | Required for paid tier |
| PWA/offline | Not built | Optional/late gate |
| Production monitoring | Not built | Required before launch |


## V2 Dietary Requirements Engine additions
- Multi-member household dietary profiles
- Vegetarian / vegan / pescatarian / flexitarian preferences
- Australia allergen declaration model with individual tree nuts/cereals
- Coeliac/gluten/oats special boundary
- Lactose/dairy and custom intolerance/exclusion support
- Low-FODMAP professional-plan mode
- Religious/cultural compatibility settings without false certification
- Clinician-directed nutrient target records
- IDDSI/texture-modified boundary
- Life-stage and sensory/preference controls
- MEETS / ADAPTABLE / EXCLUDED / UNVERIFIED recipe states
- Safe substitution intersection across all selected household members
- Adapted-recipe affordability recalculation
- CUSTOM_EXCLUSION / CUSTOM_REQUIREMENT / CUSTOM_PREFERENCE
