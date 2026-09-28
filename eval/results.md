# ARGUS eval harness results

## TEST split (headline) -- 26 of 26 correct (100.0%)

| id | category | mode | expected | actual | match | verdict | consistent |
|---|---|---|---|---|---|---|---|
| cas-root-01 | cascade | general | root=db-pool label=high | root=db-pool label=high | ✓ | correct and confident | ✓ |
| cas-root-02 | cascade | general | root=db-pool label=high | root=db-pool label=high | ✓ | correct and confident | ✓ |
| clean-03 | clean | specific | healthy | healthy | ✓ | correct abstention | ✓ |
| hsq-01 | healthy_service_question | specific | healthy | healthy | ✓ | correct abstention | ✓ |
| hsq-03 | healthy_service_question | specific | healthy | healthy | ✓ | correct abstention | ✓ |
| lv-cascade-01 | low_volume | general | root=db-pool label=low | root=db-pool label=low | ✓ | correctly uncertain | ✓ |
| me-01 | mixed_errors | general | root=notify-worker label=high | root=notify-worker label=high | ✓ | correct and confident | ✓ |
| me-03 | mixed_errors | general | root=payment-service label=high | root=payment-service label=high | ✓ | correct and confident | ✓ |
| nw-02 | noisy_warnings | specific | healthy | healthy | ✓ | correct abstention | ✓ |
| nw-03 | noisy_warnings | general | healthy | healthy | ✓ | correct abstention | ✓ |
| rs-03 | recently_stopped | general | root=notify-worker label=high | root=notify-worker label=high | ✓ | correct and confident | ✓ |
| rg-root-01 | renamed_graph | general | root=archive-store label=high | root=archive-store label=high | ✓ | correct and confident | ✓ |
| rg-victim-01 | renamed_graph | specific | root=archive-store label=high | root=archive-store label=high | ✓ | correct and confident | ✓ |
| sf-bug1-01 | single_fault | general | root=payment-service label=high | root=payment-service label=high | ✓ | correct and confident | ✓ |
| sf-bug1-03 | single_fault | specific | root=payment-service label=high | root=payment-service label=high | ✓ | correct and confident | ✓ |
| sf-bug2-01 | single_fault | general | root=db-pool label=high | root=db-pool label=high | ✓ | correct and confident | ✓ |
| sl-03 | stale_logs | general | healthy | healthy | ✓ | correct abstention | ✓ |
| se-01 | stray_error | general | root=db-pool label=high | root=db-pool label=high | ✓ | correct and confident | ✓ |
| sfc-01 | subfloor_competitor | general | root=payment-service label=high | root=payment-service label=high | ✓ | correct and confident | ✓ |
| sfc-02 | subfloor_competitor | specific | root=payment-service label=high | root=payment-service label=high | ✓ | correct and confident | ✓ |
| tur3-03 | three_upstream_roots | specific | root=payment-service label=low | root=payment-service label=low | ✓ | correctly uncertain | ✓ |
| tuf-general-02 | two_unrelated_faults | general | root=ledger-worker label=high | root=ledger-worker label=high | ✓ | correct and confident | ✓ |
| tuf-specific-01 | two_unrelated_faults | specific | root=notify-worker label=high | root=notify-worker label=high | ✓ | correct and confident | ✓ |
| tur-02 | two_upstream_roots | general | root=payment-service label=low | root=payment-service label=low | ✓ | correctly uncertain | ✓ |
| tur-specific-01 | two_upstream_roots | specific | root=payment-service label=low | root=payment-service label=low | ✓ | correctly uncertain | ✓ |
| usq-02 | unknown_service_question | specific | unknown_service | unknown_service | ✓ | correct abstention | ✓ |

### Metrics
- Overall accuracy: 26 of 26 (100.0%)
- High-confidence precision: 15 of 15 (100.0%)
- False-confidence rate (wrong among high): 0 of 15 (0.0%)
- Over-abstention (expected high, labeled low): 0 of 15 (0.0%)
- Consistency (2 runs identical): 26 of 26 (100.0%)
- Activity accuracy: 19 of 19 (100.0%)

Per-category:
- cascade: 2 of 2 (100.0%)
- clean: 1 of 1 (100.0%)
- healthy_service_question: 2 of 2 (100.0%)
- low_volume: 1 of 1 (100.0%)
- mixed_errors: 2 of 2 (100.0%)
- noisy_warnings: 2 of 2 (100.0%)
- recently_stopped: 1 of 1 (100.0%)
- renamed_graph: 2 of 2 (100.0%)
- single_fault: 3 of 3 (100.0%)
- stale_logs: 1 of 1 (100.0%)
- stray_error: 1 of 1 (100.0%)
- subfloor_competitor: 2 of 2 (100.0%)
- three_upstream_roots: 1 of 1 (100.0%)
- two_unrelated_faults: 2 of 2 (100.0%)
- two_upstream_roots: 2 of 2 (100.0%)
- unknown_service_question: 1 of 1 (100.0%)

Calibration by score bucket:
- <0.5: 7 of 7 correct (100.0%)
- 0.5-0.65: 2 of 2 correct (100.0%)
- 0.65-0.8: 2 of 2 correct (100.0%)
- >0.8: 15 of 15 correct (100.0%)

## TUNE split (tuning) -- 26 of 26 correct (100.0%)

