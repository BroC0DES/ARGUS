import { charge, Order } from "./charge";

export async function handleChargeRequest(order: Order) {
  return charge(order);
}
