import { buildHealthResponse, healthIdentity } from "./health-contract";

function equal(actual: unknown, expected: unknown, name: string): void {
  if (actual !== expected) throw new Error(name + ": expected " + String(expected) + ", got " + String(actual));
}

const requestId = "synthetic-request-id";
const ready = buildHealthResponse(true, requestId, "2026-10-14T00:00:00.000Z");
const down = buildHealthResponse(false, requestId);

for (const payload of [ready, down]) {
  equal(payload.service, "budget-cookbook", "product identity");
  equal(payload.mode, "standalone-family-budget-cookbook", "product scope");
  equal(payload.requestId, requestId, "request ID");
  const encoded = JSON.stringify(payload);
  for (const forbidden of ["password", "DATABASE_URL", "connectionString", "customer", "email", "household"]) {
    if (encoded.includes(forbidden)) throw new Error("Health payload contains prohibited detail: " + forbidden);
  }
}
equal(ready.ok, true, "success status");
if (!("databaseTime" in ready)) throw new Error("Success response missing database time");
equal(ready.databaseTime, "2026-10-14T00:00:00.000Z", "existing database time");
equal(down.ok, false, "failure status");
if (!("error" in down) || down.error !== "database_unavailable") throw new Error("Error contract changed");
if ("databaseTime" in down) throw new Error("Failure response must not report database time");
equal(healthIdentity.service, ready.service, "stable identity");
