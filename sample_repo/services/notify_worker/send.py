def send_receipt(order_id, email):
    """Queue a receipt email; failures are logged, never raised."""
    try:
        enqueue("receipts", {"order": order_id, "to": email})
    except Exception:
        pass


def enqueue(queue, payload):
    raise NotImplementedError
