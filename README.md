# OPPO KZ Data Platform

Современный стек FastAPI + React для управления данными продаж OPPO Казахстан. Этот шаблон готов к продакшену: Postgres/SQLite, Alembic, JWT, RBAC, WebSocket-уведомления и e2e тесты.

## 🚀 Quickstart (2 минуты)
1. Склонируйте репозиторий и установите Python 3.11+, Node.js 18+.
2. Backend:
   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp ../.env.example .env
   alembic upgrade head
   python -m app.db.seed
   uvicorn app.main:app --reload
   ```
3. Frontend:
   ```bash
   cd frontend
   cp .env.example .env
   npm install
   npm run dev
   ```
4. Откройте http://localhost:5173 и войдите `admin@oppo.kz / Admin123!`.

## ⚙️ Конфигурация и миграции
- Используйте `.env` для переключения профилей dev/test/prod. Пример:
  ```env
  APP_VERSION=0.1.0
  DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/oppo
  SECRET_KEY=super-secret
  CORS_ORIGINS=https://admin.oppo.kz,https://metabase.oppo.kz
  ENABLE_BONUSES=false
  ENABLE_MESSAGES=false
  ```
- Новые миграции: `alembic revision -m "message" --autogenerate` и `alembic upgrade head`.
- Сиды: `python -m app.db.seed` добавит 200 товаров и admin-аккаунт.

## 🔐 Аутентификация и RBAC
- JWT access (15 минут) + refresh (7 дней).
- Роли: `admin`, `office`, `supervisor`, `promoter`.
- REST/WS проверяют права на сервере. При подключении WS передайте `?token=...`.
- Рекомендуемый фронтовый backoff при переподключении WS: 1s, 2s, 5s, 10s с джиттером.

## 🛠️ API и WebSocket
- CRUD `/api/v1/products` с пагинацией, фильтрами (eq, contains, between, in, bool) и сортировкой.
- Единый формат ошибок: `{ "error_code", "message", "details" }`.
- WS `/api/v1/ws/products` отправляет события `product.created|updated|deleted`.

## ✅ Чек-лист качества
- Тесты: `cd backend && pytest`.
- Линтеры: `ruff check .`, `black --check .`, `cd frontend && npm run lint`.
- Рекомендованный CI: GitHub Actions (pytest + ruff/black + eslint/prettier), Dependabot.

## 🖥️ Снимки экрана
- Login
- Products Table
- Product Edit (демо через React state)

## 🩺 Troubleshooting
- "database is locked" — для SQLite используйте `PRAGMA journal_mode=WAL` или Postgres.
- 401 при логине — убедитесь, что сид выполнен и SECRET_KEY совпадает.
- WS отваливается — проверьте токен и включите экспоненциальный backoff.

## 🏗️ Деплой на Render
- Backend: `export PYTHONPATH="$(pwd)" && alembic -c alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Frontend: `cd frontend && npm i && npm run build`
- ENV: `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, `VITE_API_URL=https://<backend-host>`, `APP_VERSION`.
