import json
import dataclasses
from typing import List, Dict
import redis.asyncio as redis
from loguru import logger

from backend.config import config
from backend.models.chat_message import ChatMessage
from backend.stores.abstract_store import AbstractStore

class RedisStore(AbstractStore):
    def __init__(self):
        super().__init__()
        self.redis = None
        self.limit = config.get("chat_history_limit", 10)
        self.ttl = config.get("chat_history_ttl", 86400)

    def _ensure_connected(self) -> None:
        super()._ensure_connected()
        assert self.redis is not None

    async def _connect_impl(self, config_dict: dict | None = None) -> None:
        url = config["redis_url"]
        self.redis = redis.from_url(url, decode_responses=True)
        logger.info(f"✓ Connected to Redis at {url}")

    async def _close_impl(self) -> None:
        if self.redis:
            await self.redis.close()
            logger.info("✓ Closed Redis connection")

    def _key(self, session_id: str) -> str:
        return f"chat_history:{session_id}"

    async def store_message(self, session_id: str, message: ChatMessage) -> None:
        self._ensure_connected()
            
        key = self._key(session_id)
        new_item = json.dumps(dataclasses.asdict(message))
        
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.rpush(key, new_item)
            if self.limit > 0:
                pipe.ltrim(key, -self.limit, -1)
            pipe.expire(key, self.ttl)
            await pipe.execute()
    
    async def get_history(self, session_id: str) -> List[ChatMessage]:
        self._ensure_connected()
            
        key = self._key(session_id)
        items = await self.redis.lrange(key, 0, -1)
        if not items:
            return []
            
        return [ChatMessage(**json.loads(item)) for item in items]


redis_store = RedisStore()
