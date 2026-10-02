from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

ALGORITHM = "HS256"
# HS256 wants a key at least as long as its hash output (RFC 7518, 3.2).
# Shorter, or empty because SECRET_KEY was left unset, anyone could forge an
# admin token: such a key signs and accepts nothing.
MIN_SECRET_LENGTH = 32


class InsecureSecretError(RuntimeError):
    """SECRET_KEY is unset or too short to sign tokens with."""


def secret_is_usable(secret: str) -> bool:
    return len(secret) >= MIN_SECRET_LENGTH


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify the password against the hashed password when people login.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """
    Get the hash of the password using bcrypt when people register.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(
    data: dict, secret_key: str, expires_delta: timedelta | None = None
) -> str:
    """
    Create an access token.

    """
    if not secret_is_usable(secret_key):
        raise InsecureSecretError(
            f"SECRET_KEY must be at least {MIN_SECRET_LENGTH} characters"
        )
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict | None:
    """
    Decode an access token.

    """
    if not secret_is_usable(secret_key):
        return None
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
