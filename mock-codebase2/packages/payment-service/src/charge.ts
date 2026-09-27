import { chargeViaGateway } from "./gateway";
import { recordTransaction } from "../../db-pool/src/pool";

export interface Order {
  id: string;
  amount: number;
}

export class GatewayError extends Error {
  code: string;
  constructor(code: string) {
    super(`Gateway call failed with code: ${code}`);
    this.code = code;
  }
}

export async function charge(order: Order) {
  const res = await chargeViaGateway(order.id);
  if (!res.ok) throw new GatewayError(res.code ?? "UNKNOWN");
  // Real dependency on db-pool — if the pool is exhausted, this call
  // throws PoolError, which is how BUG #2 reaches payment-service.
  await recordTransaction(order.id, order.amount);
  return res;
}
