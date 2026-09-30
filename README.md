# Portfolio Backend

Yarikama's Portfolio Backend API - Built with FastAPI

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL 17 (CloudNativePG on k3s)
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Rate limiting**: Redis (Lua scripts)
- **Package Manager**: uv
- **Hosting**: k3s on a home server, exposed through Cloudflare Tunnel

## Quick Start

```bash
make install                  # dependencies; also creates .env.local and .env.prod from .env.example
cp .env.example .env          # make run reads .env
docker-compose up -d db       # local PostgreSQL on :5432 (user/password postgres, database app)
make run                      # API with hot reload
```

- API: http://localhost:8080
- Swagger: http://localhost:8080/docs

Which env file is read depends on how the app starts: `make run` (and anything run from the repo root) reads `.env`; the Docker stack (`make deploy`) reads `.env.<ENV>`, `.env.local` by default. `.env.prod` is the source for the production Secret (see Deployment). All three are gitignored.

## Development

### Local Development (Recommended)

```bash
make install    # Install dependencies
make run        # Start dev server with hot reload
make test       # Run tests
make lint       # Check code style
make format     # Auto-format code
```

### Docker Development

```bash
make deploy     # Start dev environment with Docker
make logs       # View container logs
make shell      # Enter container shell
make rebuild    # Rebuild image (after adding dependencies)
make down       # Stop containers
```

## Testing

```bash
docker-compose up -d db
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app make test
```

Most tests are self-contained; `tests/test_project_order.py` needs a real PostgreSQL (it defaults to `localhost:5432/test_db`, which the compose database does not create, hence the `DATABASE_URL`). CI runs the suite on Python 3.10, 3.11 and 3.12 against a PostgreSQL service container.

The rate-limit tests run their Lua scripts in fakeredis by default. Set `REDIS_TEST_URL=redis://localhost:6379/15` to run them against a real Redis instead (CI does); that database is flushed.

## Database

### PostgreSQL (Production)

