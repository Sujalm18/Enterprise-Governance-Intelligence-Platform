# Backend

FastAPI backend for ingestion, OCR fallback, governance classification, ontology-aware extraction, persistence, and report APIs.

## Run

```powershell
uvicorn backend.app.main:app --reload
```

## Database

```powershell
python scripts/setup/migrate.py
python scripts/setup/reset_database.py
```

## Tests

```powershell
pytest tests/unit tests/integration -v
```
