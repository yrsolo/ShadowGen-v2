FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY apps ./apps

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--app-dir", "apps/api/src", "--host", "0.0.0.0", "--port", "8000"]
