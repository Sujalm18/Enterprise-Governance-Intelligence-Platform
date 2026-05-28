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

## Summarization

- Mock-mode executive summaries are template-driven and not full narrative synthesis.
- The summary does not yet expose the full internal ontology as separate UI sections.

## Persistence and Deployment

- SQLite is appropriate for local and portfolio demos but not multi-user production.
- Migrations are lightweight and should eventually move to Alembic.
- Authentication and authorization are not production-grade.

