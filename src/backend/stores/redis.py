import json
import dataclasses
from typing import List
from redis.asyncio import Redis
from loguru import logger

from backend.models.chat_message import ChatMessage
from backend.stores.abstract_store import AbstractStore


class RedisStore(AbstractStore):
    """
    Redis-backed store for ephemeral chat history.

    Persists chat messages in Redis lists keyed by session id. The store is
    optimized for fast append and recent-history retrieval, with optional key
    expiration controlled by configuration.

    Conceptual model
    ----------------
    Session -> ordered Redis list of ChatMessages

    Identity
    --------
    Each session maps to one Redis key:
        chat_history:<session_id>

    Messages do not have independent Redis identities. Their order in the list
    is the source of truth for chat chronology.

    Stored data
    -----------
    Each list item stores a JSON-serialized ChatMessage:
        role
        message
        timestamp

    Behaviour
    ---------
    - connect() creates an async Redis client from the configured URL
    - store_message() appends to the end of the session list
    - get_history() returns messages in chronological order
    - limit selects the latest N messages while preserving chronological order
    - expiration, when configured, is refreshed after each stored message

    Consistency guarantees
    ----------------------
    - message append and expiration refresh run in a Redis transaction pipeline
    - reads only return complete JSON ChatMessage records
    - missing sessions return an empty history
    """

    def __init__(self) -> None:
        """Initialize Redis client state."""
        super().__init__()
        self.redis: Redis | None = None
        self.expiration_time: int | None = None

    def _ensure_connected(self) -> None:
        """Ensure the Redis client has been initialized."""
        super()._ensure_connected()
        assert self.redis is not None

    async def _connect_impl(self, config_dict: dict) -> None:
        """
        Connect to Redis using the configured URL and expiration policy.

        Parameters
        ----------
        config_dict
            Dictionary containing ``redis_url`` and ``redis_expiration_time``.
            Set ``redis_expiration_time`` to None to keep session histories
            indefinitely.

            Example::

                {
                    "redis_url": "redis://localhost:6379/0",
                    "redis_expiration_time": 86400,
                }
        """
        url = config_dict["redis_url"]
        self.expiration_time = config_dict["redis_expiration_time"]
        self.redis = Redis.from_url(url, decode_responses=True)
        logger.info(f"✓ Connected to Redis at {url}")

    async def _close_impl(self) -> None:
        """Close the Redis client if it is open."""
        if self.redis:
            await self.redis.close()
            logger.info("✓ Closed Redis connection")

    def _key(self, session_id: str) -> str:
        """Return the Redis key used for a session's chat history."""
        return f"chat_history:{session_id}"

    async def store_message(self, session_id: str, message: ChatMessage) -> None:
        """
        Append a chat message to a session history.

        The append and optional expiration refresh are executed in one Redis
        transaction pipeline.
        """
        self._ensure_connected()
        assert self.redis is not None

        key = self._key(session_id)
        new_item = json.dumps(dataclasses.asdict(message))

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.rpush(key, new_item)
            if self.expiration_time is not None:
                pipe.expire(key, self.expiration_time)
            await pipe.execute()

    async def get_history(self, session_id: str, limit: int = 0) -> List[ChatMessage]:
        """
        Retrieve chat history for a session in chronological order.

        When limit is greater than zero, only the latest limit messages are
        returned, still ordered from oldest to newest.
        """
        self._ensure_connected()
        assert self.redis is not None

        key = self._key(session_id)
        start = -limit if limit > 0 else 0
        items = await self.redis.lrange(key, start, -1)
        if not items:
            return []

        return [ChatMessage(**json.loads(item)) for item in items]


redis_store = RedisStore()
