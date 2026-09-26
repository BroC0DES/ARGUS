// Mock data for the ARGUS console UI kit. Services, edges and logs stand in for
// the backend dependency graph and log index.
window.ARGUS_DATA = {
  services: [
    { id: "gw", name: "api-gateway", rate: "0/hr", x: 12, y: 12, health: "healthy" },
    { id: "orders", name: "orders-service", rate: "12/hr", x: 210, y: 12, health: "degraded", anomaly: true },
    { id: "payment", name: "payment-service", rate: "41/hr", x: 12, y: 108, health: "critical", anomaly: true },
    { id: "ledger", name: "ledger-worker", rate: "3/hr", x: 210, y: 108, health: "healthy" },
    { id: "notify", name: "notify-worker", rate: "0/hr", x: 12, y: 204, health: "healthy" },
    { id: "pgbouncer", name: "pgbouncer", rate: "0/hr", x: 210, y: 204, health: "healthy" },
  ],
  edges: [
    { from: "gw", to: "orders" },
    { from: "orders", to: "payment" },
    { from: "orders", to: "notify" },
    { from: "payment", to: "ledger" },
    { from: "pgbouncer", to: "payment" },
  ],
  tracePath: ["gw", "orders", "payment"],
  blastRadius: [
    { id: "orders", name: "orders-service", health: "degraded", note: "queued retries backing up" },
    { id: "gw", name: "api-gateway", health: "degraded", note: "elevated p99 latency from retries" },
    { id: "ledger", name: "ledger-worker", health: "healthy", note: "ledger entries deferred" },
  ],
  logs: [
    { id: "l1", time: "14:18:02.004", text: "charge attempt order=ord_8802 gateway=stripe", severity: "info" },
    { id: "l2", time: "14:18:02.311", text: "gateway.charge latency 2984ms (p99 threshold 1200ms)", severity: "warn" },
    { id: "l3", time: "14:22:07.318", text: "gateway.charge timeout after 3000ms order=ord_8871", severity: "error", cited: true },
    { id: "l4", time: "14:22:07.402", text: "retry 1/3 order=ord_8871", severity: "warn" },
    { id: "l5", time: "14:22:08.115", text: "charge failed order=ord_8871 code=GATEWAY_TIMEOUT", severity: "error", cited: true },
    { id: "l6", time: "14:22:08.220", text: "ledger entry deferred order=ord_8871", severity: "info" },
    { id: "l7", time: "14:22:09.006", text: "circuit breaker half-open payment->stripe", severity: "warn" },
    { id: "l8", time: "14:22:11.441", text: "charge failed order=ord_8872 code=GATEWAY_TIMEOUT", severity: "error" },
  ],
  incident: {
    service: "payment-service",
    summary:
      "Card charges started timing out at 14:18 when gateway latency passed the 3s client timeout, and the retry path gave up before the gateway recovered.",
    timeline: [
      { time: "14:18:02", label: "First anomaly", severity: "warn" },
      { time: "14:22:07", label: "Escalated", severity: "error" },
      { time: "14:24:40", label: "Root cause identified", severity: "info" },
    ],
    confidentCauseFound: true,
    rootCauseFn: "charge()",
    rootCauseTarget: "the payment gateway",
    rootCauseFailureType: "timeout",
    stats: [
      { label: "Failed charges", value: "1,284", tone: "critical", sourceLogIds: ["l5"] },
      { label: "Error rate", value: "41/hr", sourceLogIds: ["l8"] },
      { label: "First seen", value: "14:18:02", sourceLogIds: ["l2"] },
      { label: "Services touched", value: "3", sourceLogIds: ["l3"] },
    ],
    rootCause: "payment-service · charge() gateway timeout",
    confidence: "high",
    evidence: [
      { id: "l3", label: "log:14:22:07.318" },
      { id: "l5", label: "log:14:22:08.115" },
      { id: "l2", label: "log:14:18:02.311" },
    ],
    code: {
      filename: "services/payment/charge.ts",
      startLine: 142,
      lines: [
        "export async function charge(order: Order) {",
        "  const res = await gateway.charge(order);",
        "  if (!res.ok) throw new GatewayError(res.code);",
        "  return res;",
        "}",
      ],
    },
    fix: {
      filename: "services/payment/charge.ts",
      lines: [
        { text: "  const res = await gateway.charge(order);", kind: "remove" },
        { text: "  const res = await gateway.charge(order, { timeout: 8_000 });", kind: "add" },
        { text: "  if (!res.ok) throw new GatewayError(res.code);", kind: "context" },
        { text: "  await retryWithBackoff(() => gateway.charge(order), { tries: 5 });", kind: "add" },
      ],
    },
  },
  noConfidentIncident: {
    service: "orders-service",
    summary:
      "Order submission latency rose for nine minutes with no clear trigger; three candidate services were checked and none met the confidence threshold.",
    timeline: [
      { time: "09:04:11", label: "First anomaly", severity: "warn" },
      { time: "09:13:02", label: "Investigation closed", severity: "info" },
    ],
    confidentCauseFound: false,
    ruledOut:
      "Ruled out: pgbouncer connection saturation (pool had headroom) and notify-worker backlog (queue depth normal). No service's error pattern matched the latency signature closely enough to call.",
    stats: [
      { label: "Peak p99", value: "1.9s" },
      { label: "Duration", value: "9m" },
      { label: "Candidates checked", value: "3" },
    ],
    evidence: [
      { id: "l1", label: "log:09:04:11.002" },
      { id: "l2", label: "log:09:09:44.118" },
    ],
  },
  serviceCode: {
    payment: {
      filename: "services/payment/charge.ts",
      bridge: "This service threw the timeout seen in the cited logs below.",
      lines: ["const res = await gateway.charge(order);", "if (!res.ok) throw new GatewayError(res.code);"],
      matches: [{ logId: "l3", lineIndex: 0 }, { logId: "l5", lineIndex: 1 }],
    },
    orders: {
      filename: "services/orders/submit.ts",
      bridge: "This service calls payment.charge directly, so its retry loop is where the timeout surfaces.",
      lines: ["const charge = await payment.charge(order);", "return { id: order.id, charge };"],
      matches: [{ logId: "l4", lineIndex: 0 }],
    },
  },
};
