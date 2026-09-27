import { checkout, CheckoutRequest } from "./checkout";

export async function handleCheckoutRequest(request: CheckoutRequest) {
  return checkout(request);
}
