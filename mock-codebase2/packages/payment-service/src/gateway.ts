import { URLS } from "../../../shared/ports";

export interface GatewayResponse {
  ok: boolean;
  code?: string;
}

// Mock external payment gateway client.
// NOTE: originally pointed at "https://mock-gateway.internal/charge", a domain that
// doesn't resolve -- every call failed on DNS lookup near-instantly regardless of
// BUG #1's timeoutMs below, so editing it would never change real behavior. Repointed
// at a real local server (mock-codebase2/mock-gateway/server.ts) with randomized
// latency straddling 3000ms/8000ms, so the timeout below is a genuine race against a
// real response time. This is the only line changed outside this file's BUG #1 block.
export async function chargeViaGateway(orderId: string): Promise<GatewayResponse> {
  // ============================================================
  // BUG #1 — PAYMENT TIMEOUT
  // TO BREAK (cause the failure): leave this at 3000
  // TO FIX (stop the failure):   change this to 8000
  // The real gateway's p99 latency drifts above 3000ms under load,
  // so a 3000ms timeout here fires too eagerly. 8000ms gives it
  // enough headroom.
  // ============================================================
  const timeoutMs = 3000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${URLS.mockGateway}/charge`, {
      method: "POST",
      body: JSON.stringify({ orderId }),
      signal: controller.signal,
    });
    return { ok: res.ok, code: res.ok ? undefined : "GATEWAY_ERROR" };
  } catch (err) {
    return { ok: false, code: "GATEWAY_TIMEOUT" };
  } finally {
    clearTimeout(timer);
  }
}

