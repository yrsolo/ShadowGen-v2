bootstrap:
	python -m pip install -e .[dev]

test:
	python -m pytest

docs-check:
	powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1

run-api:
	uvicorn main:app --app-dir apps/api/src --reload --host 0.0.0.0 --port 8000

release-check:
	powershell -ExecutionPolicy Bypass -File scripts/release-check.ps1
