from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    """Convert a string to camel case."""
    components = string.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
