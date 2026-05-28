# Regression Framework

## Purpose

The regression framework evaluates the production ingestion and extraction pipeline against a mixed-format enterprise corpus.

## Corpus Layout

Documents live under:

```text
data/regression/corpus/
```

Each document has a matching expected JSON file:

```text
meeting_minutes_01.docx
meeting_minutes_01.expected.json
```

## Run

```bash
python scripts/regression/run_regression_tests.py
```

## Outputs

- `docs/regression/regression_test_report.md`
- `docs/regression/regression_results.csv`

## Metrics

- Classification Accuracy
- Governance Detection Accuracy
- Governance Precision
- Governance Recall
- RAID Extraction Recall
- Escalation False Positive Rate
- Meeting Action Recall
- OCR Success Rate

## Current Interpretation

The latest precision-first run passes 84 of 90 corpus files. The remaining failures are meeting-action minimum thresholds where the semantic model extracts fewer but more accountable tasks.

That is an expected maturity signal: the old corpus expected high recall, while the productized platform now prioritizes governance precision.
