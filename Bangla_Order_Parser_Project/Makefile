.PHONY: install run-api run-dashboard test coverage seed docker-up docker-down

install:
	python -m pip install -r requirements.txt

run-api:
	uvicorn app.main:app --reload

run-dashboard:
	streamlit run dashboard.py

test:
	pytest

coverage:
	pytest --cov=app --cov-report=term-missing

seed:
	python scripts/seed_db.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down
