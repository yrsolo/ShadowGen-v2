bootstrap:
	python -m pip install -e .[dev]

install-local:
	cmd /c scripts\install-local-deps.cmd

test:
	python -m pytest

docs-check:
	powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1

run-api:
	python tools/dev/run_local.py

run-worker:
	python -m shadowgen_worker.main

run-local-test:
	cmd /c scripts\run-local-services.cmd

run-local-containers:
	cmd /c scripts\run-local-containers.cmd

release-check:
	powershell -ExecutionPolicy Bypass -File scripts/release-check.ps1
