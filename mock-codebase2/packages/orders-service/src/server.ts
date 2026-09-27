// Live HTTP wrapper for orders-service -- the orchestrator that fans out to
// payment-service, db-pool, ledger-worker, and notify-worker, all over real HTTP
// (each is now a separately running, separately hot-reloading process).
//
// checkout.ts's own direct imports of handleChargeRequest/saveOrder/
// queueConfirmationEmail are left untouched on disk -- still what the Code
// Indexer finds for the orders-service -> {payment-service, db-pool,
// notify-worker} edges. The one edge the original codebase never had at all is
// orders-service -> ledger-worker (nothing called ledger-worker before this),
// so recordLedgerEntry is imported here -- unused at runtime, purely so that new,
// genuinely-live edge is still statically detectable too.
import express from "express";
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { recordLedgerEntry } from "../../ledger-worker/src/ledger";
import { URLS, PORTS } from "../../../shared/ports";
import { log } from "../../../shared/logger";

const app = express();
app.use(express.json());

async function post(url: string, body: unknown) {
  // Never throws: a downstream service being mid-restart (real hot-reload, or a
  // genuine crash) must show up as a failed call here, not an unhandled rejection
  // that takes this whole process down with it.
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let data: unknown = null;
    try { data = await res.json(); } catch { /* no body */ }
    return { ok: res.ok, status: res.status, data };
  } catch (e) {
    return { ok: false, status: 0, data: null, error: (e as Error).message };
  }
}

app.post("/checkout", async (req, res) => {
  const { orderId, amount, email } = req.body as { orderId: string; amount: number; email: string };
  log("INFO", "orders-service", `checkout started order=${orderId}`);

  // Payment (real edge: orders-service -> payment-service) and the order-save
  // (real edge: orders-service -> db-pool) are independent operations -- run
  // concurrently, not one after the other. This also matters for BUG #2: db-pool's
  // maxConnections is only ever meaningfully exercised by requests that actually
  // land on it at close to the same instant, and payment-service's own call can
  // take anywhere from ~0.3s to 9s (BUG #1's gateway latency) -- sequencing behind
  // that would stagger every order's db-pool call to a different random moment,
  // never overlapping.
  const [payment, saved] = await Promise.all([
    post(`${URLS.paymentService}/charge`, { id: orderId, amount }),
    post(`${URLS.dbPool}/save-order`, { orderId }),
  ]);
  if (!payment.ok) {
    log("WARN", "orders-service", `charge failed, retry 1/3 order=${orderId}`);
  }
  // If db-pool is exhausted (BUG #2), this can fail even when payment itself
  // succeeded -- a second, independent way orders-service can show an error,
  // distinct from a payment failure.
  if (!saved.ok) {
    log("ERROR", "orders-service", `order save failed order=${orderId} code=POOL_EXHAUSTED`);
  } else {
    log("INFO", "orders-service", `order saved order=${orderId}`);
  }

  // Real edge: orders-service -> ledger-worker
  await post(`${URLS.ledgerWorker}/entry`, { orderId, amount }).catch(() => null);

  // Real edge: orders-service -> notify-worker
  await post(`${URLS.notifyWorker}/queue`, { orderId, email }).catch(() => null);

  const ok = payment.ok && saved.ok;
  res.status(ok ? 200 : 502).json({ ok, orderId, payment: payment.data });
});

app.listen(PORTS.ordersService, () => log("INFO", "orders-service", `listening on :${PORTS.ordersService}`));
