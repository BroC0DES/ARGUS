// Synthetic victim service: same role as payment-service in mock-codebase2 --
// depends on the shared downstream store, so it fails whenever that store
// does (a real cascade edge, not a coincidence).
import { writeArchive } from "../../archive-store/src/archive";

export async function chargeBilling(orderId: string) {
  return writeArchive(orderId);
}
