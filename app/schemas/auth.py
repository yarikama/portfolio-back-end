from pydantic import BaseModel


class LoginRequest(BaseModel):
    """
    Request schema for the login endpoint.
    Contains the username and password.
    """

    username: str
    password: str


class TokenResponse(BaseModel):
    """
    Response schema for the login endpoint.
    Contains the JWT access token and the token type.
    """

    access_token: str
    token_type: str = "bearer"
