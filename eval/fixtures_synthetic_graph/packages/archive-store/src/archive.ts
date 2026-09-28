// Synthetic sink service: same role as db-pool in mock-codebase2 -- a leaf
// with no outgoing dependencies, called directly by two other services.
let writes = 0;

export async function writeArchive(orderId: string) {
  writes++;
  return { ok: true, orderId };
}
