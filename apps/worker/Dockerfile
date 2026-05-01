FROM python:3.12-slim

ARG SHADOWGEN_GIT_BRANCH=""
ARG SHADOWGEN_GIT_COMMIT=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SHADOWGEN_GIT_BRANCH=${SHADOWGEN_GIT_BRANCH} \
    SHADOWGEN_GIT_COMMIT=${SHADOWGEN_GIT_COMMIT}

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt README.md /app/
COPY apps/api/src /app/apps/api/src
COPY apps/worker/src /app/apps/worker/src
COPY packages /app/packages

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir .

EXPOSE 8081

CMD ["python", "-m", "shadowgen_worker.main"]
