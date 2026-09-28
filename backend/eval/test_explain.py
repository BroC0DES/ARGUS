"""Exact-match test for explain(). Run from the backend folder:
    python -m eval.test_explain
Prints PASS or FAIL. Makes no model calls."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from explain import explain  # noqa: E402

TARGET = (
    "ARGUS saw errors in 4 services, but most were just victims. "
    "payment-service, ledger-worker and orders-service all depend on db-pool, "
    "and db-pool was failing too. So their errors were most likely caused by db-pool. "
    "db-pool depends on nothing that was failing, and it had 90 errors in 5 minutes, "
    "so ARGUS named it the root cause. Confidence is high (0.91) because the evidence "
    "was strong, only one possible cause was left, and matching code was found."
)

CASCADE = dict(
    failing_services=["db-pool", "payment-service", "ledger-worker", "orders-service"],
    root="db-pool",
    candidates=["db-pool"],
    symptoms=["payment-service", "ledger-worker", "orders-service"],
    root_errors=90,
    label="high",
    score=0.91,
    signals=dict(evidence=1.0, dominance=1.0, relevance=0.62),
    is_eval=False,
)

out = explain(CASCADE).replace("**", "")
if out == TARGET:
    print("PASS")
    sys.exit(0)
print("FAIL")
print(out)
sys.exit(1)
