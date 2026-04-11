

# ShadowGen-v2: инструкция на полную перестройку репозитория

## 1. Контекст и цель

Нужно перестроить репозиторий `ShadowGen-v2` с нуля в чистую, расширяемую архитектуру.

Важно:

* **старое ML-ядро не переписывать**;
* **старую бизнес-логику обработки пока не менять существенно**;
* на первом этапе считать старую ML-часть **чёрным ящиком**;
* новая версия должна дать:

  * чистую архитектуру;
  * понятные контракты;
  * модульность;
  * возможность позже заменить отдельные звенья обработки;
  * возможность сделать новый GUI/frontend;
  * возможность потом переписать ML-ядро без переделки всей системы.

На первом этапе новая система должна строиться вокруг следующей идеи:

* новый `web`;
* новый `api`;
* новый `worker`;
* новый набор `contracts`;
* новый `pipeline interface`;
* старое ML-ядро подключается через **тонкий legacy adapter**.

---

## 2. Архитектурные принципы

### 2.1. Общая модель

Система должна быть организована так:

```text
Web UI -> API -> Job Store / Queue -> Worker -> Pipeline Interface -> Legacy ML Adapter -> Old ML Core
```

### 2.2. Жёсткие правила

1. **Monorepo**
   Один репозиторий для `web`, `api`, `worker`, `shared packages`.

2. **API не делает inference**
   API только:

   * принимает запросы;
   * валидирует;
   * создаёт job;
   * возвращает status/result.

3. **Worker делает обработку**
   Worker:

   * читает job;
   * вызывает pipeline;
   * сохраняет result;
   * обновляет status.

4. **ML-ядро пока black box**
   Новая система не должна зависеть от внутренней реализации старого ML-кода.
   Только адаптер знает, как дёргать legacy pipeline.

5. **Контракты централизованы**
   Все DTO и схемы должны лежать в одном месте.

6. **UI ничего не знает о ML**
   UI работает только через API.

7. **Будущая замена звеньев должна быть дешёвой**
   Pipeline строится на интерфейсах и адаптерах.

8. **Никакой доменной логики в HTTP-роутах**
   Роуты только вызывают use cases.

9. **Сразу готовим место под многоуровневый кэш**
   Но на первом этапе можно ограничиться интерфейсами и простым in-memory/null cache.

---

## 3. Что делаем на первом этапе

### Делаем

* новый скелет репозитория;
* новый README;
* документацию по архитектуре;
* базовые доменные модели;
* базовые contracts;
* базовые use cases;
* pipeline interfaces;
* legacy adapter;
* skeleton API;
* skeleton worker;
* skeleton frontend;
* место под infra и tests.

### Не делаем пока

* полную перепись ML-ядра;
* сложную референсно-тестовую систему;
* микросервисы;
* разнос по разным репозиториям;
* premature optimization;
* сложный production-grade infra код.

---

## 4. Целевая структура репозитория

Нужно привести репозиторий к такой структуре:

```text
ShadowGen-v2/
├── README.md
├── pyproject.toml
├── .gitignore
├── .env.example
│
├── apps/
│   ├── api/
│   │   ├── README.md
│   │   └── src/
│   │       └── shadowgen_api/
│   │           ├── __init__.py
│   │           ├── main.py
│   │           ├── config.py
│   │           ├── deps.py
│   │           ├── routes/
│   │           │   ├── __init__.py
│   │           │   ├── health.py
│   │           │   ├── jobs.py
│   │           │   └── assets.py
│   │           ├── schemas/
│   │           │   ├── __init__.py
│   │           │   ├── api_requests.py
│   │           │   └── api_responses.py
│   │           └── services/
│   │               ├── __init__.py
│   │               └── job_service.py
│   │
│   ├── worker/
│   │   ├── README.md
│   │   └── src/
│   │       └── shadowgen_worker/
│   │           ├── __init__.py
│   │           ├── main.py
│   │           ├── config.py
│   │           ├── loop.py
│   │           └── executor.py
│   │
│   └── web/
│       ├── README.md
│       ├── package.json
│       ├── tsconfig.json
│       ├── next.config.js
│       └── src/
│           ├── app/
│           │   ├── page.tsx
│           │   ├── layout.tsx
│           │   └── jobs/
│           │       └── [jobId]/
│           │           └── page.tsx
│           ├── components/
│           │   ├── upload-form.tsx
│           │   ├── angle-slider.tsx
│           │   └── result-view.tsx
│           └── lib/
│               ├── api-client.ts
│               └── types.ts
│
├── packages/
│   ├── contracts/
│   │   └── src/
│   │       └── shadowgen_contracts/
│   │           ├── __init__.py
│   │           ├── enums.py
│   │           ├── common.py
│   │           ├── render.py
│   │           ├── jobs.py
│   │           └── errors.py
│   │
│   ├── domain/
│   │   └── src/
│   │       └── shadowgen_domain/
│   │           ├── __init__.py
│   │           ├── entities.py
│   │           ├── value_objects.py
│   │           ├── statuses.py
│   │           └── exceptions.py
│   │
│   ├── application/
│   │   └── src/
│   │       └── shadowgen_application/
│   │           ├── __init__.py
│   │           ├── dto.py
│   │           ├── ports.py
│   │           └── use_cases/
│   │               ├── __init__.py
│   │               ├── create_job.py
│   │               ├── get_job.py
│   │               └── process_job.py
│   │
│   ├── pipeline/
│   │   └── src/
│   │       └── shadowgen_pipeline/
│   │           ├── __init__.py
│   │           ├── interfaces.py
│   │           ├── context.py
│   │           └── cache_keys.py
│   │
│   └── adapters/
│       └── src/
│           └── shadowgen_adapters/
│               ├── __init__.py
│               ├── legacy_pipeline/
│               │   ├── __init__.py
│               │   ├── adapter.py
│               │   └── mapper.py
│               ├── storage/
│               │   ├── __init__.py
│               │   └── memory_asset_store.py
│               ├── jobs/
│               │   ├── __init__.py
│               │   └── memory_job_repository.py
│               └── queue/
│                   ├── __init__.py
│                   └── memory_job_queue.py
│
├── docs/
│   ├── README.md
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── repository-structure.md
│   │   ├── pipeline.md
│   │   ├── caching.md
│   │   └── decisions.md
│   ├── contracts/
│   │   ├── api.md
│   │   ├── jobs.md
│   │   └── ml-black-box.md
│   └── roadmap/
│       ├── bootstrap-plan.md
│       └── migration-phases.md
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── smoke/
│       └── README.md
│
└── tools/
    └── dev/
        └── run_local.py
```

