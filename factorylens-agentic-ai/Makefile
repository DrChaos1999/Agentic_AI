.PHONY: install demo dataset train index api dashboard test mlflow

install:
	python -m pip install -r requirements-dev.txt

demo:
	python scripts/generate_demo_data.py
	python scripts/build_demo_index.py

dataset:
	python scripts/download_dataset.py
	python scripts/validate_dataset.py
	python scripts/prepare_dataset.py

train:
	python -m training.train

index:
	python -m training.build_faiss_index --include-val

api:
	uvicorn app.main:app --reload

dashboard:
	streamlit run dashboard.py

test:
	pytest --cov=app --cov-report=term-missing

mlflow:
	mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
