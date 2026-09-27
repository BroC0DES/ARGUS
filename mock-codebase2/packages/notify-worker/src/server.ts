// Live HTTP wrapper for notify-worker. queueConfirmationEmail() from notify.ts is
// called completely unchanged -- notify-worker has no dependencies of its own
// (deliberately, per notify.ts's own comment), so there's no shared-state issue
// here and no reason to reimplement anything.
import express from "express";
import { queueConfirmationEmail } from "./notify";
import { PORTS } from "../../../shared/ports";
import { log } from "../../../shared/logger";

const app = express();
app.use(express.json());

app.post("/queue", async (req, res) => {
  const { orderId, email } = req.body as { orderId: string; email: string };
  const r = await queueConfirmationEmail({ orderId, email });
  log("INFO", "notify-worker", `confirmation email queued order=${orderId}`);
  res.json(r);
});

app.listen(PORTS.notifyWorker, () => log("INFO", "notify-worker", `listening on :${PORTS.notifyWorker}`));
