// Synthetic entry service for the renamed_graph eval category. Same shape as
// api-gateway in mock-codebase2 (single entry point, no callers), just under
// different names, to prove the pipeline's routing/partitioning never
// hardcodes a service name.
import { routeRequest } from "../../core-router/src/router";

export async function handleRequest(orderId: string) {
  return routeRequest(orderId);
}
