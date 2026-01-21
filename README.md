# Portfolio Backend

Yarikama's Portfolio Backend API - Built with FastAPI

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Package Manager**: uv

## Quick Start

### Prerequisites

- Docker & Docker Compose
- uv (Python package manager)

### Development Setup

```bash
# 1. Clone and enter the project
cd portfolio-back-end

# 2. Copy environment variables
cp .env.example .env

# 3. Start development environment
docker compose up --build

# 4. Run database migrations (in another terminal)
docker compose exec app alembic upgrade head
```

The API will be available at: http://localhost:8080

## Development Commands

### Docker

```bash
# Start development environment
docker compose up

# Start with rebuild (after adding new dependencies)
docker compose up --build

# Stop all containers
docker compose down

# View logs
docker compose logs -f app

# Enter the app container
docker compose exec app bash
```

### Database Migrations (Alembic)

```bash
# Run all pending migrations
docker compose exec app alembic upgrade head

# Create a new migration (after modifying models)
docker compose exec app alembic revision --autogenerate -m "description of changes"

# Rollback one migration
docker compose exec app alembic downgrade -1

# View current migration version
docker compose exec app alembic current

# View migration history
docker compose exec app alembic history
```

### Dependencies

```bash
# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>

# Update lock file
uv lock

# After updating dependencies, rebuild the container
docker compose up --build
```

## API Documentation

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## Project Structure

```
app/
├── api/
│   └── routes/          # API endpoints
├── core/                # Config, logging, error handling
├── schemas/             # Pydantic models (API validation)
├── db/
│   ├── session.py       # Database connection
│   └── models/          # SQLAlchemy ORM models
├── services/            # Business logic
├── alembic/
│   └── versions/        # Migration files
└── main.py              # FastAPI application entry
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `SECRET_KEY` | JWT secret key | - |
| `DEBUG` | Enable debug mode | `False` |

## Production Deployment

```bash
# Build production image
docker build --target production -t portfolio-backend:prod .

# Run production container
docker run -p 8080:8080 --env-file .env.production portfolio-backend:prod
```
