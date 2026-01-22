# Portfolio Backend

Yarikama's Portfolio Backend API - Built with FastAPI

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (Neon)
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Package Manager**: uv
- **Hosting**: GCP Cloud Run

## Quick Start

```bash
# 1. Install dependencies
make install

# 2. Run locally
make run
```

- API: http://localhost:8080
- Swagger: http://localhost:8080/docs

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
make test       # Run all tests
```

## Database

### Neon PostgreSQL (Production)

Database is hosted on [Neon](https://neon.tech) (free tier).

- **Project**: `yarikama-portfolio-backend`
- **Region**: `aws-us-east-1`

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

### GCP Cloud Run (Production)

Hosted on [GCP Cloud Run](https://cloud.google.com/run) (free tier).

```bash
make deploy-gcp   # One-click deploy to GCP Cloud Run
```

**Service URL**: https://portfolio-backend-790579792548.us-central1.run.app

**Prerequisites**:
1. Install [gcloud CLI](https://cloud.google.com/sdk/docs/install)
2. Login: `gcloud auth login`
3. Set Python for gcloud (add to `~/.zshrc`):
   ```bash
   export CLOUDSDK_PYTHON=/opt/homebrew/opt/python@3.12/bin/python3.12
   ```

### Manual Deployment

```bash
export CLOUDSDK_PYTHON=/opt/homebrew/opt/python@3.12/bin/python3.12

gcloud run deploy portfolio-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --project yarikama-portfolio
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

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `DEBUG` | Enable debug mode | No (default: False) |
| `MEMOIZATION_FLAG` | Load ML model on startup | No (default: False) |
| `ADMIN_USERNAME` | Admin login username | No |
| `ADMIN_PASSWORD_HASH` | Bcrypt hashed password | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | No (default: 30) |

Generate password hash:
```bash
make hash
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /docs` | Swagger UI |
| `GET /api/v1/projects` | List projects |
| `GET /api/v1/lab-notes` | List lab notes |
| `POST /api/v1/contact` | Submit contact form |
| `POST /api/v1/auth/token` | Get auth token |

## Free Tier Limits

| Service | Free Quota |
|---------|------------|
| **Neon** | 0.5 GB storage |
| **GCP Cloud Run** | 2M requests/month, 180K vCPU-sec |

## Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make run` | Run local dev server |
| `make test` | Run tests |
| `make lint` | Check code style |
| `make format` | Format code |
| `make deploy` | Deploy with Docker Compose |
| `make deploy-gcp` | Deploy to GCP Cloud Run |
| `make down` | Stop Docker containers |
| `make logs` | View Docker logs |
| `make shell` | Enter Docker container |
| `make hash` | Generate password hash |
| `make clean` | Clean cache files |
