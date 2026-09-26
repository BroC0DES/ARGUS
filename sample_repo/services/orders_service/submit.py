from services.payment_service.charge import charge
from services.notify_worker.send import send_receipt


def submit_order(order):
    """Validate the order, charge the customer, then queue a receipt."""
    if not order.get("items"):
        raise ValueError("empty order")
    charge_result = charge(order)
    send_receipt(order["id"], order["email"])
    return {"id": order["id"], "charge": charge_result}
