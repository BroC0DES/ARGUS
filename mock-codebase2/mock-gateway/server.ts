// Stand-in for the real external payment gateway that gateway.ts's chargeViaGateway()
// calls. The original code pointed at "https://mock-gateway.internal/charge", a
// domain that doesn't resolve -- every call would fail on DNS lookup almost
// instantly, regardless of BUG #1's timeoutMs value, so editing that value would
// never visibly change anything. This is the one change made outside a bug file
// or a thin server wrapper: gateway.ts's fetch target was repointed at this real,
// running local server (see gateway.ts's comment at that line). BUG #1's
// `timeoutMs` constant itself, and the surrounding decision logic, are untouched.
//
// Latency here straddles the 3000ms/8000ms line on purpose, so the *unmodified*
// AbortController in gateway.ts genuinely times out most calls at 3000ms and
// genuinely succeeds most calls at 8000ms -- the outcome is a real race against
// this server's real response time, not a canned INFO/ERROR line.
import * as http from "http";
import { PORTS } from "../shared/ports";

function randomDelayMs(): number {
  // Matches gateway.ts's own comment ("p99 latency drifts above 3000ms under
  // load"): most requests are comfortably fast; a real tail of load spikes pushes
  // some past 3000ms (making BUG #1's timeout fire often, not universally); only a
  // rare, genuine p99-style outlier pushes past 8000ms (BUG #1's fix), so "fixed"
  // means "almost always succeeds now," matching a real gateway, not "never fails."
  const r = Math.random();
  if (r < 0.03) return 7500 + Math.random() * 1500; // ~3%: rare severe outlier (7.5-9s)
  if (r < 0.38) return 2500 + Math.random() * 5000; // ~35%: real load-spike tail (2.5-7.5s)
  return 300 + Math.random() * 2200; // ~62%: comfortably fast (0.3-2.5s)
}

const server = http.createServer((req, res) => {
  if (req.method !== "POST") {
    res.writeHead(404).end();
    return;
  }
  const delay = randomDelayMs();
  setTimeout(() => {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ ok: true }));
  }, delay);
});

server.listen(PORTS.mockGateway, () => {
  console.log(`[mock-gateway] listening on :${PORTS.mockGateway}`);
});
