from services.db_pool.pool import get_connection
from services.ledger_worker.record import record_entry

GATEWAY_TIMEOUT_MS = 3000


def charge(order):
    """Charge the card through the payment gateway (3s client timeout)."""
    res = gateway_call(order, timeout_ms=GATEWAY_TIMEOUT_MS)
    if not res["ok"]:
        raise GatewayError(res["code"])
    record_entry(order["id"], res["amount"])
    return res


def gateway_call(order, timeout_ms):
    """POST to the external card gateway; raises on client timeout."""
    conn = get_connection()
    return conn.post("/v1/charges", order, timeout=timeout_ms / 1000)


class GatewayError(Exception):
    pass
