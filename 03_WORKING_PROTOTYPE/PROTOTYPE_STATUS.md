# Working Prototype Status

**Status:** BUILT / browser prototype / not production persistence.

Verified source-baseline behaviour includes:
- 800 recipe catalogue;
- household scaling;
- pantry quantities;
- local price book;
- shortage and missing-cost calculations;
- filters;
- ranking;
- detail modal with scaled ingredients and swaps;
- browser `localStorage` persistence.

Production replacement rules:
- do not discard this prototype until production regression tests match it;
- bundled `data.js` becomes server/database catalogue data;
- localStorage household data becomes authenticated Neon-backed state;
- production price model adds retail pack size and unit conversion;
- current deterministic ranking remains the regression baseline.
