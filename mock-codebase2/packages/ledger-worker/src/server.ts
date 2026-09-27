// Live HTTP wrapper for ledger-worker. Nothing in the original codebase actually
// called recordLedgerEntry() from ledger.ts (no import graph edge pointed at
// ledger-worker at all) -- for it to participate in genuinely live traffic, it
// needs a real caller; orders-service's server.ts calls it after saving the order.
//
// Reaches db-pool over real HTTP for the same shared-connection-count reason as
// payment-service's server.ts -- ledger.ts's own direct import of writeLedgerEntry
// is left untouched on disk (still what the Code Indexer finds for the
// ledger-worker -> db-pool edge).
import express from "express";
import { URLS, PORTS } from "../../../shared/ports";
import { log } from "../../../shared/logger";

const app = express();
app.use(express.json());

app.post("/entry", async (req, res) => {
  const { orderId, amount } = req.body as { orderId: string; amount: number };
  try {
    const r = await fetch(`${URLS.dbPool}/ledger-entry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ orderId, amount }),
    });
    if (!r.ok) {
      log("ERROR", "ledger-worker", `ledger write failed order=${orderId} code=POOL_EXHAUSTED`);
      res.status(503).json({ ok: false });
      return;
    }
    log("INFO", "ledger-worker", `ledger entry written order=${orderId}`);
    res.json({ ok: true });
  } catch {
    log("ERROR", "ledger-worker", `ledger write failed order=${orderId} code=POOL_EXHAUSTED`);
    res.status(503).json({ ok: false });
  }
});

app.listen(PORTS.ledgerWorker, () => log("INFO", "ledger-worker", `listening on :${PORTS.ledgerWorker}`));
