# Universal Project Starter Template v2 Шаблон для будущих проектов: структурированный репозиторий, понятная документация, сильные агентские инструкции, рабочий процесс без бюрократии и набор базовых skills. --- # 1. Принципы шаблона 1. Репозиторий должен быстро вводить в проект сверху вниз: - корневой `README.md` — обзор и ценность; - `docs/README.md` — карта документации; - `docs/overview/` — быстрый вход; - `docs/architecture/` и `docs/reference/` — детали; - `work/` — временный рабочий слой. 2. Документация не считается истиной сама по себе. Всё важное сверяется с: - кодом, - схемами, - конфигами, - тестами, - CI/deploy, - реальным поведением системы. 3. Агент не должен работать хаотично. Работа должна оставлять след: - текущая задача, - план, - evidence, - закрытие этапа. 4. Повседневная работа должна быть лёгкой. Глубокие проверки — только по явной команде или в конце крупного этапа. 5. Архитектура должна быть эволюционной. Без big-bang переделок, без fat handlers, без document drift, без config-spaghetti. --- # 2. Структура репозитория ```text project-template/ ├─ README.md ├─ AGENTS.md ├─ .gitignore ├─ .editorconfig ├─ .env.example ├─ .env.dev.example ├─ .env.prod.example ├─ package.json ├─ pyproject.toml ├─ Makefile ├─ Dockerfile ├─ .github/ │ ├─ workflows/ │ │ ├─ ci.yml │ │ └─ docs-check.yml │ ├─ ISSUE_TEMPLATE/ │ │ ├─ bug_report.md │ │ ├─ feature_request.md │ │ └─ documentation.md │ └─ pull_request_template.md ├─ .codex/ │ └─ skills/ │ ├─ verify-docs-architecture/ │ │ └─ SKILL.md │ ├─ trace-source-of-truth/ │ │ └─ SKILL.md │ ├─ check-readme-role/ │ │ └─ SKILL.md │ ├─ update-tracking/ │ │ └─ SKILL.md │ ├─ run-tests/ │ │ └─ SKILL.md │ ├─ prepare-release/ │ │ └─ SKILL.md │ ├─ verify-tool-contracts/ │ │ └─ SKILL.md │ ├─ change-prompts/ │ │ └─ SKILL.md │ └─ run-evals/ │ └─ SKILL.md ├─ agent/ │ ├─ OPERATING_CONTRACT.md │ ├─ prompts/ │ │ ├─ system.md │ │ ├─ developer.md │ │ └─ templates/ │ │ ├─ task-start.md │ │ ├─ task-close.md │ │ └─ doc-audit.md │ ├─ policies/ │ │ ├─ approvals.yaml │ │ ├─ budgets.yaml │ │ ├─ rate_limits.yaml │ │ └─ redaction.yaml │ ├─ tools/ │ │ ├─ schemas/ │ │ │ ├─ command.schema.json │ │ │ ├─ report.schema.json │ │ │ └─ doc_audit.schema.json │ │ └─ implementations/ │ │ └─ README.md │ └─ evals/ │ ├─ README.md │ ├─ datasets/ │ │ └─ smoke.yaml │ └─ scenarios/ │ └─ doc-governance.yaml ├─ apps/ │ ├─ api/ │ │ ├─ README.md │ │ ├─ src/ │ │ │ ├─ main.py │ │ │ ├─ entrypoints/ │ │ │ │ └─ http.py │ │ │ ├─ domain/ │ │ │ │ └─ README.md │ │ │ ├─ application/ │ │ │ │ └─ README.md │ │ │ ├─ adapters/ │ │ │ │ └─ README.md │ │ │ └─ config/ │ │ │ └─ settings.py │ │ └─ tests/ │ │ └─ test_health.py │ └─ web/ │ ├─ README.md │ ├─ src/ │ │ ├─ app/ │ │ ├─ pages/ │ │ ├─ features/ │ │ ├─ shared/ │ │ └─ config/ │ └─ tests/ │ └─ smoke.test.ts ├─ packages/ │ ├─ schema/ │ │ ├─ README.md │ │ ├─ openapi/ │ │ └─ jsonschema/ │ └─ shared/ │ └─ README.md ├─ docs/ │ ├─ README.md │ ├─ overview/ │ │ ├─ product.md │ │ ├─ getting-started.md │ │ └─ repository-map.md │ ├─ architecture/ │ │ ├─ README.md │ │ ├─ ideal-principles.md │ │ ├─ system-overview.md │ │ ├─ backend.md │ │ ├─ frontend.md │ │ ├─ data-model.md │ │ └─ integrations.md │ ├─ process/ │ │ ├─ README.md │ │ ├─ agent-workflow.md │ │ ├─ documentation-governance.md │ │ ├─ release-flow.md │ │ └─ how-to-use-skills.md │ ├─ adr/ │ │ ├─ README.md │ │ └─ ADR-001-template.md │ ├─ reference/ │ │ ├─ api.md │ │ ├─ config.md │ │ ├─ env.md │ │ └─ commands.md │ └─ archive/ ├─ work/ │ ├─ now/ │ │ ├─ README.md │ │ ├─ current-task.md │ │ ├─ plan.md │ │ └─ evidence.md │ ├─ roadmap/ │ │ └─ README.md │ └─ archive/ │ └─ README.md ├─ scripts/ │ ├─ bootstrap.sh │ ├─ docs-check.sh │ ├─ test.sh │ └─ release-check.sh ├─ tests/ │ ├─ integration/ │ └─ e2e/ └─ artifacts/ └─ README.md 
3. Назначение ключевых зон
Корень репозитория
В корне должно быть только то, что помогает быстро понять проект:
• что это;
• зачем он нужен;
• как запустить;
• где документация;
• где код;
• как работать агенту и человеку.
Корень не должен превращаться в свалку техдеталей.
docs/
Постоянная документация. Строится как дерево от простого к сложному.
work/
Временный рабочий контур. Здесь живут:
• текущая задача,
• временный план,
• evidence,
• промежуточные решения.
После завершения всё либо архивируется, либо конденсируется в постоянные docs.
.codex/skills/
Модульные procedural skills. Не надо пытаться впихнуть всё в один AGENTS.md.
agent/
Артефакты агентного слоя:
• операционный контракт,
• prompts,
• policies,
• tool contracts,
• evals.
apps/
Продуктовый код. Разделение на приложения, а не хаотичный монолит.
4. Содержимое основных файлов
README.md
# Project Name Короткое, понятное описание продукта в 2–4 предложениях. ## Что это Обзор продукта простыми словами. ## Зачем это нужно Какая проблема решается и для кого. ## Основные возможности - Возможность 1 - Возможность 2 - Возможность 3 ## Быстрый старт См.: - [Getting Started](docs/overview/getting-started.md) - [Repository Map](docs/overview/repository-map.md) - [Architecture Overview](docs/architecture/system-overview.md) ## Структура репозитория - `apps/` — приложения - `packages/` — общие схемы и shared code - `docs/` — постоянная документация - `work/` — активная работа - `agent/` — агентный слой - `.codex/skills/` — модульные procedural skills ## Документация Главная карта документации: [docs/README.md](docs/README.md) ## Работа агента См.: - [AGENTS.md](AGENTS.md) - [agent/OPERATING_CONTRACT.md](agent/OPERATING_CONTRACT.md) ## Статус Коротко о зрелости проекта. ## License Указать лицензию при необходимости. 
AGENTS.md
# AGENTS.md Этот файл задаёт обязательные правила работы агента в репозитории. ## 1. Основной принцип Не работать хаотично. Любое заметное изменение должно оставлять понятный след. ## 2. Перед началом работы Перед реализацией агент обязан: 1. Прочитать `README.md` 2. Прочитать `docs/README.md` 3. Прочитать `agent/OPERATING_CONTRACT.md` 4. Проверить `work/now/current-task.md` 5. Если задача крупная — обновить `work/now/plan.md` ## 3. Source of truth Документация не считается истиной автоматически. При важных утверждениях сверять: - код, - конфиги, - схемы, - тесты, - CI, - runtime entrypoints. ## 4. Работа с документацией Документация должна оставаться иерархичной: - root README — обзор; - docs overview — быстрый вход; - architecture/reference — детали; - work — временное. ## 5. Tracking обязателен Если работа дольше мелкой локальной правки: - обновить `work/now/current-task.md` - при необходимости обновить `work/now/plan.md` - после работы — `work/now/evidence.md` ## 6. Не плодить хаос Нельзя без нужды: - создавать новые файлы; - дублировать docs; - писать новые архитектурные сущности без мотивации; - делать скрытую магию в config/runtime. ## 7. После завершения этапа Агент должен: 1. Обновить docs, если они затронуты 2. Запустить релевантные проверки 3. Обновить evidence 4. При крупном этапе — предложить полный doc audit ## 8. Предпочитаемый workflow - обычная работа: quick checks - крупный этап: full audit / full sync - перед release: release check 
agent/OPERATING_CONTRACT.md
# Operating Contract ## Цель Поддерживать управляемую, проверяемую и эволюционную разработку. ## Инварианты 1. Код важнее prose при конфликте. 2. Важные выводы должны быть проверяемыми. 3. Рабочие документы не смешиваются с постоянной документацией. 4. Один документ — одна роль. 5. Один большой этап должен завершаться cleanup-процедурой. ## Start gate Перед заметной работой агент обязан: - понять текущую задачу; - проверить карту документации; - понять, где source of truth; - определить, нужно ли обновлять tracking; - определить риск затронуть docs. ## Contract check Перед финализацией: - код соответствует задаче; - docs обновлены или явно не требуют обновления; - evidence кратко зафиксировано; - тесты/проверки выполнены; - нет явных конфликтов docs и code. ## Режимы проверки docs - `quick`: локально по затронутой области - `full-audit`: полный анализ repo без тяжёлой перестройки - `full-sync`: полный анализ и приведение docs в порядок ## Когда использовать full - конец крупного этапа - перед релизом - после архитектурного рефакторинга - если docs начали расходиться с кодом ## Anti-chaos rules - не дробить документы без нужды; - не плодить индексы на каждый чих; - не запускать полную ревизию на каждую мелкую задачу; - не оставлять изменения без следа в tracking при большой работе. 
5. Документация
docs/README.md
# Documentation Map ## Как читать эту документацию Документация устроена как дерево от простого к сложному: 1. Overview — быстро понять продукт и репозиторий 2. Architecture — техническая картина системы 3. Process — как в проекте работать 4. Reference — точные справочные материалы 5. ADR — отдельные архитектурные решения 6. Archive — устаревшие или исторические материалы ## Быстрый вход - [Product Overview](overview/product.md) - [Getting Started](overview/getting-started.md) - [Repository Map](overview/repository-map.md) ## Архитектура - [Architecture Index](architecture/README.md) - [System Overview](architecture/system-overview.md) - [Ideal Principles](architecture/ideal-principles.md) ## Процесс - [Process Index](process/README.md) - [Agent Workflow](process/agent-workflow.md) - [Documentation Governance](process/documentation-governance.md) - [How to Use Skills](process/how-to-use-skills.md) ## Reference - [API](reference/api.md) - [Config](reference/config.md) - [Env](reference/env.md) - [Commands](reference/commands.md) ## ADR - [ADR Index](adr/README.md) 
docs/overview/product.md
# Product Overview ## Что это Коротко объяснить продукт без технической перегрузки. ## Для кого Кто пользователь. ## Какую проблему решает Главная ценность. ## Основные сценарии - Сценарий 1 - Сценарий 2 - Сценарий 3 ## Ключевые части системы Коротко, без deep technical details. ## Куда идти дальше - [Getting Started](getting-started.md) - [Repository Map](repository-map.md) - [System Overview](../architecture/system-overview.md) 
docs/overview/getting-started.md
# Getting Started ## Что нужно для старта - требования к окружению - как установить зависимости - как запустить сервисы ## Быстрый запуск Простые команды или ссылка на команды. ## Что открыть после запуска - UI - API - docs - test endpoints ## Дальше читать - [Repository Map](repository-map.md) - [Commands Reference](../reference/commands.md) - [Agent Workflow](../process/agent-workflow.md) 
docs/overview/repository-map.md
# Repository Map ## Цель Помочь быстро понять, что где лежит. ## Основные директории - `apps/api` — backend - `apps/web` — frontend - `packages/schema` — контракты - `docs` — постоянная документация - `work` — активная работа - `agent` — агентные артефакты - `.codex/skills` — procedural skills ## Типичный маршрут новичка 1. `README.md` 2. `docs/README.md` 3. `docs/overview/*` 4. `docs/architecture/system-overview.md` 5. `agent/OPERATING_CONTRACT.md` ## Связанные документы - [Documentation Map](../README.md) - [System Overview](../architecture/system-overview.md) 
docs/architecture/README.md
# Architecture Index ## Что здесь Технические документы по устройству системы. ## Основные документы - [System Overview](system-overview.md) - [Ideal Principles](ideal-principles.md) - [Backend](backend.md) - [Frontend](frontend.md) - [Data Model](data-model.md) - [Integrations](integrations.md) 
docs/architecture/ideal-principles.md
# Ideal Architecture Principles ## 1. Thin entrypoints HTTP/CLI/jobs не должны содержать бизнес-логику. ## 2. Domain-first core Ключевые правила должны жить в domain/application слоях. ## 3. Explicit composition root Сборка зависимостей должна быть явной. ## 4. Ports and adapters Интеграции и инфраструктура изолированы от core. ## 5. Contracts over improvisation API, env, data contracts, async jobs должны быть явно описаны. ## 6. Bulk over N+1 Избегать потока мелких запросов и скрытого fan-out. ## 7. Read/write clarity Чётко разделять чтение, запись и побочные эффекты. ## 8. Observable behavior Ключевые потоки должны быть диагностируемыми. ## 9. No config spaghetti Доступ к env/config централизован. ## 10. No hidden branching Скрытая runtime-магия и feature-flag spaghetti запрещены. ## 11. Evolution over big-bang Система должна поддерживать пошаговую эволюцию. ## 12. Documentation with trust levels Docs полезны, но не заменяют проверку по коду. 
docs/process/README.md
# Process Index ## Что здесь Как в проекте работать, поддерживать docs и проводить большие этапы изменений. ## Основные документы - [Agent Workflow](agent-workflow.md) - [Documentation Governance](documentation-governance.md) - [Release Flow](release-flow.md) - [How to Use Skills](how-to-use-skills.md) 
docs/process/agent-workflow.md
# Agent Workflow ## Обычный цикл работы 1. Прочитать контекст 2. Определить source of truth 3. Выполнить задачу 4. Обновить локальные docs при необходимости 5. Прогнать quick checks 6. Обновить tracking, если задача заметная ## После крупного этапа 1. Выполнить `verify-docs-architecture` в `full-audit` 2. Посмотреть отчёт 3. Выполнить `full-sync`, если нужен cleanup 4. Прогнать tests 5. Выполнить `prepare-release` ## Когда не надо перегружать процесс - мелкая локальная правка - typo - незначительное переименование - маленькое изменение без архитектурного следа ## Когда нужен усиленный режим - серия фич - рефакторинг - изменение API - изменение auth/config/runtime - restructuring docs 
docs/process/documentation-governance.md
# Documentation Governance ## Основной принцип Документация — это архитектурная система, а не свалка markdown-файлов. ## Уровни документации - Level 0: root README - Level 1: overview docs - Level 2: architecture/reference - Level 3: ADR - Working layer: `work/` - Archive layer: `docs/archive/`, `work/archive/` ## Правила 1. Один документ — одна роль. 2. Корневой README обзорный и маршрутизирующий. 3. Overview docs вводят в тему быстро. 4. Tech docs узкие и конкретные. 5. Work docs не смешиваются с постоянными. 6. Все важные docs связаны ссылками. 7. Важные утверждения сверяются с кодом и конфигами. ## Когда делать полный аудит docs - перед релизом - после крупного этапа - после архитектурных изменений - когда docs начали расползаться ## Чего не делать - не создавать новый doc без нужды; - не дублировать одну тему в 3 местах; - не писать временные заметки в permanent docs; - не превращать README в техпомойку. 
docs/process/how-to-use-skills.md
# How to Use Skills ## Повседневная работа Обычно достаточно: 1. выполнить задачу 2. обновить локальные docs, если нужно 3. запустить quick-проверку docs 4. прогнать тесты Типовые команды в разговоре с агентом: - "Проверь docs по-быстрому" - "Прогони тесты" - "Обнови tracking" ## После крупного этапа Использовать: 1. `verify-docs-architecture` в `full-audit` 2. `verify-docs-architecture` в `full-sync` 3. `trace-source-of-truth` 4. `prepare-release` Типовые команды: - "Сделай полный аудит документации" - "Теперь выполни full-sync" - "Перепроверь source of truth для API, env и auth" - "Подготовь всё к релизу" ## Базовый набор skills - verify-docs-architecture - trace-source-of-truth - check-readme-role - update-tracking - run-tests - prepare-release ## Расширенный набор - verify-tool-contracts - change-prompts - run-evals 
6. Рабочий контур
work/now/README.md
# Active Work Здесь живут текущие рабочие материалы. ## Основные файлы - `current-task.md` — что сейчас делается - `plan.md` — план по шагам для заметной задачи - `evidence.md` — что выяснили, что проверили, какие риски ## Правила - не держать устаревшие задачи в `now/` - после завершения переносить в архив или схлопывать в постоянные docs 
work/now/current-task.md
# Current Task ## Название Короткое название текущей задачи. ## Цель Что хотим получить. ## Область изменения Какие части репозитория затрагиваются. ## Риски Что может поехать. ## Нужны ли docs Да / Нет / Возможно ## Нужен ли full doc audit Да / Нет 
work/now/plan.md
# Plan ## Шаги 1. ... 2. ... 3. ... ## Проверки - ... - ... ## Ожидаемые файлы - ... - ... 
work/now/evidence.md
# Evidence ## Что проверено - ... - ... ## Что подтверждено кодом - ... - ... ## Что пока предположительно - ... - ... ## Что обновлено - код - docs - tests - configs ## Остаточные риски - ... 
7. Базовые конфиги
.gitignore
# Node node_modules/ dist/ build/ .next/ coverage/ # Python __pycache__/ .pytest_cache/ .venv/ venv/ *.pyc # Env .env .env.local .env.*.local # IDE .idea/ .vscode/ # OS .DS_Store Thumbs.db # Artifacts artifacts/tmp/ artifacts/generated/ # Logs *.log 
.env.example
APP_ENV=development APP_NAME=project-template APP_PORT=8000 WEB_PORT=3000 LOG_LEVEL=info API_BASE_URL=http://localhost:8000 PUBLIC_APP_URL=http://localhost:3000 
Makefile
bootstrap: \tbash scripts/bootstrap.sh test: \tbash scripts/test.sh docs-check: \tbash scripts/docs-check.sh release-check: \tbash scripts/release-check.sh 
scripts/bootstrap.sh
#!/usr/bin/env bash set -e echo "Bootstrap project" echo "Install dependencies for your stack here" 
scripts/docs-check.sh
#!/usr/bin/env bash set -e echo "Run documentation checks here" echo "Examples:" echo "- validate links" echo "- check docs presence" echo "- compare expected docs structure" 
scripts/test.sh
#!/usr/bin/env bash set -e echo "Run project tests here" 
scripts/release-check.sh
#!/usr/bin/env bash set -e echo "Run release readiness checks here" 
8. Skills
Ниже готовые SKILL.md тексты.
.codex/skills/verify-docs-architecture/SKILL.md
# Skill: verify-docs-architecture ## Purpose Проверить, что документация: - структурирована как дерево от простого к сложному; - соответствует актуальному коду и конфигам; - не содержит опасных противоречий, дублей и сирот; - остаётся понятной и навигационно связной; - не смешивает обзор, детали и рабочие материалы. ## Modes - `quick` - `full-audit` - `full-sync` ## Default behavior По умолчанию использовать только `quick`. `full-audit` и `full-sync` запускать только: - по явной команде; - перед release; - после крупного этапа; - после архитектурного рефакторинга; - при сильном drift документации. ## What to verify ### 1. Documentation layers Проверять, что документация разделена по слоям: - root overview - overview docs - technical detail docs - reference docs - ADR - working docs - archive ### 2. Root README role Проверять, что корневой README: - обзорный; - маршрутизирующий; - не перегружен техдеталями; - не содержит временных рабочих заметок. ### 3. Overview quality Проверять, что обзорные документы: - быстро вводят в тему; - не дублируют техдоки; - содержат ссылки на deeper docs. ### 4. Technical docs quality Проверять, что техдоки: - узкие и конкретные; - не пытаются быть сразу всем; - ссылаются на overview и смежные документы; - не расходятся с кодом. ### 5. Work docs separation Проверять, что временные материалы не смешаны с постоянной документацией. ### 6. Link integrity Проверять, что: - ключевые docs связаны ссылками; - нет важных сиротских документов; - у deep docs есть путь обратно к overview. ### 7. Source-of-truth alignment Сверять важные утверждения по: - code - schema - config - tests - routes - jobs - CI/deploy files ## Mode: quick ### Goal Локальная спокойная проверка без лишнего шума. ### Perform 1. Найти затронутую область. 2. Проверить ближайшие docs и индексные файлы. 3. Проверить очевидные broken links. 4. Проверить, не требует ли обновления README раздела. 5. Проверить, нет ли явного расхождения docs и code рядом с изменением. 6. Исправить только мелкие и очевидные проблемы. ### Do not - не проводить полный аудит репозитория; - не дробить docs без необходимости; - не запускать большую уборку; - не создавать новые документы, если достаточно поправить существующие. ## Mode: full-audit ### Goal Сделать полный анализ документации без агрессивной перестройки. ### Perform 1. Построить карту docs. 2. Классифицировать документы по ролям. 3. Найти перегруженные документы. 4. Найти дубли и сиротские файлы. 5. Проверить связность ссылок. 6. Проверить root README. 7. Проверить ключевые утверждения по source of truth. 8. Подготовить отчёт: - что хорошо; - что устарело; - что конфликтует; - что стоит объединить, вынести, архивировать. ### Output Короткий и понятный audit summary. ## Mode: full-sync ### Goal Сделать полный аудит и затем привести docs в порядок. ### Perform 1. Выполнить всё из `full-audit`. 2. Исправить broken links. 3. Вынести техдетали из root README в docs. 4. Разделить перегруженные документы при реальной необходимости. 5. Объединить явные дубли. 6. Переместить misplaced docs. 7. Архивировать или вычистить устаревшие рабочие материалы. 8. Обновить карты и навигационные ссылки. ## Rules 1. Не плодить новые документы без нужды. 2. Один документ — одна роль. 3. Сначала навести порядок в структуре, потом украшать. 4. При конфликте code > prose. 5. Важные утверждения должны быть проверяемыми. 6. Не превращать full-sync в бюрократический разгром. ## Success criteria - repo docs читаются сверху вниз; - root README остаётся обзорным; - overview docs реально ускоряют вход; - deep docs не висят в изоляции; - нет явной каши и drift; - после изменений навигация стала лучше, а не хуже. 
.codex/skills/trace-source-of-truth/SKILL.md
# Skill: trace-source-of-truth ## Purpose Перепроверить важные утверждения документации, планов или итогов по реальным источникам истины. ## Use when - меняется API - меняется auth - меняется config/env - меняется runtime behavior - делается full doc audit - есть риск, что docs устарели ## Sources of truth priority 1. Код 2. Схемы и контракты 3. Централизованные config modules 4. Тесты 5. CI/deploy files 6. Runtime entrypoints 7. Документация 8. Временные заметки ## Method 1. Выделить load-bearing claims. 2. Для каждого утверждения найти подтверждение. 3. Пометить: - verified - inferred - unverified - contradicted 4. При конфликте не замалчивать, а явно фиксировать. ## Output Краткий список: - что подтверждено; - что не подтверждено; - что требует ручного решения; - где docs расходятся с кодом. 
.codex/skills/check-readme-role/SKILL.md
# Skill: check-readme-role ## Purpose Следить, чтобы корневой README оставался обзорным, маркетингово-навигационным и не превращался в техническую свалку. ## Verify README должен содержать: - что это за продукт; - для кого он; - основные возможности; - быстрый старт; - карту дальнейшего чтения; - структуру репозитория на верхнем уровне. README не должен содержать: - большие implementation details; - временные планы; - рабочие заметки; - длинные edge-case dumps; - внутреннюю историю изменений. ## If violated - сократить README; - вынести deep details в `docs/`; - оставить в README ссылки на нужные документы; - не ломать обзорную роль README. 
.codex/skills/update-tracking/SKILL.md
# Skill: update-tracking ## Purpose Поддерживать `work/` в порядке без лишней бюрократии. ## Use when - задача больше локальной мелочи; - есть заметный этап работ; - нужна передача контекста; - есть риски забыть промежуточные выводы. ## Method 1. Обновить `work/now/current-task.md` 2. Если задача заметная — обновить `work/now/plan.md` 3. По ходу или в конце — обновить `work/now/evidence.md` 4. После завершения этапа: - архивировать временное; - или схлопнуть в постоянные docs. ## Rule Tracking должен помогать, а не душить. Не надо разводить громоздкий ритуал для мелкой правки. 
.codex/skills/run-tests/SKILL.md
# Skill: run-tests ## Purpose Единообразно запускать проверки без самодеятельности. ## Default Использовать canonical commands проекта: - `make test` - или скрипты из `scripts/` - или documented project commands ## Method 1. Определить, какие проверки релевантны изменению. 2. Сначала запустить минимально достаточный набор. 3. Перед крупным этапом или release — расширенный набор. 4. Сообщить, что именно запускалось и почему. ## Avoid - не запускать бессмысленно весь мир на микроправку; - не заявлять "всё проверено", если проверена только малая часть. 
.codex/skills/prepare-release/SKILL.md
# Skill: prepare-release ## Purpose Сделать короткую финальную проверку перед merge/release/handoff. ## Checklist 1. Код реализует заявленную цель. 2. Документация обновлена или явно не требует обновления. 3. Нет явных конфликтов docs и code. 4. Tracking закрыт или приведён в порядок. 5. Прогнаны релевантные проверки. 6. Нет висящих временных файлов, которые должны быть архивированы. 7. Есть краткое summary: - что сделано; - что изменено; - что осталось; - какие риски. ## Output Короткий release-readiness summary. 
.codex/skills/verify-tool-contracts/SKILL.md
# Skill: verify-tool-contracts ## Purpose Проверять, что tool contracts, schemas и runtime expectations не разъехались. ## Use when - меняются tools - меняются schemas - меняется формат agent outputs - появляются новые команды или structured reports ## Verify - schema matches implementation - docs match schema - examples are still valid - naming is consistent - no silent breaking changes 
.codex/skills/change-prompts/SKILL.md
# Skill: change-prompts ## Purpose Менять prompts аккуратно, не ломая поведение системы незаметно. ## Rules 1. Менять prompt только с понятной целью. 2. Явно фиксировать, что меняется: - tone - constraints - allowed behavior - required outputs 3. Проверять, не конфликтует ли prompt с policies. 4. После заметных изменений рекомендовать eval pass. 
.codex/skills/run-evals/SKILL.md
# Skill: run-evals ## Purpose Прогонять базовые eval scenarios для agent behavior. ## Use when - изменились prompts - изменились tool contracts - изменились policies - менялась логика response formatting ## Method 1. Выбрать smoke scenarios. 2. Прогнать критичные кейсы. 3. Сравнить ожидаемое и фактическое поведение. 4. Зафиксировать regressions и suspicious drift. 
9. Agent policies
agent/policies/approvals.yaml
version: 1 destructive_operations: require_explicit_approval: true operations: delete_files: explicit mass_docs_restructure: explicit schema_breaking_change: explicit prod_config_change: explicit 
agent/policies/budgets.yaml
version: 1 limits: max_full_repo_rewrites_per_task: 1 max_large_doc_restructures_without_request: 0 max_optional_full_audits_without_request: 0 
agent/policies/rate_limits.yaml
version: 1 checks: quick_doc_check_default: enabled full_doc_audit_default: disabled full_doc_sync_default: disabled 
agent/policies/redaction.yaml
version: 1 redact: - secrets - tokens - private_keys - prod_credentials 
10. Agent prompts
agent/prompts/system.md
# System Prompt Notes Агент должен: - поддерживать порядок, а не бюрократию; - не считать docs абсолютной истиной; - сохранять root README обзорным; - не запускать полный аудит без нужды; - по умолчанию выбирать лёгкий режим; - по явной команде уметь провести глубокую ревизию. 
agent/prompts/developer.md
# Developer Prompt Notes Предпочитаемый стиль работы: - структурно; - аккуратно; - без каши; - по папкам и файлам; - с деревом документации от простого к сложному; - с обязательными ссылками между docs; - с проверкой docs по коду после крупных этапов. 
11. CI-заготовки
.github/workflows/ci.yml
name: CI on: push: pull_request: jobs: basic-checks: runs-on: ubuntu-latest steps: - uses: actions/checkout@v4 - name: Show repo structure run: ls -la - name: Run tests run: bash scripts/test.sh 
.github/workflows/docs-check.yml
name: Docs Check on: pull_request: paths: - 'docs/**' - 'README.md' - 'AGENTS.md' - 'agent/**' - '.codex/skills/**' jobs: docs-check: runs-on: ubuntu-latest steps: - uses: actions/checkout@v4 - name: Run docs check run: bash scripts/docs-check.sh 
12. Как этим пользоваться на практике
Повседневная работа
На обычных задачах не надо включать тяжёлую машину.
Нормальный цикл:
• сделать задачу;
• при необходимости обновить локальные docs;
• прогнать quick doc check;
• прогнать релевантные тесты;
• при заметной задаче обновить tracking.
Примеры живых команд:
• "Сделай задачу и потом проверь docs по-быстрому"
• "Прогони тесты"
• "Обнови tracking по текущему этапу"
После большого этапа фич
Вот здесь как раз нужен усиленный режим.
Нормальный цикл:
• полный аудит docs;
• посмотреть проблемы;
• сделать sync;
• перепроверить source of truth;
• подготовить release summary.
Примеры команд:
• "Сделай полный аудит документации после этапа"
• "Теперь выполни full-sync"
• "Перепроверь source of truth для API, env и auth"
• "Подготовь всё к релизу"
Важный практический принцип
Не надо запускать full-audit и full-sync на каждый коммит.
Базовый режим:
• quick
Ручной тяжёлый режим:
• full-audit
• full-sync
Это и есть правильный баланс:
• без бюрократии в повседневной работе;
• с сильной генеральной уборкой по команде.
13. Минимально обязательный набор для старта
Если хочется не перегружать шаблон, то можно считать обязательными только:
• README.md
• AGENTS.md
• agent/OPERATING_CONTRACT.md
• docs/README.md
• docs/overview/
• docs/architecture/ideal-principles.md
• docs/process/documentation-governance.md
• work/now/*
• .codex/skills/verify-docs-architecture/SKILL.md
• .codex/skills/trace-source-of-truth/SKILL.md
• .codex/skills/check-readme-role/SKILL.md
• .codex/skills/update-tracking/SKILL.md
• .codex/skills/run-tests/SKILL.md
• .codex/skills/prepare-release/SKILL.md
Остальное можно считать усилителями.
14. Итоговая идея шаблона
Это не “enterprise-бюрократия”.
Это система, где:
• корень остаётся обзорным;
• документация имеет ясное дерево;
• временная работа не засоряет постоянные docs;
• агент не живёт в хаосе;
• на каждый день есть лёгкий режим;
• после большого этапа есть мощная команда на генеральную уборку и сверку с кодом.
Именно это делает шаблон удобным для реальных будущих проектов, а не просто красивым набором файлов.