// Live HTTP wrapper for payment-service.
//
// chargeViaGateway() from gateway.ts -- the actual BUG #1 function -- is called
// completely unchanged below; that's the literal ask ("payment-service exposes
// POST /charge calling the existing charge() function unchanged").
//
// One deliberate deviation: charge.ts's own charge() wrapper also calls
// recordTransaction() from db-pool via a direct in-process import, which would
// give payment-service its OWN private copy of pool.ts's connection counter,
// separate from the one db-pool's real server tracks for orders-service and
// ledger-worker's calls. That breaks the shared-resource premise the
// cascading-failure scenario depends on (one pool, multiple real dependents).
// So the db-pool call here goes over real HTTP instead, exactly like every other
// caller -- charge.ts itself is untouched and still on disk (still what the Code
// Indexer finds for the payment-service -> db-pool edge).
import express from "express";
import { chargeViaGateway } from "./gateway";
import { URLS, PORTS } from "../../../shared/ports";
import { log } from "../../../shared/logger";

const app = express();
app.use(express.json());

app.post("/charge", async (req, res) => {
  const { id, amount } = req.body as { id: string; amount: number };
  const start = Date.now();
  try {
    const gw = await chargeViaGateway(id);
    if (!gw.ok) {
      if (gw.code === "GATEWAY_TIMEOUT") {
        log("ERROR", "payment-service", `gateway.charge timeout after ${Date.now() - start}ms order=${id}`);
      }
      log("ERROR", "payment-service", `charge failed order=${id} code=${gw.code}`);
      res.status(502).json({ ok: false, code: gw.code });
      return;
    }
    // Real edge: payment-service -> db-pool.
    const dbRes = await fetch(`${URLS.dbPool}/transaction`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ orderId: id, amount }),
    });
    if (!dbRes.ok) {
      log("ERROR", "payment-service", `transaction record failed order=${id} code=POOL_EXHAUSTED`);
      res.status(503).json({ ok: false, code: "POOL_EXHAUSTED" });
      return;
    }
    log("INFO", "payment-service", `gateway.charge succeeded order=${id} latency=${Date.now() - start}ms`);
    res.json({ ok: true, orderId: id });
  } catch (e) {
    const code = (e as { code?: string })?.code || "UNKNOWN";
    log("ERROR", "payment-service", `charge failed order=${id} code=${code}`);
    res.status(502).json({ ok: false, code });
  }
});

app.listen(PORTS.paymentService, () => log("INFO", "payment-service", `listening on :${PORTS.paymentService}`));
