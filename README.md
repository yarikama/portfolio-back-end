# Portfolio Backend

Yarikama's Portfolio Backend API - Built with FastAPI

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL 17 (CloudNativePG on k3s)
- **ORM**: SQLAlchemy
- **Migration**: Alembic
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
| `MEMOIZATION_FLAG` | Load the ML model at startup | `True` (production sets `False`) |
| `MODEL_PATH`, `MODEL_NAME` | Where the ML model is loaded from | `./ml/model/`, `model.pkl` |

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
| `POST /api/v1/predict`, `GET /api/v1/health` | ML predictor and its self-check (see Known limitations) |

Lists return `{"data": [...], "pagination": {"total", "limit", "offset", "hasMore"}}` (categories: `data` only); single items return `{"data": {...}}`. Projects and lab notes use camelCase fields.

## Known Limitations

- **The ML predictor does not work in production.** The production image ships no model file (`ml/model/` holds only examples), so `POST /api/v1/predict` fails and `GET /api/v1/health`, which runs a real prediction as its check, returns `404 {"detail": "Unhealthy"}`. Use `/health` for liveness.

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
