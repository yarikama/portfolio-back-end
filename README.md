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
make deploy     # 啟動開發環境
make logs       # 查看 logs
make shell      # 進入容器
make rebuild    # 重建 image（新增依賴後）
make down       # 停止容器
```

### Database Migrations

```bash
# 在容器內執行 (make shell)
alembic upgrade head                              # 執行 migration
alembic revision --autogenerate -m "description"  # 建立 migration
alembic downgrade -1                              # 回滾一版
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
