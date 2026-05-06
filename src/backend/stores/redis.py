import json
import dataclasses
from typing import List
from redis.asyncio import Redis
from loguru import logger

from backend.models.chat_message import ChatMessage
from backend.stores.abstract_store import AbstractStore

class RedisStore(AbstractStore):
    def __init__(self):
        super().__init__()
        self.redis: Redis | None = None
        self.expiration_time: int | None = None

    def _ensure_connected(self) -> None:
        super()._ensure_connected()
        assert self.redis is not None

    async def _connect_impl(self, config_dict: dict) -> None:
        url = config_dict["redis_url"]
        self.expiration_time = config_dict["redis_expiration_time"]
        self.redis = Redis.from_url(url, decode_responses=True)
        logger.info(f"✓ Connected to Redis at {url}")

    async def _close_impl(self) -> None:
        if self.redis:
            await self.redis.close()
            logger.info("✓ Closed Redis connection")

    def _key(self, session_id: str) -> str:
        return f"chat_history:{session_id}"

    async def store_message(self, session_id: str, message: ChatMessage) -> None:
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
        self._ensure_connected()
        assert self.redis is not None

        key = self._key(session_id)
        start = -limit if limit > 0 else 0
        items = await self.redis.lrange(key, start, -1)
        if not items:
            return []
            
        return [ChatMessage(**json.loads(item)) for item in items]


redis_store = RedisStore()
