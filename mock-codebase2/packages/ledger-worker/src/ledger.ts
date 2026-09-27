import { writeLedgerEntry } from "../../db-pool/src/pool";

export interface LedgerRequest {
  orderId: string;
  amount: number;
}

// ledger-worker depends on db-pool directly — this is the real edge
// that makes it part of the cascading-failure scenario. If db-pool is
// exhausted (BUG #2), this call fails too.
export async function recordLedgerEntry(request: LedgerRequest) {
  return writeLedgerEntry(request.orderId, request.amount);
}
