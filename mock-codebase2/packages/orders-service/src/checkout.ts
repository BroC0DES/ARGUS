import { handleChargeRequest } from "../../payment-service/src/index";
import { saveOrder } from "../../db-pool/src/pool";
import { queueConfirmationEmail } from "../../notify-worker/src/notify";

export interface CheckoutRequest {
  orderId: string;
  amount: number;
  email: string;
}

export async function checkout(request: CheckoutRequest) {
  // Real edge #1: orders-service -> payment-service
  const paymentResult = await handleChargeRequest({
    id: request.orderId,
    amount: request.amount,
  });

  // Real edge #2: orders-service -> db-pool
  // If db-pool is exhausted (BUG #2), this can fail even when payment
  // itself succeeded — a second, independent way orders-service can
  // show an error, distinct from a payment failure.
  await saveOrder(request.orderId);

  // Real edge #3: orders-service -> notify-worker
  await queueConfirmationEmail({ orderId: request.orderId, email: request.email });

  return paymentResult;
}