| id | category | mode | expected | actual | match | verdict | consistent |
|---|---|---|---|---|---|---|---|
| cas-victim-01 | cascade | specific | root=db-pool label=high | root=db-pool label=high | ✓ | correct and confident | ✓ |
| cas-victim-02 | cascade | specific | root=db-pool label=high | root=db-pool label=high | ✓ | correct and confident | ✓ |
| clean-01 | clean | general | healthy | healthy | ✓ | correct abstention | ✓ |
| clean-02 | clean | specific | healthy | healthy | ✓ | correct abstention | ✓ |
| hsq-02 | healthy_service_question | specific | healthy | healthy | ✓ | correct abstention | ✓ |
| lv-dbexh-01 | low_volume | general | root=db-pool label=low | root=db-pool label=low | ✓ | correctly uncertain | ✓ |
| lv-paytimeout-01 | low_volume | specific | root=payment-service label=low | root=payment-service label=low | ✓ | correctly uncertain | ✓ |
| me-02 | mixed_errors | specific | root=ledger-worker label=high | root=ledger-worker label=high | ✓ | correct and confident | ✓ |
| nw-01 | noisy_warnings | general | healthy | healthy | ✓ | correct abstention | ✓ |
| rs-01 | recently_stopped | general | root=db-pool label=high | root=db-pool label=high | ✓ | correct and confident | ✓ |
| rs-02 | recently_stopped | specific | root=payment-service label=high | root=payment-service label=high | ✓ | correct and confident | ✓ |
| rg-single-01 | renamed_graph | general | root=billing-unit label=high | root=billing-unit label=high | ✓ | correct and confident | ✓ |
| sf-bug1-02 | single_fault | general | root=payment-service label=high | root=payment-service label=high | ✓ | correct and confident | ✓ |
| sf-bug2-02 | single_fault | specific | root=db-pool label=high | root=db-pool label=high | ✓ | correct and confident | ✓ |
| sf-bug2-03 | single_fault | general | root=db-pool label=high | root=db-pool label=high | ✓ | correct and confident | ✓ |
| sl-01 | stale_logs | general | healthy | healthy | ✓ | correct abstention | ✓ |
| sl-02 | stale_logs | specific | healthy | healthy | ✓ | correct abstention | ✓ |
| se-02 | stray_error | specific | root=db-pool label=high | root=db-pool label=high | ✓ | correct and confident | ✓ |
| se-03 | stray_error | general | root=payment-service label=high | root=payment-service label=high | ✓ | correct and confident | ✓ |
| sfc-03 | subfloor_competitor | specific | root=notify-worker label=low | root=notify-worker label=low | ✓ | correctly uncertain | ✓ |
| tur3-01 | three_upstream_roots | general | root=payment-service label=low | root=payment-service label=low | ✓ | correctly uncertain | ✓ |
| tur3-02 | three_upstream_roots | general | root=payment-service label=low | root=payment-service label=low | ✓ | correctly uncertain | ✓ |
| tuf-general-01 | two_unrelated_faults | general | root=ledger-worker label=high | root=ledger-worker label=high | ✓ | correct and confident | ✓ |
| tur-01 | two_upstream_roots | general | root=payment-service label=low | root=payment-service label=low | ✓ | correctly uncertain | ✓ |
| usq-01 | unknown_service_question | specific | unknown_service | unknown_service | ✓ | correct abstention | ✓ |
| usq-03 | unknown_service_question | specific | unknown_service | unknown_service | ✓ | correct abstention | ✓ |

### Metrics
- Overall accuracy: 26 of 26 (100.0%)
- High-confidence precision: 12 of 12 (100.0%)
- False-confidence rate (wrong among high): 0 of 12 (0.0%)
- Over-abstention (expected high, labeled low): 0 of 12 (0.0%)
- Consistency (2 runs identical): 26 of 26 (100.0%)
- Activity accuracy: 18 of 18 (100.0%)

Per-category:
- cascade: 2 of 2 (100.0%)
- clean: 2 of 2 (100.0%)
- healthy_service_question: 1 of 1 (100.0%)
- low_volume: 2 of 2 (100.0%)
- mixed_errors: 1 of 1 (100.0%)
- noisy_warnings: 1 of 1 (100.0%)
- recently_stopped: 2 of 2 (100.0%)
- renamed_graph: 1 of 1 (100.0%)
- single_fault: 3 of 3 (100.0%)
- stale_logs: 2 of 2 (100.0%)
- stray_error: 2 of 2 (100.0%)
- subfloor_competitor: 1 of 1 (100.0%)
- three_upstream_roots: 2 of 2 (100.0%)
- two_unrelated_faults: 1 of 1 (100.0%)
- two_upstream_roots: 1 of 1 (100.0%)
- unknown_service_question: 2 of 2 (100.0%)

Calibration by score bucket:
- <0.5: 8 of 8 correct (100.0%)
- 0.5-0.65: 5 of 5 correct (100.0%)
- 0.65-0.8: 2 of 2 correct (100.0%)
- >0.8: 11 of 11 correct (100.0%)

## Failures (test split, wrong-but-confident first)
None.
## Original-vs-sanitized codebase gap (test split, sanitized-repo scenarios only)
- Sanitized accuracy: 24 of 24 (100.0%)
- Original (commented) accuracy: 24 of 24 (100.0%)
- Gap: 0.0 percentage points

