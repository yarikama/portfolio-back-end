from pydantic import BaseModel


class AdminResponse(BaseModel):
    """Who is signed in to the admin area."""

    email: str