---

## 5. Базовые решения по технологиям

### Python

* Python 3.11+
* Pydantic v2
* FastAPI
* Uvicorn

### Frontend

* Next.js
* TypeScript

### На первом этапе для простоты

* in-memory job repository;
* in-memory asset store;
* in-memory queue;
* mock or placeholder wiring для локального запуска.

Потом это можно заменить на Redis / Postgres / S3 / YDB / YMQ, не меняя application layer.

---

## 6. Содержимое README.md

Нужно полностью заменить текущий README на новый.

### Новый README.md

````md
# ShadowGen v2

ShadowGen v2 — новая версия ShadowGEN с чистой архитектурой, расширяемым пайплайном и новым интерфейсом.

## Цель проекта

Перестроить систему вокруг существующего ML-ядра без повторного закапывания в legacy.

На первом этапе:
- старое ML-ядро используется как black box;
- новый код отвечает за архитектуру, API, worker, contracts, frontend и инфраструктурные точки расширения;
- внутренняя логика обработки изображения пока не переписывается;
- архитектура сразу строится так, чтобы потом можно было без боли заменить отдельные звенья пайплайна или всё ML-ядро целиком.

## Основные принципы

1. Monorepo, но не свалка
2. API не делает inference
3. Worker обрабатывает job
4. ML пока black box
5. Контракты централизованы
6. UI не знает внутренностей ML
7. Пайплайн строится на интерфейсах и адаптерах

## High-level схема

```text
Web UI -> API -> Queue / Job Store -> Worker -> Pipeline Interface -> Legacy ML Adapter -> Old ML Core
````

## Структура репозитория

* `apps/api` — FastAPI backend
* `apps/worker` — background worker
* `apps/web` — frontend
* `packages/contracts` — общие контракты
* `packages/domain` — доменные сущности
* `packages/application` — use cases и порты
* `packages/pipeline` — интерфейсы пайплайна
* `packages/adapters` — адаптеры, включая legacy pipeline
* `docs` — документация
* `tests` — тесты

## Статус текущего этапа

Сейчас проект находится на этапе архитектурного bootstrap:

* новый каркас системы;
* новый набор contracts;
* новый API/worker/frontend skeleton;
* старое ML-ядро подключается как black box adapter.

## Документация

* `docs/architecture/overview.md`
* `docs/architecture/repository-structure.md`
* `docs/architecture/pipeline.md`
* `docs/contracts/ml-black-box.md`
* `docs/roadmap/bootstrap-plan.md`

## Что не делаем прямо сейчас

* не переписываем ML-ядро;
* не строим сложную reference/golden test system;
* не режем проект на много репозиториев;
* не делаем premature microservices.

````

---

## 7. Документация, которую нужно создать

### `docs/README.md`

```md
# Documentation Map

## Architecture
- `architecture/overview.md`
- `architecture/repository-structure.md`
- `architecture/pipeline.md`
- `architecture/caching.md`
- `architecture/decisions.md`

## Contracts
- `contracts/api.md`
- `contracts/jobs.md`
- `contracts/ml-black-box.md`

## Roadmap
- `roadmap/bootstrap-plan.md`
- `roadmap/migration-phases.md`
````

---

### `docs/architecture/overview.md`

```md
# Architecture Overview

ShadowGen v2 строится как модульная система с разделением на:

- Web UI
- API
- Worker
- Pipeline
- Legacy ML Adapter
- Old ML Core

## High-level flow

1. Пользователь загружает изображение через Web UI
2. API создаёт job
3. Job попадает в очередь / store
4. Worker забирает job
5. Worker вызывает pipeline
6. Pipeline вызывает legacy adapter
7. Legacy adapter вызывает старое ML-ядро как black box
8. Результат сохраняется и становится доступен через API

## Основные архитектурные правила

- API не делает inference
- Worker не должен содержать HTTP-логику
- Pipeline должен быть заменяемым
- Legacy код не должен размазываться по новому проекту
- Контракты должны быть централизованы
```

---

