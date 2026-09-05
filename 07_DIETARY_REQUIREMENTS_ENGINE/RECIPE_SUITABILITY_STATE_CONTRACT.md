# Recipe Suitability State Contract

## Canonical states

### MEETS
Use only when the recipe and all relevant ingredient/preparation evidence satisfy the selected requirement set.

### ADAPTABLE
Use when one or more approved substitutions/preparation changes can satisfy the selected requirements. The adapted ingredient list and recalculated cost must be shown before selection.

### EXCLUDED
Use when at least one hard requirement is violated and no approved safe substitution path exists.

### UNVERIFIED
Use whenever evidence is incomplete, ambiguous or depends on an unverified packaged product/process. **UNVERIFIED outranks optimism.**

## Precedence
For a household meal involving multiple people:
1. any unresolved high-consequence safety requirement can force `UNVERIFIED`;
2. any hard conflict with no approved substitute forces `EXCLUDED`;
3. one or more required approved substitutions yields `ADAPTABLE`;
4. only a fully satisfied set yields `MEETS`.

## Explanation payload
Every result must return machine-readable reasons, for example:

```json
{
  "state": "ADAPTABLE",
  "member_results": [
    {
      "member_id": "...",
      "requirement_code": "VEGAN",
      "result": "ADAPTABLE",
      "reason": "Replace dairy milk with an approved plant milk"
    },
    {
      "member_id": "...",
      "requirement_code": "ALLERGY_PEANUT",
      "result": "MEETS",
      "reason": "No peanut ingredient in reviewed recipe; product-level label verification still applies where packaged foods are used"
    }
  ]
}
```

## UX copy boundary
- Green: **Meets selected requirements**
- Amber: **Can be adapted — review changes**
- Red: **Does not meet selected requirements**
- Grey: **Cannot verify yet — check ingredients/process**

Never replace the grey state with a green state merely to increase recipe results.
