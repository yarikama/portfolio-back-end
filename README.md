# Portfolio Backend

Yarikama's Portfolio Backend API - Built with FastAPI

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Package Manager**: uv

## Quick Start

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Start development environment
make deploy

# 3. Run database migrations
make shell
alembic upgrade head
```

API: http://localhost:8080
Swagger: http://localhost:8080/docs

## Development

```bash
make deploy     # Start dev environment
make logs       # View logs
make shell      # Enter container
make rebuild    # Rebuild image (after adding dependencies)
make down       # Stop containers
```

### Database Migrations

```bash
# Run inside container (make shell)
alembic upgrade head                              # Run migrations
alembic revision --autogenerate -m "description"  # Create migration
alembic downgrade -1                              # Rollback one version
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
└── main.py              # Application entry
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key |
| `ADMIN_USERNAME` | Admin login username |
| `ADMIN_PASSWORD_HASH` | Bcrypt hashed password |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry (default: 30) |

Generate password hash:
```bash
make hash
```

## Production

```bash
docker build --target production -t portfolio-backend:prod .
docker run -p 8080:8080 --env-file .env.production portfolio-backend:prod
```