### `docs/architecture/repository-structure.md`

```md
# Repository Structure

## apps
- `api` — HTTP API
- `worker` — background execution
- `web` — frontend

## packages
- `contracts` — DTO и схемы
- `domain` — доменные сущности
- `application` — use cases и порты
- `pipeline` — интерфейсы пайплайна и будущие stage abstractions
- `adapters` — внешние реализации портов и legacy bridge

## docs
Постоянная документация по проекту

## tests
Юнит, интеграционные и smoke тесты
```

---

### `docs/architecture/pipeline.md`

```md
# Pipeline Architecture

На первом этапе пайплайн рассматривается как единый black-box процесс, завернутый в интерфейс.

## Текущая модель

Worker -> RenderPipeline -> LegacyPipelineAdapter -> Old ML Core

## Цель этого слоя

Сделать так, чтобы новая система зависела не от старого ML-кода напрямую, а от стабильного интерфейса.

## Дальнейшая эволюция

Позже pipeline может быть разрезан на стадии:
1. description / detection
2. segmentation
3. normalization
4. shadow generation
5. composition
6. export

Но на текущем этапе это не требуется.
```

---

### `docs/architecture/caching.md`

```md
# Caching Strategy

В системе закладывается место под многоуровневый кэш.

## Уровни кэша

1. Request-level deduplication
2. Source image cache by checksum
3. Intermediate pipeline artifacts cache
4. Final result cache by request parameters

## На первом этапе

На первом этапе реализуется только архитектурная готовность:
- интерфейсы и точки интеграции;
- cache keys;
- допустим placeholder/null cache.

## Базовая идея ключей

- source image: hash(image bytes)
- request result: hash(image hash + normalized params + pipeline version)
```

---

### `docs/architecture/decisions.md`

```md
# Architecture Decisions

## ADR-001
Используем один репозиторий для web/api/worker/shared packages.

## ADR-002
Старое ML-ядро не интегрируется напрямую в application/domain слой, а подключается через legacy adapter.

## ADR-003
API и worker разделяются с самого начала.

## ADR-004
Контракты выносятся в отдельный shared package.

## ADR-005
На первом этапе инфраструктура может быть in-memory/mock, чтобы не тормозить разработку архитектуры.
```

---

### `docs/contracts/api.md`

```md
# Public API Contracts

## Основные endpoint'ы

### GET /health
Проверка доступности API

### POST /v1/jobs
Создать job на обработку изображения

### GET /v1/jobs/{job_id}
Получить статус job

### GET /v1/jobs/{job_id}/result
Получить результат job

## Принципы ответа

- все ответы в JSON
- все ошибки в едином формате
- timestamps — ISO8601 UTC
```

---

### `docs/contracts/jobs.md`

```md
# Job Model

## Job statuses

- queued
- running
- succeeded
- failed
- canceled

## Обязательные поля job

- job_id
- status
- created_at
- updated_at

## Опциональные поля

- started_at
- finished_at
- error
- result
```

---

### `docs/contracts/ml-black-box.md`

```md
# ML Black Box Contract

На первом этапе старое ML-ядро используется как внешний black box.

## Input

- input image bytes
- render params:
  - angle_deg
  - softness
  - opacity
  - reflection
  - background spec
  - output spec

## Output

- final image
- optional debug images
- metadata
- processing metrics
- error

## Ограничения

- новая архитектура не должна зависеть от внутренней реализации legacy ML
- mapping request/response должен быть сосредоточен внутри legacy adapter
```

---

### `docs/roadmap/bootstrap-plan.md`

```md
# Bootstrap Plan

## Stage 1
- repository structure
- docs
- contracts
- domain models
- application ports/use cases
- pipeline interface
- legacy adapter

## Stage 2
- API skeleton
- worker skeleton
- local in-memory implementations

## Stage 3
- frontend skeleton
- end-to-end local happy path

## Stage 4
- infra adapters
- queue/storage replacement
- caching layer

## Stage 5
- gradual ML modularization
```

---

### `docs/roadmap/migration-phases.md`

```md
# Migration Phases

## Phase 1
New architecture around old ML black box

## Phase 2
Stable API + worker + web

## Phase 3
Internal modularization of pipeline

## Phase 4
Replacement of legacy ML stages

## Phase 5
Potential new generation GUI / interaction model
```

---

## 8. Python package: contracts

### `packages/contracts/src/shadowgen_contracts/enums.py`

```python
from enum import StrEnum


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class OutputFormat(StrEnum):
    PNG = "png"
    JPEG = "jpeg"


class ImageKind(StrEnum):
    SOURCE = "source"
    FINAL = "final"
    DEBUG = "debug"
    MASK = "mask"
    PREVIEW = "preview"
```

---

### `packages/contracts/src/shadowgen_contracts/common.py`

```python
from datetime import datetime
from pydantic import BaseModel, Field


class TimestampedModel(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AssetRef(BaseModel):
    asset_id: str
    kind: str
    mime_type: str | None = None
    width: int | None = None
    height: int | None = None
    url: str | None = None


class ProcessingMetrics(BaseModel):
    total_ms: int | None = None
    detection_ms: int | None = None
    segmentation_ms: int | None = None
    shadow_ms: int | None = None
    composition_ms: int | None = None
```

---

### `packages/contracts/src/shadowgen_contracts/render.py`

