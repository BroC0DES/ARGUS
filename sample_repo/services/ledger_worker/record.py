LEDGER_TABLE = "ledger"


def record_entry(order_id, amount):
    """Append a ledger row for a settled charge (own append-only writer, no shared pool)."""
    with open("/var/ledger/entries.log", "a") as f:
        f.write(f"{LEDGER_TABLE},{order_id},{amount}\n")
