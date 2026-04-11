# API App

Path:

- `apps/api/src/shadowgen_api`

Entry point:

- `apps/api/src/shadowgen_api/main.py`

Responsibilities:

- expose HTTP endpoints
- validate uploads and requests
- compose application use cases and adapter wiring
- expose diagnostics, runtime config, and worker action endpoints

Main files:

- `main.py` - FastAPI app factory
- `config.py` - API runtime config
- `deps.py` - dependency wiring
- `routes/assets.py`
- `routes/jobs.py`
- `routes/system.py`
- `routes/health.py`

Not responsible for:

- ML inference
- queue consumption
- artifact generation
