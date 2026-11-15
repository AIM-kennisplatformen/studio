"""Shared JSON value type for data crossing serialization boundaries."""

type JsonValue = (
    str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
)
