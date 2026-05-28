.PHONY: setup migrate reset backend frontend test regression docker

setup:
	pip install -r requirements.txt

migrate:
	python scripts/setup/migrate.py

reset:
	python scripts/setup/reset_database.py

backend:
	uvicorn backend.app.main:app --reload

frontend:
	streamlit run frontend/app.py

test:
	pytest tests/ -v

regression:
	python scripts/regression/run_regression_tests.py

docker:
	docker compose -f deployment/docker/docker-compose.yml up --build
