# Validation report

Validated on 2026-06-25 in a clean Python environment.

## Passed checks

- Python byte-code compilation for `app`, `scripts`, `training`, and `dashboard.py`
- Ruff static analysis: no errors
- Pytest: 9 tests passed
- Application coverage: 84%
- Synthetic demo generator: 36 images across six classes
- FAISS demo index: 36 vectors using the real `faiss-cpu` backend
- FastAPI/LangGraph `/analyze` smoke test: classification, image retrieval, manual retrieval, risk calculation, persistence, and approval gate completed
- MLflow transfer-learning smoke run: one epoch completed, metrics/artifacts/checkpoint/model logged

## Dataset validation status

The real Magnetic Tile Surface Defect images are not bundled because the author repository does not publish a standard licence file. The dataset source and expected class distribution were cross-checked against the author repository and peer-reviewed descriptions. The included downloader fetches directly from the author repository. The included validator then checks:

- expected total and per-class counts
- readable image files
- SHA-256 hashes
- masks for defective images
- duplicate-file groups

The full binary dataset was not downloaded or republished in this build environment. Run the three dataset commands in `README.md` to download, validate, and split the original data on your machine.

## Important limitation

The included demo classifier is deliberately untrained and exists only to test the software pipeline. Train a checkpoint on the validated real dataset before interpreting predictions.
