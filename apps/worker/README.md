# Worker App

Background worker for ShadowGen v2.

Responsibilities:

- consume jobs
- execute pipeline
- update job status
- isolate live legacy ML integration behind adapters

Non-responsibilities:

- no HTTP API
- no frontend logic
