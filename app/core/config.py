import logging
import sys

from core.logging import InterceptHandler
from loguru import logger
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

API_PREFIX = "/api"
VERSION = "0.1.0"
DEBUG: bool = config("DEBUG", cast=bool, default=False)
MAX_CONNECTIONS_COUNT: int = config("MAX_CONNECTIONS_COUNT", cast=int, default=10)
MIN_CONNECTIONS_COUNT: int = config("MIN_CONNECTIONS_COUNT", cast=int, default=10)
SECRET_KEY: Secret = config("SECRET_KEY", cast=Secret, default="")
MEMOIZATION_FLAG: bool = config("MEMOIZATION_FLAG", cast=bool, default=True)
DATABASE_URL: str = config("DATABASE_URL", default="sqlite:///./app.db")

PROJECT_NAME: str = config("PROJECT_NAME", default="Portfolio-Back-End")

# Auth configuration
ADMIN_USERNAME: str = config("ADMIN_USERNAME", default="admin")
ADMIN_PASSWORD_HASH: str = config("ADMIN_PASSWORD_HASH", default="")
ACCESS_TOKEN_EXPIRE_MINUTES: int = config(
    "ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=30
)

# logging configuration
LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    handlers=[InterceptHandler(level=LOGGING_LEVEL)], level=LOGGING_LEVEL
)
logger.configure(handlers=[{"sink": sys.stderr, "level": LOGGING_LEVEL}])

MODEL_PATH = config("MODEL_PATH", default="./ml/model/")
MODEL_NAME = config("MODEL_NAME", default="model.pkl")
INPUT_EXAMPLE = config("INPUT_EXAMPLE", default="./ml/model/examples/example.json")

# R2 Storage configuration
R2_ACCOUNT_ID: str = config("R2_ACCOUNT_ID", default="")
R2_ACCESS_KEY_ID: str = config("R2_ACCESS_KEY_ID", default="")
R2_SECRET_ACCESS_KEY: str = config("R2_SECRET_ACCESS_KEY", default="")
R2_BUCKET_NAME: str = config("R2_BUCKET_NAME", default="yarikama-portfolio-backend")
R2_PUBLIC_URL: str = config("R2_PUBLIC_URL", default="")
