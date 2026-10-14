/**
 * Identity-only health response contract for the standalone Family Budget Cookbook.
 * No household, recipe, session, database URL or customer record enters this response.
 * This is not a cross-product data bridge or proof of application acceptance.
 */
export const healthIdentity = Object.freeze({
  service: "budget-cookbook",
  mode: "standalone-family-budget-cookbook",
});

export function buildHealthResponse(
  ok: boolean,
  requestId: string,
  databaseTime: unknown = null,
) {
  if (ok) return { ...healthIdentity, ok: true, databaseTime, requestId };
  return { ...healthIdentity, ok: false, error: "database_unavailable", requestId };
}
