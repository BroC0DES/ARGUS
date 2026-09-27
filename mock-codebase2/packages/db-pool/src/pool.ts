// A tiny, real (if simplified) connection pool.

let active = 0;

// ============================================================
// BUG #2 — DATABASE POOL EXHAUSTION
// TO BREAK (cause the failure): leave this at 5
// TO FIX (stop the failure):   change this to 50
// Under normal traffic, active connections can exceed 5, and any
// request arriving while the pool is full is rejected outright
// (POOL_EXHAUSTED) instead of queued. 50 gives real headroom.
// This is the trigger for the CASCADING scenario — payment-service,
// ledger-worker, and orders-service all depend on this pool, so
// exhausting it here causes failures to ripple into all three.
// ============================================================
const maxConnections = 5;

export class PoolError extends Error {
  code: string;
  constructor(code: string) {
    super(`Database pool error: ${code}`);
    this.code = code;
  }
}

export async function withConnection<T>(fn: () => Promise<T>): Promise<T> {
  if (active >= maxConnections) {
    throw new PoolError("POOL_EXHAUSTED");
  }
  active++;
  try {
    return await fn();
  } finally {
    active--;
  }
}

export async function recordTransaction(orderId: string, amount: number) {
  return withConnection(async () => {
    return { ok: true, orderId, amount };
  });
}

export async function saveOrder(orderId: string) {
  return withConnection(async () => {
    return { ok: true, orderId };
  });
}

export async function writeLedgerEntry(orderId: string, amount: number) {
  return withConnection(async () => {
    return { ok: true, orderId, amount };
  });
}