PostgreSQL 17 runs on the k3s cluster, managed by [CloudNativePG](https://cloudnative-pg.io). WAL is archived continuously and a base backup is taken daily to the Cloudflare R2 bucket `yarikama-db-backups`, so the database can be restored to any point in the last 30 days. Manifests and the restore runbook live in the homelab repo under `apps/portfolio-db`.

### Migrations

```bash
# Run migrations (local)
DATABASE_URL="your-database-url" PYTHONPATH=app uv run alembic -c app/alembic.ini upgrade head

# Create new migration
DATABASE_URL="your-database-url" PYTHONPATH=app uv run alembic -c app/alembic.ini revision --autogenerate -m "description"

# Rollback one version
DATABASE_URL="your-database-url" PYTHONPATH=app uv run alembic -c app/alembic.ini downgrade -1
```

## Deployment

Production runs on a single-node k3s cluster and is served at `https://api.yarikama.com` through a Cloudflare Tunnel. The Kubernetes manifests, secret tooling and runbooks live in the private [homelab](https://github.com/yarikama/homelab) repo.

Deploys are automatic: **merging to `main` is the deploy.**

1. CI runs lint and tests, then builds the production image for `linux/amd64` and pushes it to GHCR as `ghcr.io/yarikama/portfolio-backend:sha-<short>` and `latest`.
2. The `deploy` job commits the new tag to `apps/portfolio-backend/kustomization.yaml` in the homelab repo. It authenticates with a deploy key held in the `production` environment, which only `main` can use.
3. Argo CD picks up that commit within about three minutes and rolls the pods; the new pod must pass `/health` before the old one stops, so there is no downtime.

Merge to live takes about five minutes. To roll back, `git revert` the `deploy(portfolio-backend): sha-…` commit in the homelab repo; `kubectl rollout undo` does not stick, because Argo CD restores what Git says.

Production configuration is a Sealed Secret in the homelab repo, generated from `.env.prod` by `scripts/create-secret.sh` there; `DATABASE_URL` is not part of it and comes from the CloudNativePG-generated Secret instead.

The database is PostgreSQL on the same cluster, managed by CloudNativePG, with continuous backups to Cloudflare R2.

Database migrations run on their own: the pod's init container runs `alembic upgrade head` before the API starts. To run Alembic by hand against production, run it inside the pod, which already has the right `DATABASE_URL`:

```bash
kubectl -n portfolio exec deploy/portfolio-backend -c api -- alembic -c alembic.ini current
```

## Project Structure

```
app/
├── api/
│   ├── dependencies/    # Auth, etc.
│   └── routes/          # API endpoints
├── core/                # Config, security
├── schemas/             # Pydantic models
├── db/
│   ├── session.py       # Database connection
│   └── models/          # SQLAlchemy models
├── alembic/             # Database migrations
└── main.py              # Application entry
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string. In production it comes from CloudNativePG, not from `.env.prod` | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT signing key; changing it logs everyone out | empty (set it) |
| `ADMIN_USERNAME` | Admin login username | `admin` |
| `ADMIN_PASSWORD_HASH` | bcrypt hash of the admin password (`make hash`) | empty (set it) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `30` |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL` | Cloudflare R2, for image uploads | bucket `yarikama-portfolio-backend` |
| `DEBUG` | Debug mode | `False` |
| `REDIS_URL` | Redis for rate limits, e.g. `redis://:password@host:6379/0`; empty turns rate limiting off | empty |
| `METRICS_PORT` | Serve Prometheus metrics on this port (kept off the API port, so the public Ingress never exposes them); `0` turns them off | `0` |
| `AUTOCOMPLETE_URL` | OpenAI-compatible completions server for note autocomplete; empty disables it (503) | empty |
| `AUTOCOMPLETE_MODEL`, `AUTOCOMPLETE_MODEL_VERSION` | Model name to request, and the version recorded with each suggestion | `autocomplete`, `unknown` |
| `AUTOCOMPLETE_MIN_TOKEN_PROB` | Suggestions stop at the first token less likely than this | `0.5` |
| `AUTOCOMPLETE_FREQUENCY_PENALTY`, `AUTOCOMPLETE_PRESENCE_PENALTY` | Discourage repeating what the suggestion itself already wrote (not the note); a suggestion is also cut where it starts repeating the text before it | `2.0`, `1.0` |

`make hash` prompts for the admin password without echoing it, asks for it twice, and can write the hash into `.env.local`.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness, used by Kubernetes probes and uptime monitoring: `{"status": "ok"}` |
| `GET /docs`, `GET /redoc` | Interactive API docs |
| `POST /api/v1/auth/login` | `{"username", "password"}` → `{"access_token", "token_type"}` |
| `GET /api/v1/projects`, `GET /api/v1/projects/{slug}` | Published projects, in display order |
| `GET /api/v1/lab-notes`, `GET /api/v1/lab-notes/{slug}`, `GET /api/v1/lab-notes/tags` | Published lab notes |
| `GET /api/v1/categories` | Project categories |
| `POST /api/v1/contact` | Submit the contact form |
| `/api/v1/admin/...` | Create, edit, reorder and delete content, list contact messages, upload images. Needs `Authorization: Bearer <token>` |
| `POST /api/v1/admin/complete` | Note autocomplete: `{"prefix", "title", "noteId"}` → `{"id", "suggestion"}` (empty when the model is unsure or unavailable). Admin only |
| `POST /api/v1/admin/complete/{id}/feedback` | `{"outcome": "accepted" \| "rejected" \| "ignored", "acceptedChars"}`, recorded once per suggestion |

### Rate limits

Per visitor (the `CF-Connecting-IP` address that Cloudflare sets; IPv6 grouped by /64), kept in Redis so every replica shares them. Over a limit the API answers `429` with `Retry-After` in seconds and a readable `detail`.

| Rule | Limit | Algorithm | If Redis is down |
|------|-------|-----------|------------------|
| Login | 5 attempts per 15 minutes; a successful login clears the count | Sliding log | Refuse (`503`) |
| Contact form | 3 messages per hour | Sliding log | Allow |
| Every other `/api/` request except `/api/v1/admin/*` and preflights | Bursts of 60, then 1 per second | Token bucket | Allow |

Design and trade-offs: homelab `docs/11-rate-limiting.md`.

### Caching

`GET` on projects, lab notes and categories answers with an `ETag` and `Cache-Control: public, max-age=0, s-maxage=60, stale-while-revalidate=600`: browsers revalidate each time (a `304` when nothing changed), and Cloudflare keeps a copy for a minute. These responses carry `Access-Control-Allow-Origin: *`, because Cloudflare's cache ignores `Vary: Origin`. Edits in the admin show up publicly within about a minute.

Lists return `{"data": [...], "pagination": {"total", "limit", "offset", "hasMore"}}` (categories: `data` only); single items return `{"data": {...}}`. Projects and lab notes use camelCase fields.

## Known Limitations

- The `request_logs` table is left over from a removed ML predictor. It is empty and unused; the model stays only so Alembic does not propose dropping it.

## Free Tier Limits

| Service | Free Quota |
|---------|------------|
| **Cloudflare R2** | 10 GB storage (uploaded images and database backups) |

## Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make run` | Run local dev server |
| `make test` | Run tests |
| `make lint` | Check code style |
| `make format` | Format code |
| `make deploy` | Start the local Docker Compose stack (not production; see Deployment) |
| `make down` | Stop Docker containers |
| `make logs` | View Docker logs |
| `make shell` | Enter Docker container |
| `make hash` | Generate the admin password hash (hidden input) |
| `make clean` | Clean cache files |
