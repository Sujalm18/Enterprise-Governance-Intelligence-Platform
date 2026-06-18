# Known Limitations

This document is intentionally candid. The platform is strong enough for portfolio demonstration and engineering review, but it is not a fully validated enterprise product.

## Semantic Modeling

- Semantic clustering is heuristic and still evolving.
- Some related governance concepts may be over-merged when they share broad root themes.
- Some weak but valid action items may be omitted because the system is precision-biased.
- The ontology is incomplete for audit, compliance, procurement, and change-control governance.

## OCR

- OCR fallback is validated against the local corpus, not a broad scanned-document benchmark.
- EasyOCR performance varies by CPU/GPU availability.
- Handwriting and low-resolution scans remain high risk.

## Evaluation

- The regression corpus is synthetic and may encode count-based expectations.
- Manual PMO validation is still required.
- Meeting action recall now reflects conservative action legitimacy, which may underperform old high-recall thresholds.

**Regression suite measures threshold-clearing, not extraction accuracy.**
The .expected.json thresholds (e.g. raid_items_min) are coarse per-category minimums, not content-matched ground truth. A manual check against raid_register_10.txt found 17 actual RAID items against a threshold of 5 - meaning extraction could miss the majority of real items in a document and still pass. The current 100% pass rate (see regression_test_report.md) reflects these coarse thresholds, not verified per-item extraction quality. Per-item ground truth evaluation against manually annotated documents is a planned improvement, not yet implemented.

## Summarization

- Mock-mode executive summaries are template-driven and not full narrative synthesis.
- The summary does not yet expose the full internal ontology as separate UI sections.

## Persistence and Deployment

- SQLite is appropriate for local and portfolio demos but not multi-user production.
- Migrations are lightweight and should eventually move to Alembic.
- Authentication and authorization are not production-grade.

