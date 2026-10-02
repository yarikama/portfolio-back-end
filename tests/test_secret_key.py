import jwt
import pytest
from core import config
from core.security import (
    MIN_SECRET_LENGTH,
    InsecureSecretError,
    create_access_token,
    decode_access_token,
)
from fastapi.testclient import TestClient
from main import get_application

STRONG = "s" * MIN_SECRET_LENGTH


@pytest.mark.parametrize("weak", ["", "short", "s" * (MIN_SECRET_LENGTH - 1)])
def test_a_missing_or_short_key_signs_nothing(weak):
    with pytest.raises(InsecureSecretError):
        create_access_token({"sub": "admin"}, weak)


@pytest.mark.parametrize("weak", ["", "s" * (MIN_SECRET_LENGTH - 1)])
def test_a_missing_or_short_key_accepts_nothing(weak):
    # Signed with the weak key itself, as a forger would.
    forged = jwt.encode({"sub": "admin"}, weak or "x", algorithm="HS256")
    assert decode_access_token(forged, weak) is None


def test_a_strong_key_round_trips():
    token = create_access_token({"sub": "admin"}, STRONG)
    assert decode_access_token(token, STRONG)["sub"] == "admin"


@pytest.mark.parametrize(
    "setting, value", [("SECRET_KEY", ""), ("ADMIN_PASSWORD_HASH", "")]
)
def test_login_is_refused_when_misconfigured(monkeypatch, setting, value):
    monkeypatch.setattr(config, setting, value)
    response = TestClient(get_application()).post(
        "/api/v1/auth/login", json={"username": "admin", "password": "x"}
    )
    assert response.status_code == 503


def test_admin_routes_refuse_tokens_when_the_key_is_unset(monkeypatch):
    token = create_access_token({"sub": config.ADMIN_USERNAME}, str(config.SECRET_KEY))
    monkeypatch.setattr(config, "SECRET_KEY", "")
    response = TestClient(get_application()).get(
        "/api/v1/admin/ask/questions", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
