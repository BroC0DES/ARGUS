// Live HTTP wrapper for db-pool. pool.ts's functions (and BUG #2's maxConnections)
// are called completely unchanged -- this file only adds the HTTP transport.
// db-pool is the ONE process where pool.ts's module-level `active` counter lives,
// so every other service reaching it (via real HTTP, see their own server.ts files)
// shares the exact same connection count -- which is what makes the cascading
// scenario (payment-service + ledger-worker + orders-service all failing together
// when the pool is exhausted) genuinely real instead of three separate, unshared
// in-memory counters.
import express from "express";
import { recordTransaction, saveOrder, writeLedgerEntry } from "./pool";
import { PORTS } from "../../../shared/ports";
import { log } from "../../../shared/logger";

const app = express();
app.use(express.json());

function route(
  fn: (orderId: string, amount?: number) => Promise<unknown>,
  okMessage: (orderId: string) => string,
) {
  return async (req: express.Request, res: express.Response) => {
    const { orderId, amount } = req.body as { orderId: string; amount?: number };
    try {
      const result = await fn(orderId, amount);
      log("INFO", "db-pool", okMessage(orderId));
      res.json(result);
    } catch (e) {
      const code = (e as { code?: string })?.code || "POOL_ERROR";
      log("ERROR", "db-pool", `connection pool exhausted order=${orderId} code=${code}`);
      res.status(503).json({ ok: false, code });
    }
  };
}

app.post("/transaction", route((id, amt) => recordTransaction(id, amt as number), (id) => `transaction recorded order=${id}`));
app.post("/save-order", route((id) => saveOrder(id), (id) => `order saved order=${id}`));
app.post("/ledger-entry", route((id, amt) => writeLedgerEntry(id, amt as number), (id) => `ledger entry recorded order=${id}`));

app.listen(PORTS.dbPool, () => log("INFO", "db-pool", `listening on :${PORTS.dbPool}`));
