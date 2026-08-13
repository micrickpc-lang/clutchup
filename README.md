# ClutchUp

ClutchUp is a Telegram Mini App for finding open gaming parties: pick a game, set intent, request to join, and play.

Supported games:

- CS2
- VALORANT
- Standoff 2

FACEIT is an optional CS2 integration used to import nickname, rank, avatar and statistics. It is not required to create a ClutchUp profile or use Valorant/Standoff 2.

## Product flow

`Telegram identity → generic profile → game profile → open parties → join request → accepted membership`

The primary entities are `UserProfile`, `GameProfile`, `Party`, `PartyMember`, and `PartyRequest`. Legacy swipe/lobby endpoints remain temporarily available for older clients but the current frontend does not call them.

## Architecture

- `backend/`: FastAPI, async SQLAlchemy, PostgreSQL, Redis, Aiogram and Alembic.
- `frontend/`: React 18, strict TypeScript, Vite and Telegram SDK.
- `cloudflare-worker/`: allowlisted optional FACEIT proxy.
- `docker-compose.yml`: PostgreSQL, Redis, backend and Nginx frontend.

## Development

```bash
cd frontend
npm ci
npm run typecheck
npm run lint
npm run test
npm run build
```

Use `?demo=1` with the Vite development server for local UI preview. Demo fixtures are enabled only when `import.meta.env.DEV` is true and are never substituted in production.

```bash
cd backend
pip install -r requirements-dev.txt
alembic upgrade head
ruff check .
pytest -q
```

The migration `20260814_03_party_product.py` is additive. It creates the party-domain tables and backfills existing `User + CS2Profile` data into generic and CS2 game profiles. It intentionally does not drop legacy tables or production data. Test migrations on a database copy before production deployment.

## Configuration

Required core settings include PostgreSQL, Redis, Telegram bot credentials and `FRONTEND_URL`. FACEIT variables may be left empty. If FACEIT OAuth is enabled, client id, client secret, and redirect URI must be configured together.

`PARTY_TTL_HOURS` controls the lifetime of a party signal and defaults to six hours.