```python
from pydantic import BaseModel, Field
from .common import AssetRef, ProcessingMetrics
from .enums import OutputFormat


class ShadowSpec(BaseModel):
    angle_deg: int = Field(default=45, ge=0, lt=360)
    softness: float = Field(default=0.5, ge=0.0, le=1.0)
    opacity: float = Field(default=0.6, ge=0.0, le=1.0)
    reflection: float = Field(default=0.0, ge=0.0, le=1.0)


class BackgroundSpec(BaseModel):
    mode: str = "solid"
    color_hex: str = "#FFFFFF"


class OutputSpec(BaseModel):
    format: OutputFormat = OutputFormat.PNG
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    return_debug: bool = False


class RenderRequest(BaseModel):
    source_asset_id: str
    pipeline_version: str = "legacy-v1"
    shadow: ShadowSpec = ShadowSpec()
    background: BackgroundSpec = BackgroundSpec()
    output: OutputSpec = OutputSpec()


class RenderResult(BaseModel):
    images: list[AssetRef] = []
    debug_images: list[AssetRef] = []
    metrics: ProcessingMetrics | None = None
    warnings: list[str] = []
```

---

### `packages/contracts/src/shadowgen_contracts/jobs.py`

```python
from datetime import datetime
from pydantic import BaseModel
from .enums import JobStatus
from .render import RenderRequest, RenderResult


class JobError(BaseModel):
    code: str
    message: str
    details: dict | None = None


class JobRecord(BaseModel):
    job_id: str
    status: JobStatus
    request: RenderRequest
    result: RenderResult | None = None
    error: JobError | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class CreateJobRequest(BaseModel):
    render: RenderRequest


class CreateJobResponse(BaseModel):
    job_id: str
    status: JobStatus


class GetJobResponse(BaseModel):
    job: JobRecord
```

---

### `packages/contracts/src/shadowgen_contracts/errors.py`

```python
from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
    request_id: str | None = None
```

---

### `packages/contracts/src/shadowgen_contracts/__init__.py`

```python
from .enums import JobStatus, OutputFormat, ImageKind
from .common import AssetRef, ProcessingMetrics
from .render import ShadowSpec, BackgroundSpec, OutputSpec, RenderRequest, RenderResult
from .jobs import JobError, JobRecord, CreateJobRequest, CreateJobResponse, GetJobResponse
from .errors import ErrorBody, ErrorResponse

__all__ = [
    "JobStatus",
    "OutputFormat",
    "ImageKind",
    "AssetRef",
    "ProcessingMetrics",
    "ShadowSpec",
    "BackgroundSpec",
    "OutputSpec",
    "RenderRequest",
    "RenderResult",
    "JobError",
    "JobRecord",
    "CreateJobRequest",
    "CreateJobResponse",
    "GetJobResponse",
    "ErrorBody",
    "ErrorResponse",
]
```

---

## 9. Python package: domain

### `packages/domain/src/shadowgen_domain/statuses.py`

```python
from enum import StrEnum


class JobLifecycleStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
```

---

### `packages/domain/src/shadowgen_domain/value_objects.py`

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class JobId:
    value: str


@dataclass(frozen=True)
class AssetId:
    value: str


@dataclass(frozen=True)
class RequestFingerprint:
    value: str
```

---

### `packages/domain/src/shadowgen_domain/entities.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from shadowgen_contracts import RenderRequest, RenderResult, JobError
from .statuses import JobLifecycleStatus


@dataclass
class Job:
    job_id: str
    status: JobLifecycleStatus
    request: RenderRequest
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: RenderResult | None = None
    error: JobError | None = None
```

---

### `packages/domain/src/shadowgen_domain/exceptions.py`

```python
class DomainError(Exception):
    pass


class JobNotFoundError(DomainError):
    pass


class InvalidJobStateError(DomainError):
    pass
```

---

### `packages/domain/src/shadowgen_domain/__init__.py`

```python
from .entities import Job
from .value_objects import JobId, AssetId, RequestFingerprint
from .statuses import JobLifecycleStatus
from .exceptions import DomainError, JobNotFoundError, InvalidJobStateError

__all__ = [
    "Job",
    "JobId",
    "AssetId",
    "RequestFingerprint",
    "JobLifecycleStatus",
    "DomainError",
    "JobNotFoundError",
    "InvalidJobStateError",
]
```

---

## 10. Python package: application

### `packages/application/src/shadowgen_application/dto.py`

```python
from dataclasses import dataclass
from shadowgen_contracts import RenderRequest, RenderResult


@dataclass
class CreateJobCommand:
    request: RenderRequest


@dataclass
class ProcessJobCommand:
    job_id: str


@dataclass
class ProcessJobResult:
    result: RenderResult
```

---

### `packages/application/src/shadowgen_application/ports.py`

```python
from typing import Protocol
from shadowgen_contracts import JobRecord, RenderRequest, RenderResult


class JobRepository(Protocol):
    def create(self, job: JobRecord) -> None: ...
    def get(self, job_id: str) -> JobRecord | None: ...
    def update(self, job: JobRecord) -> None: ...


class JobQueue(Protocol):
    def publish(self, job_id: str) -> None: ...
    def consume(self) -> str | None: ...


