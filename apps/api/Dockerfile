FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml requirements.txt README.md /app/
COPY apps/api/src /app/apps/api/src
COPY apps/worker/src /app/apps/worker/src
COPY packages /app/packages

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir .

EXPOSE 8080

CMD ["sh", "-c", "python -m uvicorn shadowgen_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
