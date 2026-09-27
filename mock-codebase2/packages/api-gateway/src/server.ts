// Live HTTP wrapper for api-gateway -- the entry point traffic_sim2.mjs hits.
// router.ts's own direct import of handleCheckoutRequest is left untouched on
// disk (still what the Code Indexer finds for the api-gateway -> orders-service
// edge); the actual live call is real HTTP to orders-service's own process.
import express from "express";
import { URLS, PORTS } from "../../../shared/ports";
import { log } from "../../../shared/logger";

const app = express();
app.use(express.json());

app.post("/checkout", async (req, res) => {
  const { orderId, amount, email } = req.body as { orderId: string; amount: number; email: string };
  log("INFO", "api-gateway", `request routed order=${orderId}`);
  try {
    const r = await fetch(`${URLS.ordersService}/checkout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ orderId, amount, email }),
    });
    const data = await r.json().catch(() => ({}));
    res.status(r.status).json(data);
  } catch {
    log("WARN", "api-gateway", `elevated error rate downstream order=${orderId}`);
    res.status(502).json({ ok: false });
  }
});

app.listen(PORTS.apiGateway, () => log("INFO", "api-gateway", `listening on :${PORTS.apiGateway}`));
