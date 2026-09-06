# Recipe Content Folder

- `GENEVIEVE_Family_Budget_Cookbook_Recipe_Bank_V1_800.xlsx` — authoritative V1 recipe workbook baseline.
- `build_recipe_bank.py` — generator used to produce the current structured recipe bank.

The spreadsheet contains recipe metadata, normalized ingredient rows, swap matrix, scaling rules and app schema material. Production migration must preserve stable recipe IDs and reconcile counts to the sealed baseline.

Before public launch, run Phase 2 content/culinary QA. A structured/generated recipe record is not automatically equivalent to a kitchen-tested published recipe.
