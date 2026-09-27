import { handleCheckoutRequest } from "../../orders-service/src/index";

export interface CheckoutHttpRequest {
  orderId: string;
  amount: number;
  email: string;
}

// api-gateway is the entry point every request comes through — the
// real edge here (api-gateway -> orders-service) is why api-gateway
// shows up as "affected" whenever anything downstream of it fails.
export async function routeCheckout(req: CheckoutHttpRequest) {
  return handleCheckoutRequest(req);
}
