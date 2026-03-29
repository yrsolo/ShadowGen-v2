# Commands Reference

## Install

```bash
python -m pip install -e .[dev]
```

## Run API

```bash
uvicorn main:app --app-dir apps/api/src --reload
```

## Test

```bash
python -m pytest
```

## Docs Check

```powershell
powershell -ExecutionPolicy Bypass -File scripts/docs-check.ps1
```
