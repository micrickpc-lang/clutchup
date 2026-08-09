# ClutchUp

Telegram Mini App для поиска тиммейтов в CS2 с Telegram-аутентификацией, FACEIT OAuth, подбором по ELO, свайпами и уведомлениями о взаимных матчах.

## Запуск

```bash
cp .env.example .env
docker compose up -d --build
```

Перед запуском заполните в `.env` токен Telegram-бота, FACEIT API/OAuth credentials и параметры Cloudflare Worker. Приложение доступно на порту `8080` loopback-интерфейса; публичный HTTPS reverse proxy должен направлять домен на `http://127.0.0.1:8080`.

## Состав

- `backend` — FastAPI, SQLAlchemy, Aiogram, Redis и FACEIT OAuth/API.
- `frontend` — React, TypeScript, Vite и Tailwind CSS.
- `cloudflare-worker` — защищённый FACEIT API proxy.
- `docker-compose.yml` — PostgreSQL, Redis, backend и frontend.

Файл `.env` и секреты не входят в репозиторий.
