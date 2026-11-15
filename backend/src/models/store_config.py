from typing import TypedDict


class RedisConfig(TypedDict):
    redis_url: str
    redis_expiration_time: int | None


class PostgresConfig(TypedDict):
    postgres_url: str
