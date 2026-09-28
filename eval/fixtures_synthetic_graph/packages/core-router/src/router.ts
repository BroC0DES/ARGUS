// Synthetic hub service: same role as orders-service in mock-codebase2 --
// calls two downstream services, one of which (billing-unit) itself depends
// on the other (archive-store), so a real cascade edge exists here too.
import { chargeBilling } from "../../billing-unit/src/billing";
import { writeArchive } from "../../archive-store/src/archive";

export async function routeRequest(orderId: string) {
  await chargeBilling(orderId);
  return writeArchive(orderId);
}
