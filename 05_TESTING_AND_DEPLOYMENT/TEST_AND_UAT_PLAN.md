# Test + UAT Plan

## A. Catalogue integrity
- recipe count reconciles to 800 source baseline before any launch exclusions;
- ingredient-line count reconciles to 3,840 source baseline;
- recipe IDs unique and stable;
- swap groups reconcile to 20 source groups;
- no orphan recipe ingredients.

## B. Scaling golden tests
Test target serves 1, 2, 4, 6, 8, 10 against recipes containing:
- cups/volume;
- grams/mass;
- eggs/count;
- optional lines;
- strong spice;
- oil;
- raising agent;
- tins/packs after Phase 10.

## C. Pantry math
- zero pantry;
- exact pantry coverage;
- partial pantry;
- surplus pantry;
- pantry unit mismatch must not be silently subtracted;
- one weekly plan must not consume the same pantry quantity twice.

## D. Pricing states
- no shortage => Cook now even without price;
- shortage + missing price => Need prices;
- complete price + under cap => Within budget;
- complete price + over cap => Over budget;
- price zero is not treated as a genuine retail price unless explicitly allowed as a free item.

## E. Shopping pack math
- exact one pack;
- fraction of pack rounds purchase up;
- multiple pack sizes;
- price-per-unit versus basket-outlay distinction;
- canned/count items never instruct purchase of fractional packs.

## F. Filters
Every required filter excludes non-matching recipes: meal type, vegetarian, GF adaptable, DF adaptable, lunchbox, freezer, one-pan/pot.

## G. Account/security
- household A cannot read/write household B;
- unauthenticated private endpoints reject;
- session expiry behaves safely;
- SQL inputs parameterised;
- rate limits and CSRF/session protections tested where applicable.

## H. Stripe
- Checkout success;
- cancellation;
- payment failure;
- webhook replay/idempotency;
- invalid signature rejected;
- entitlement remains consistent if webhook order changes.

## I. UAT journeys
1. First-time user with empty pantry.
2. User with pantry but no prices.
3. User with pantry + prices + $15 dinner cap.
4. Household changes from 2 to 6 people.
5. User selects cheaper swap.
6. User builds a 7-day plan and shopping list.
7. User subscribes, cancels and later returns.
8. Mobile-only journey.
