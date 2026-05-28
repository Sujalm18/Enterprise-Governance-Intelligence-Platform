# Contributing

Thanks for improving the Enterprise Governance Intelligence Platform.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/setup/migrate.py
```

## Validation

Run tests before submitting changes:

```powershell
pytest tests/ -v
python scripts/regression/run_regression_tests.py
```

## Engineering Guidelines

- Preserve existing API contracts.
- Keep extraction changes precision-first.
- Do not alter regression expectations to hide failures.
- Keep generated reports under `docs/regression/` or `data/generated/`.
- Keep root-level files limited to repository entry points and project governance files.