class AssetStore(Protocol):
    def put_bytes(self, data: bytes, kind: str, mime_type: str) -> str: ...
    def get_bytes(self, asset_id: str) -> bytes: ...
    def get_url(self, asset_id: str) -> str | None: ...


class RenderPipeline(Protocol):
    def process(self, request: RenderRequest) -> RenderResult: ...


class RequestCache(Protocol):
    def get(self, key: str) -> RenderResult | None: ...
    def set(self, key: str, value: RenderResult) -> None: ...
```

---

### `packages/application/src/shadowgen_application/use_cases/create_job.py`

```python
from datetime import datetime, UTC
from uuid import uuid4

from shadowgen_contracts import JobRecord, JobStatus
from shadowgen_application.dto import CreateJobCommand
from shadowgen_application.ports import JobRepository, JobQueue


class CreateJobUseCase:
    def __init__(self, job_repository: JobRepository, job_queue: JobQueue) -> None:
        self.job_repository = job_repository
        self.job_queue = job_queue

    def execute(self, command: CreateJobCommand) -> JobRecord:
        now = datetime.now(UTC)
        job = JobRecord(
            job_id=str(uuid4()),
            status=JobStatus.QUEUED,
            request=command.request,
            result=None,
            error=None,
            created_at=now,
            updated_at=now,
            started_at=None,
            finished_at=None,
        )
        self.job_repository.create(job)
        self.job_queue.publish(job.job_id)
        return job
```

---

### `packages/application/src/shadowgen_application/use_cases/get_job.py`

```python
from shadowgen_application.ports import JobRepository
from shadowgen_domain import JobNotFoundError


