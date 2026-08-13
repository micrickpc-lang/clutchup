# ClutchUp

Production-oriented Telegram Mini App для поиска CS2-тиммейтов. Telegram `initData` проверяется только на backend, FACEIT подключается через OAuth 2.0 Authorization Code + PKCE, анкеты подбираются сервером по сохранённым фильтрам, а presence хранится в Redis с TTL.

## Архитектура

- `backend/` — FastAPI, SQLAlchemy 2 async, PostgreSQL, Redis, Aiogram, pooled httpx client и Alembic.
- `frontend/` — React 18, strict TypeScript, Vite, feature/page-based UI, Telegram SDK и Lucide icons.
- `cloudflare-worker/` — закрытый allowlist proxy к необходимым FACEIT Data/Auth paths.
- `docker-compose.yml` — PostgreSQL 16, Redis 7, API и Nginx frontend.

Frontend имеет пять разделов: поиск, матчи, профиль, статистика/фильтры и настройки. Отдельные экраны отвечают за карточку игрока, детали и новый взаимный матч.

## Быстрый запуск Docker

```bash
cp .env.example .env
# заполните все значения replace_with_* и смените пароль PostgreSQL
docker compose up --build
```

Nginx слушает `127.0.0.1:8080`. Публичный HTTPS reverse proxy должен направлять `clutchup.tech` на этот адрес. Backend при старте выполняет `alembic upgrade head`; ручной `create_all` не используется.

Проверка:

```bash
docker compose ps
curl http://127.0.0.1:8080/health
```

## Переменные окружения

Обязательные: `POSTGRES_PASSWORD`, `BOT_TOKEN`, `FACEIT_API_KEY`, `FACEIT_CLIENT_ID`, `FACEIT_CLIENT_SECRET`, `FACEIT_REDIRECT_URI`, `FRONTEND_URL`, `TELEGRAM_BOT_USERNAME`. Для Worker также задаются `FACEIT_PROXY_URL` и одинаковый секрет `FACEIT_PROXY_SECRET` / `PROXY_SECRET`.

`AUTH_MAX_AGE_SECONDS` управляет сроком Telegram initData (по умолчанию 3600), `OAUTH_STATE_TTL_SECONDS` — одноразовым OAuth-state, `PRESENCE_TTL_SECONDS` — online TTL. Реальные секреты нельзя добавлять в Git или frontend variables.

## FACEIT и Cloudflare Worker

1. В FACEIT Developers создайте API key и OAuth2 client с Authorization Code + PKCE.
2. Redirect URI должен в точности совпасть с `https://<domain>/api/faceit/oauth/callback`.
3. В consent screen укажите HTTPS URL сайта, privacy и terms.
4. Разверните `cloudflare-worker/worker.js`, добавьте encrypted secret `PROXY_SECRET` и запишите Worker URL/secret в backend `.env`.

Worker принимает только GET к нужным Data API paths, GET userinfo и POST token exchange. Он не является open proxy и не пересылает Cloudflare/private headers.

## Telegram Mini App

В BotFather задайте Web App URL `https://<domain>`. Пользователь должен открывать приложение из Telegram: обычный браузер не содержит подписанного `initData`. OAuth создаётся только после нажатия кнопки; после возврата профиль обновляется на `focus`/`visibilitychange`.

## Локальная разработка

```bash
cd frontend
npm ci
npm run dev

cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn main:app --reload
```

Vite проксирует `/api` на `localhost:8000`. Для API-запросов всё равно нужен валидный Telegram header.

## Проверки

```bash
cd frontend
npm run typecheck
npm run lint
npm run test
npm run build

cd backend
ruff check .
ruff format --check .
pytest -q
```

GitHub Actions выполняет те же проверки. Frontend tests покрывают loading/empty/error-facing UI, свайп, навигацию, фильтры матчей, профиль, статистику и OAuth user action. Backend tests проверяют valid/invalid/expired/future/malformed Telegram initData и критическую validation.

## Миграции

Текущая baseline migration `20260809_01` использует idempotent DDL для безопасного обновления legacy-базы. Новые изменения создавайте через Alembic и проверяйте сначала на копии production DB:

```bash
alembic revision --autogenerate -m "change"
alembic upgrade head
```

## Production и troubleshooting

- Cloudflare SSL/TLS: `Full (strict)` при валидном origin certificate.
- Не публикуйте PostgreSQL/Redis; Compose не открывает их порты.
- `401 X-Telegram-Init-Data` означает запуск вне Telegram или просроченный initData.
- `400 OAuth session expired` означает использованный/истёкший state — начните вход снова.
- Ошибки FACEIT 502/503 проверяйте по Worker logs, proxy secret и rate limits.
- Если контейнер backend не стартует, сначала смотрите `docker compose logs backend`; migration завершается до запуска Uvicorn.
