# Getting Started

## Requirements

- Python 3.11+
- pip

## Quick Start

```bash
python -m pip install -e .[dev]
uvicorn main:app --app-dir apps/api/src --reload
```

On Windows PowerShell you can also run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

## What To Open

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Current Scope

Right now the processing pipeline is implemented for transparent PNG inputs. Automatic background removal from ordinary photos is intentionally left as the next extension step.

## Read Next

- [Repository Map](repository-map.md)
- [Commands Reference](../reference/commands.md)
- [API Reference](../reference/api.md)
