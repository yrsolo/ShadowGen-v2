
## Коротко: целевая схема

* **Бакет Object Storage** — фронт и файлы
* **Serverless Container** — API backend
* **API Gateway** — входная HTTPS-точка для API
* **Домашний Windows-комп с GPU** — worker + текущее ML-ядро
* **Очередь Yandex Message Queue** — обмен job между облаком и домашним worker
* **Домен** — на фронт и API
* **VPS** — не нужен, держим как аварийный запасной план

Object Storage умеет хостить статический сайт, Serverless Containers запускают контейнерное приложение без VM, API Gateway даёт HTTPS-вход, а Message Queue совместима с Amazon SQS API, так что домашний worker может сам забирать задания исходящими запросами — без белого IP. ([Яндекс.Облако][1])

---

## Как именно разложить сервисы

### 1) Frontend

**Куда:** `Object Storage`

Туда кладёшь:

* `apps/web` после билда
* статику
* возможно, preview assets

Это дешёвый и очень естественный вариант для твоего нового web UI. Yandex Object Storage поддерживает static website hosting, а для своего домена можно привязать DNS и HTTPS через Certificate Manager. ([Яндекс.Облако][1])

### 2) API

**Куда:** `Serverless Container`
**Перед ним:** `API Gateway`

Туда кладёшь:

* `apps/api` как Docker image с FastAPI
* ручки:

  * `POST /v1/jobs`
  * `GET /v1/jobs/{id}`
  * `GET /health`
  * позже `POST /v1/assets`

Почему контейнер, а не функция:

* у тебя не один маленький handler, а нормальный backend;
* удобнее тащить свои зависимости;
* проще локально гонять тот же образ;
* легче потом расти без перепаковки архитектуры.
  Yandex Serverless Containers как раз рассчитаны на запуск контейнеризованных приложений, а API Gateway — на публичный HTTP вход. ([Яндекс.Облако][2])

### 3) Очередь задач

**Куда:** `Yandex Message Queue`

Туда кладёшь:

* сообщения о job
* возможно отдельную DLQ later

Это главный трюк, который избавляет тебя от белого IP:
не облако идёт в домашний GPU, а **домашний worker сам polling’ом читает очередь**.

Message Queue поддерживает standard и FIFO очереди, совместима с Amazon SQS API и работает в модели “producer кладёт → consumer читает → после обработки удаляет”. Для твоего сценария это почти идеальное связующее звено. ([Яндекс.Облако][3])

### 4) Хранилище файлов

**Куда:** ещё один или те же `Object Storage` бакеты

Я бы разделил логически хотя бы на:

* `shadowgen-web` — фронт
* `shadowgen-assets` — пользовательские исходники и результаты
* опционально `shadowgen-debug` — промежуточные артефакты

В `assets` кладёшь:

* source images
* final images
* debug masks / previews
* позже кэш промежуточных результатов

### 5) Домашний GPU

**Куда:** твой текущий Windows-комп

Там живут:

* `apps/worker`
* `LegacyPipelineAdapter`
* текущее ML-ядро
* локальный кэш моделей
* возможно локальный temp storage

Worker делает так:

1. читает сообщение из очереди;
2. получает параметры job;
3. скачивает исходник из Object Storage или принимает ссылку/asset id;
4. дёргает старое ML-ядро как black box;
5. загружает результат обратно в Object Storage;
6. сообщает API, что job завершён.

Это лучший вариант под твоё ограничение “серый IP + Windows + уже крутится ML”. Никакого входящего трафика домой не нужно.

---

## Как идут данные по системе

### Сценарий запроса

1. Пользователь открывает сайт с бакета.
2. UI отправляет запрос в API Gateway.
3. API в Serverless Container:

   * валидирует запрос,
   * создаёт `job_id`,
   * пишет job metadata,
   * складывает сообщение в Message Queue,
   * сразу отвечает `queued`.
4. Домашний worker периодически читает очередь.
5. Worker берёт job, запускает legacy ML.
6. Готовый результат грузит в Object Storage.
7. Worker обновляет статус job.
8. UI опрашивает API и получает `succeeded` + ссылки на результат.

---

## Что где должно лежать по коду

### В облаке

**Object Storage**

* билд фронта
* user assets
* final results
* debug artifacts

**Serverless Container**

* `apps/api`
* только backend orchestration
* без ML inference

**API Gateway**

* маршрутит `/api/*` в контейнер
* даёт публичный HTTPS endpoint

**Message Queue**