class GetJobUseCase:
    def __init__(self, job_repository: JobRepository) -> None:
        self.job_repository = job_repository

    def execute(self, job_id: str):
        job = self.job_repository.get(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")
        return job
```

---

### `packages/application/src/shadowgen_application/use_cases/process_job.py`

```python
from datetime import datetime, UTC

from shadowgen_contracts import JobStatus, JobError
from shadowgen_application.ports import JobRepository, RenderPipeline
from shadowgen_domain import JobNotFoundError


class ProcessJobUseCase:
    def __init__(self, job_repository: JobRepository, pipeline: RenderPipeline) -> None:
        self.job_repository = job_repository
        self.pipeline = pipeline

    def execute(self, job_id: str):
        job = self.job_repository.get(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")

        now = datetime.now(UTC)
        job.status = JobStatus.RUNNING
        job.started_at = now
        job.updated_at = now
        self.job_repository.update(job)

        try:
            result = self.pipeline.process(job.request)
            now = datetime.now(UTC)
            job.status = JobStatus.SUCCEEDED
            job.result = result
            job.updated_at = now
            job.finished_at = now
            self.job_repository.update(job)
            return job

        except Exception as exc:
            now = datetime.now(UTC)
            job.status = JobStatus.FAILED
            job.error = JobError(
                code="PIPELINE_FAILED",
                message=str(exc),
                details=None,
            )
            job.updated_at = now
            job.finished_at = now
            self.job_repository.update(job)
            return job
```

---

### `packages/application/src/shadowgen_application/__init__.py`

```python
from .dto import CreateJobCommand, ProcessJobCommand, ProcessJobResult
```

---

## 11. Python package: pipeline

### `packages/pipeline/src/shadowgen_pipeline/interfaces.py`

```python
from typing import Protocol
from shadowgen_contracts import RenderRequest, RenderResult


class RenderPipeline(Protocol):
    def process(self, request: RenderRequest) -> RenderResult:
        ...
```

---

### `packages/pipeline/src/shadowgen_pipeline/context.py`

```python
from pydantic import BaseModel
from shadowgen_contracts import RenderRequest, RenderResult


class RenderContext(BaseModel):
    request: RenderRequest
    result: RenderResult | None = None
    warnings: list[str] = []
    cache_hits: list[str] = []
```

---

### `packages/pipeline/src/shadowgen_pipeline/cache_keys.py`

```python
import hashlib
import json
from shadowgen_contracts import RenderRequest


def make_request_cache_key(request: RenderRequest) -> str:
    payload = request.model_dump(mode="json")
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
```

---

### `packages/pipeline/src/shadowgen_pipeline/__init__.py`

```python
from .interfaces import RenderPipeline
from .context import RenderContext
from .cache_keys import make_request_cache_key
```

---

## 12. Python package: adapters

### Legacy pipeline

#### `packages/adapters/src/shadowgen_adapters/legacy_pipeline/mapper.py`

```python
from shadowgen_contracts import RenderRequest


def map_render_request_to_legacy_payload(request: RenderRequest) -> dict:
    return {
        "source_asset_id": request.source_asset_id,
        "angle_deg": request.shadow.angle_deg,
        "softness": request.shadow.softness,
        "opacity": request.shadow.opacity,
        "reflection": request.shadow.reflection,
        "background_color": request.background.color_hex,
        "return_debug": request.output.return_debug,
        "format": request.output.format.value,
        "width": request.output.width,
        "height": request.output.height,
        "pipeline_version": request.pipeline_version,
    }
```

---

#### `packages/adapters/src/shadowgen_adapters/legacy_pipeline/adapter.py`

```python
from shadowgen_contracts import RenderRequest, RenderResult, AssetRef, ProcessingMetrics
from .mapper import map_render_request_to_legacy_payload


class LegacyPipelineAdapter:
    """
    Временный адаптер к старому ML-ядру.
    На первом этапе может содержать заглушку.
    Позже сюда подключается реальный вызов legacy black box:
    - импорт Python функции
    - HTTP вызов
    - subprocess
    """

    def process(self, request: RenderRequest) -> RenderResult:
        legacy_payload = map_render_request_to_legacy_payload(request)

        # TODO:
        # Реализовать вызов старого ML black box.
        # Пока возвращаем заглушку, чтобы архитектура и wiring были готовы.
        _ = legacy_payload

        return RenderResult(
            images=[
                AssetRef(
                    asset_id="placeholder-final-image",
                    kind="final",
                    mime_type="image/png",
                    url=None,
                )
            ],
            debug_images=[],
            metrics=ProcessingMetrics(total_ms=0),
            warnings=["Legacy black-box adapter is not connected yet"],
        )
```

---

### Memory adapters

#### `packages/adapters/src/shadowgen_adapters/jobs/memory_job_repository.py`

```python
from shadowgen_contracts import JobRecord


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._storage: dict[str, JobRecord] = {}

    def create(self, job: JobRecord) -> None:
        self._storage[job.job_id] = job

    def get(self, job_id: str) -> JobRecord | None:
        return self._storage.get(job_id)

    def update(self, job: JobRecord) -> None:
        self._storage[job.job_id] = job
```

---

#### `packages/adapters/src/shadowgen_adapters/queue/memory_job_queue.py`

```python
class InMemoryJobQueue:
    def __init__(self) -> None:
        self._items: list[str] = []

    def publish(self, job_id: str) -> None:
        self._items.append(job_id)

    def consume(self) -> str | None:
        if not self._items:
            return None
        return self._items.pop(0)
```

---

#### `packages/adapters/src/shadowgen_adapters/storage/memory_asset_store.py`

```python
from uuid import uuid4


class InMemoryAssetStore:
    def __init__(self) -> None:
        self._storage: dict[str, bytes] = {}

    def put_bytes(self, data: bytes, kind: str, mime_type: str) -> str:
        asset_id = f"{kind}-{uuid4()}"
        self._storage[asset_id] = data
        return asset_id

    def get_bytes(self, asset_id: str) -> bytes:
        return self._storage[asset_id]

    def get_url(self, asset_id: str) -> str | None:
        return None
```

---

### `packages/adapters/src/shadowgen_adapters/__init__.py`

```python
```

---

## 13. API приложение

### `apps/api/src/shadowgen_api/config.py`

```python
from pydantic import BaseModel


class ApiConfig(BaseModel):
    app_name: str = "ShadowGen API"
    debug: bool = True
```

---

### `apps/api/src/shadowgen_api/deps.py`

```python
from shadowgen_adapters.jobs.memory_job_repository import InMemoryJobRepository
from shadowgen_adapters.queue.memory_job_queue import InMemoryJobQueue
from shadowgen_application.use_cases.create_job import CreateJobUseCase
from shadowgen_application.use_cases.get_job import GetJobUseCase


job_repository = InMemoryJobRepository()
job_queue = InMemoryJobQueue()


def get_create_job_use_case() -> CreateJobUseCase:
    return CreateJobUseCase(job_repository=job_repository, job_queue=job_queue)


def get_get_job_use_case() -> GetJobUseCase:
    return GetJobUseCase(job_repository=job_repository)
```

---

### `apps/api/src/shadowgen_api/schemas/api_requests.py`

```python
from shadowgen_contracts import CreateJobRequest

__all__ = ["CreateJobRequest"]
```

---

### `apps/api/src/shadowgen_api/schemas/api_responses.py`

```python
from shadowgen_contracts import CreateJobResponse, GetJobResponse, ErrorResponse

__all__ = ["CreateJobResponse", "GetJobResponse", "ErrorResponse"]
```

---

### `apps/api/src/shadowgen_api/routes/health.py`

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}
```

---

### `apps/api/src/shadowgen_api/routes/jobs.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from shadowgen_contracts import CreateJobRequest, CreateJobResponse, GetJobResponse
from shadowgen_application.dto import CreateJobCommand
from shadowgen_application.use_cases.create_job import CreateJobUseCase
from shadowgen_application.use_cases.get_job import GetJobUseCase
from shadowgen_domain import JobNotFoundError

from shadowgen_api.deps import get_create_job_use_case, get_get_job_use_case

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.post("", response_model=CreateJobResponse)
def create_job(
    payload: CreateJobRequest,
    use_case: CreateJobUseCase = Depends(get_create_job_use_case),
):
    job = use_case.execute(CreateJobCommand(request=payload.render))
    return CreateJobResponse(job_id=job.job_id, status=job.status)


@router.get("/{job_id}", response_model=GetJobResponse)
def get_job(
    job_id: str,
    use_case: GetJobUseCase = Depends(get_get_job_use_case),
):
    try:
        job = use_case.execute(job_id)
        return GetJobResponse(job=job)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
```

---

### `apps/api/src/shadowgen_api/routes/assets.py`

```python
from fastapi import APIRouter

router = APIRouter(prefix="/v1/assets", tags=["assets"])


@router.post("")
def upload_asset_placeholder():
    return {"message": "Asset upload is not implemented yet"}
```

---

### `apps/api/src/shadowgen_api/services/job_service.py`

```python
# Reserved for future orchestration helpers.
```

---

### `apps/api/src/shadowgen_api/main.py`

```python
from fastapi import FastAPI

from shadowgen_api.routes.health import router as health_router
from shadowgen_api.routes.jobs import router as jobs_router
from shadowgen_api.routes.assets import router as assets_router


def create_app() -> FastAPI:
    app = FastAPI(title="ShadowGen API", version="0.1.0")
    app.include_router(health_router)
    app.include_router(jobs_router)
    app.include_router(assets_router)
    return app


app = create_app()
```

---

### `apps/api/README.md`

```md
# API App

FastAPI backend for ShadowGen v2.

Responsibilities:
- validate requests
- create jobs
- return statuses and results

Non-responsibilities:
- no image inference
- no ML logic
```

---

## 14. Worker приложение

### `apps/worker/src/shadowgen_worker/config.py`

```python
from pydantic import BaseModel


class WorkerConfig(BaseModel):
    poll_interval_sec: float = 1.0
```

---

### `apps/worker/src/shadowgen_worker/executor.py`

```python
from shadowgen_application.use_cases.process_job import ProcessJobUseCase


class JobExecutor:
    def __init__(self, process_job_use_case: ProcessJobUseCase) -> None:
        self.process_job_use_case = process_job_use_case

    def execute(self, job_id: str):
        return self.process_job_use_case.execute(job_id)
```

---

### `apps/worker/src/shadowgen_worker/loop.py`

```python
import time


class WorkerLoop:
    def __init__(self, queue, executor, poll_interval_sec: float = 1.0) -> None:
        self.queue = queue
        self.executor = executor
        self.poll_interval_sec = poll_interval_sec

    def run_forever(self):
        while True:
            job_id = self.queue.consume()
            if job_id is None:
                time.sleep(self.poll_interval_sec)
                continue
            self.executor.execute(job_id)
```

---

### `apps/worker/src/shadowgen_worker/main.py`

```python
from shadowgen_adapters.jobs.memory_job_repository import InMemoryJobRepository
from shadowgen_adapters.queue.memory_job_queue import InMemoryJobQueue
from shadowgen_adapters.legacy_pipeline.adapter import LegacyPipelineAdapter
from shadowgen_application.use_cases.process_job import ProcessJobUseCase

from shadowgen_worker.executor import JobExecutor
from shadowgen_worker.loop import WorkerLoop


def main():
    # NOTE:
    # Сейчас это локальный placeholder wiring.
    # Позже репозиторий и очередь должны быть общими для API и worker.
    job_repository = InMemoryJobRepository()
    job_queue = InMemoryJobQueue()
    pipeline = LegacyPipelineAdapter()

    process_job_use_case = ProcessJobUseCase(
        job_repository=job_repository,
        pipeline=pipeline,
    )
    executor = JobExecutor(process_job_use_case)
    loop = WorkerLoop(queue=job_queue, executor=executor)
    loop.run_forever()


if __name__ == "__main__":
    main()
```

---

### `apps/worker/README.md`

```md
# Worker App

Background worker for ShadowGen v2.

Responsibilities:
- consume jobs
- execute pipeline
- update job status

Non-responsibilities:
- no HTTP API
- no frontend logic
```

---

## 15. Web приложение

На первом этапе фронт можно оставить минимальным, но создать правильную структуру.

### `apps/web/README.md`

```md
# Web App

Next.js frontend for ShadowGen v2.

Main user flow:
1. upload image
2. choose shadow parameters
3. create job
4. poll job status
5. show result
```

---

### `apps/web/package.json`

```json
{
  "name": "shadowgen-web",
  "private": true,
  "version": "0.1.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.2.0",
    "react": "18.2.0",
    "react-dom": "18.2.0"
  },
  "devDependencies": {
    "typescript": "5.4.0",
    "@types/react": "18.2.0",
    "@types/node": "20.11.0"
  }
}
```

---

### `apps/web/src/lib/types.ts`

```ts
export type JobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "canceled";

export interface CreateJobRequest {
  render: {
    source_asset_id: string;
    pipeline_version: string;
    shadow: {
      angle_deg: number;
      softness: number;
      opacity: number;
      reflection: number;
    };
    background: {
      mode: string;
      color_hex: string;
    };
    output: {
      format: "png" | "jpeg";
      width?: number | null;
      height?: number | null;
      return_debug: boolean;
    };
  };
}

export interface CreateJobResponse {
  job_id: string;
  status: JobStatus;
}
```

---

### `apps/web/src/lib/api-client.ts`

```ts
import { CreateJobRequest, CreateJobResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function createJob(payload: CreateJobRequest): Promise<CreateJobResponse> {
  const response = await fetch(`${API_BASE}/v1/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Failed to create job: ${response.status}`);
  }

  return response.json();
}
```

---

### `apps/web/src/components/upload-form.tsx`

```tsx
"use client";

export function UploadForm() {
  return (
    <div>
      <p>Upload form placeholder</p>
    </div>
  );
}
```

---

### `apps/web/src/components/angle-slider.tsx`

```tsx
"use client";

export function AngleSlider() {
  return (
    <div>
      <p>Angle slider placeholder</p>
    </div>
  );
}
```

---

### `apps/web/src/components/result-view.tsx`

```tsx
"use client";

export function ResultView() {
  return (
    <div>
      <p>Result view placeholder</p>
    </div>
  );
}
```

---

### `apps/web/src/app/layout.tsx`

```tsx
import React from "react";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

---

### `apps/web/src/app/page.tsx`

```tsx
import { UploadForm } from "../components/upload-form";
import { AngleSlider } from "../components/angle-slider";
import { ResultView } from "../components/result-view";

export default function HomePage() {
  return (
    <main style={{ padding: 24 }}>
      <h1>ShadowGen v2</h1>
      <UploadForm />
      <AngleSlider />
      <ResultView />
    </main>
  );
}
```

---

### `apps/web/src/app/jobs/[jobId]/page.tsx`

```tsx
export default function JobPage() {
  return (
    <main style={{ padding: 24 }}>
      <h1>Job page placeholder</h1>
    </main>
  );
}
```

---

## 16. Общие служебные файлы

### `.env.example`

```env
APP_ENV=dev
API_HOST=0.0.0.0
API_PORT=8000
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

---

### `.gitignore`

```gitignore
__pycache__/
*.pyc
.venv/
venv/
.env
.env.local
node_modules/
.next/
dist/
build/
.idea/
.vscode/
.DS_Store
```

---

### `pyproject.toml`

Нужен простой, но рабочий bootstrap.

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "shadowgen-v2"
version = "0.1.0"
description = "ShadowGen v2"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn>=0.30.0",
  "pydantic>=2.7.0"
]

[tool.setuptools]
include-package-data = true

[tool.setuptools.packages.find]
where = [
  "apps/api/src",
  "apps/worker/src",
  "packages/contracts/src",
  "packages/domain/src",
  "packages/application/src",
  "packages/pipeline/src",
  "packages/adapters/src"
]
```

---

### `tools/dev/run_local.py`

```python
import uvicorn


if __name__ == "__main__":
    uvicorn.run("shadowgen_api.main:app", host="0.0.0.0", port=8000, reload=True)
```

---

## 17. Тестовая структура

Пока достаточно заглушек.

### `tests/smoke/README.md`

```md
# Smoke Tests

На первом этапе здесь хранятся простые sanity checks:
- API поднимается
- create job работает
- worker может обработать job через legacy adapter stub
```

---

## 18. Обязательные требования к агенту

Агент должен:

1. **Не подмешивать старую архитектуру в новую**
   Никаких прямых импортов legacy ML-кода за пределами `packages/adapters/legacy_pipeline`.

2. **Не менять целевую структуру без веской причины**
   Можно аккуратно дополнять, но не ломать общую схему.

3. **Сохранить идею black-box integration**
   На первом этапе `LegacyPipelineAdapter` может быть stub, но должен быть готов к подключению настоящего legacy вызова.

4. **Не перегружать проект**
   Не добавлять сейчас:

   * Redis;
   * Postgres;
   * Celery;
   * Docker orchestration;
   * сложную auth систему;
   * продвинутую observability.

5. **Сделать код запускаемым локально**
   Даже со stub adapter.

6. **Сделать contracts центром интеграции**
   Все слои должны опираться на shared contracts.

7. **Сохранить расширяемость**
   Пайплайн, storage, queue, cache должны зависеть от портов/интерфейсов, а не от конкретных реализаций.

---

## 19. Что именно надо сделать в репозитории

Агент должен выполнить следующие изменения:

### Шаг 1

Полностью перестроить дерево каталогов под структуру из этой инструкции.

### Шаг 2

Заменить README и создать документацию в `docs/`.

### Шаг 3

Создать Python packages:

* `contracts`
* `domain`
* `application`
* `pipeline`
* `adapters`

### Шаг 4

Создать skeleton приложений:

* `apps/api`
* `apps/worker`
* `apps/web`

### Шаг 5

Сделать minimal working wiring:

* FastAPI app поднимается;
* endpoint `/health` работает;
* endpoint `POST /v1/jobs` создаёт job;
* endpoint `GET /v1/jobs/{job_id}` возвращает job;
* есть `LegacyPipelineAdapter` stub;
* есть базовые in-memory adapters.

### Шаг 6

Не пытаться сейчас внедрять реальный legacy ML вызов, если это потребует много неаккуратного протаскивания старого кода.
Нужен именно clean architecture bootstrap.

---

## 20. Что можно улучшить поверх этого, но только аккуратно

Допустимо:

* добавить `Makefile`;
* добавить базовые unit tests;
* добавить prettier/eslint для web;
* добавить `health` и `ready`;
* добавить `request_id` middleware;
* добавить нормальный error handler.

Но это не должно размыть главный смысл: **чистый skeleton новой архитектуры вокруг black-box ML**.

---

## 21. Итоговое краткое описание для агента

Нужно превратить `ShadowGen-v2` в **чистый монорепозиторий** со следующей моделью:

* `web` — UI;
* `api` — HTTP-слой;
* `worker` — исполняет jobs;
* `contracts` — единый источник схем;
* `application` — use cases и порты;
* `pipeline` — интерфейсы обработки;
* `adapters/legacy_pipeline` — единственное место, где допустимо знание о старом ML-ядре.

На первом этапе старая ML-логика не переписывается и считается black box. Главная цель — создать правильную архитектурную оболочку, которую потом можно будет безопасно развивать.

