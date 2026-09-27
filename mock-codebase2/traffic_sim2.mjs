#!/usr/bin/env node
// Replaces pre-written log lines with real HTTP traffic: fires actual checkout
// requests at api-gateway on an interval. Whatever genuinely happens downstream
// (a real gateway timeout, a real pool exhaustion, or a real success) is what
// gets logged -- by each service's own server.ts, via shared/logger.ts -- not a
// scripted line. Run with: node traffic_sim2.mjs
import { setTimeout as delay } from "node:timers/promises";

const API_GATEWAY = process.env.ARGUS_API_GATEWAY_URL || "http://localhost:4000";
const INTERVAL_MS = Number(process.env.TRAFFIC_INTERVAL_MS || 800);
// pool.ts's withConnection() holds a "connection" for a near-instant, artificial-
// delay-free critical section, so genuine pool exhaustion (BUG #2) only shows up
// when multiple requests' db-pool calls land in that same instant -- one request
// every INTERVAL_MS never overlaps with itself. BURST_SIZE fires that many
// checkouts concurrently each tick, which is a more realistic simulation of real
// concurrent users anyway (real traffic doesn't arrive one at a time, evenly
// spaced) and is what actually exercises maxConnections.
const BURST_SIZE = Number(process.env.TRAFFIC_BURST_SIZE || 4);

function orderId() {
  return "ord_" + Math.floor(1000 + Math.random() * 9000);
}

async function fireOne() {
  const id = orderId();
  const body = { orderId: id, amount: Math.floor(Math.random() * 400) + 5, email: `${id}@example.com` };
  try {
    const res = await fetch(`${API_GATEWAY}/checkout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    console.log(`[traffic] order=${id} -> HTTP ${res.status}`);
  } catch (e) {
    console.log(`[traffic] order=${id} -> request failed: ${e.message}`);
  }
}

console.log(`[traffic] sending ${BURST_SIZE} real, concurrent checkout requests to ${API_GATEWAY} every ~${INTERVAL_MS}ms`);

async function main() {
  for (;;) {
    for (let i = 0; i < BURST_SIZE; i++) fireOne(); // fire-and-forget, genuinely concurrent
    await delay(INTERVAL_MS);
  }
}
main();