* сообщения `render-job-created`
* позже можно добавить DLQ и retry policy

### Дома

**Windows worker**

* `apps/worker`
* `packages/adapters/legacy_pipeline`
* legacy ML core
* model weights
* локальный temporary cache

---

## Где хранить состояние job

У тебя из перечисленного нет нормальной managed БД в обязательном наборе, и ты не хочешь VPS.

Поэтому я бы предложил **двухэтапный путь**:

### Вариант 1 — самый простой старт

Состояние job временно хранить:

* либо в Object Storage как JSON-файлы по `job_id`,
* либо в простом внутреннем storage-слое API, если тебе нужно только быстро завестись.

Это не идеал, но для bootstrap нормально.

### Вариант 2 — правильнее чуть позже

Добавить managed БД/serverless-хранилище метаданных.

Но раз ты сейчас хочешь минимальной инфры, можно начать даже так:

* `jobs/{job_id}.json`
* `results/{job_id}/final.png`

Это грубовато, зато не требует VPS и не мешает потом заменить storage adapter.

---

## Что я бы сделал прямо сейчас по окружениям

### Production-lite

* `web` → Object Storage
* `api` → Serverless Container
* `api public entry` → API Gateway
* `jobs queue` → Message Queue
* `gpu worker` → home Windows PC
* `assets/results` → Object Storage

### Local dev

* `web` локально
* `api` локально
* `worker` локально
* `legacy ML` локально
* in-memory queue/store

---

## Почему VPS пока лучше не трогать

Потому что VPS сразу тянет за собой:

* systemd
* reverse proxy
* сертификаты
* Docker Compose
* обновления
* логи
* перезапуски
* ручное обслуживание

А твоя схема и без этого уже жизнеспособна:
serverless control plane в облаке + GPU worker дома.

VPS я бы оставил только как запасной путь, если потом упрёшься в ограничения serverless или захочешь постоянный stateful backend.

---

## Важный архитектурный принцип для твоего случая

### В облако — только orchestration

Туда выносим:

* HTTP
* очередь
* хранение файлов
* статусы
* контракты

### На домашний GPU — только inference

Там:

* старый ML black box
* pipeline execution
* локальные модели
* тяжёлые вычисления

Так ты не смешиваешь transport и ML, и не привязываешь облачную часть к Windows-машине напрямую.

---

## Что лучше сделать с доменом

Я бы разделил так:

* `app.yourdomain` → frontend в Object Storage
* `api.yourdomain` → API Gateway → Serverless Container

Для фронта через Object Storage можно подключить свой домен и HTTPS; для API Gateway тоже даёшь свой публичный адрес. Yandex документация для static hosting с доменом и HTTPS это поддерживает. ([Яндекс.Облако][4])

---

## Самый практичный стартовый набор ресурсов

Если совсем по минимуму:

1. **Bucket `shadowgen-web`**
2. **Bucket `shadowgen-assets`**
3. **Serverless Container `shadowgen-api`**
4. **API Gateway `shadowgen-gateway`**
5. **Message Queue `shadowgen-jobs`**
6. **Домашний worker на Windows**

И всё.

---

## Как бы я разложил роли сервисов

### Object Storage

* фронт
* исходники
* финальные картинки
* debug outputs
* возможно JSON статусы на самом старте

### Serverless Container

* HTTP API
* create job
* get job
* get result
* presigned/public URL logic
* позже auth/session

### API Gateway

* единая HTTPS точка входа
* маршрутизация к контейнеру

### Message Queue

* транспорт задач
* decoupling между API и worker

### Home GPU worker

* polling queue
* inference
* upload result
* update status

---

## Чего я бы не делал сейчас

* не публиковал домашний GPU наружу;
* не делал прямой HTTP вызов из облака в дом;
* не заводил VPS “на всякий случай”;
* не делал сразу Cloud Functions рядом с контейнером для тех же задач;
* не раскладывал всё по куче сервисов.

---

## Моя итоговая рекомендация

Тебе лучше всего подойдёт такая инфра-схема:

```text
[Object Storage: web]
        |
     browser
        |
   [API Gateway]
        |
[Serverless Container: api]
        |
 [Message Queue: jobs]
        |
   polling over HTTPS
        |
[Home Windows GPU worker]
        |
 old ML black box
        |
[Object Storage: assets/results]
```

Это:

* укладывается в твои доступные сервисы;
* не требует белого IP;
* не требует VPS;
* не требует постоянного Linux-администрирования;
* хорошо совпадает с архитектурой `api + worker + black-box ml`.
