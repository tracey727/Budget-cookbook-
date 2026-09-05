# Household Member Dietary Profile Contract

A household must be able to plan one meal for one member, selected members, or everybody.

## Required member fields
- `member_id`
- `household_id`
- display name/nickname
- active/inactive
- optional age band (not date of birth unless genuinely required)
- requirement records

## Requirement fields
- `requirement_code`
- `requirement_class`
- `enforcement_level`
- `source_type`
- `notes`
- `starts_at`
- `ends_at`
- `verified_at`
- `professional_plan_reference` (optional; never expose unnecessarily)

## Enforcement levels
- `HARD_EXCLUDE` — recipe cannot be recommended when the requirement conflicts.
- `REQUIRE_VERIFIED` — recipe may only be `MEETS` when evidence is verified; otherwise `UNVERIFIED`.
- `PREFER` — ranking signal, not exclusion.
- `INFORMATION_ONLY` — show information but do not alter ranking unless user elects to.

## Privacy/minimisation
The app does not need a diagnosis to honour a dietary rule. Prefer “avoid peanut” or “sodium limit supplied by user/care plan” over storing unnecessary clinical narrative. Medical reasons should not be required unless the function genuinely depends on them.
