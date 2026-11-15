from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.models.chat_message import ChatMessage

ConfigT = TypeVar("ConfigT")


class AbstractStore(ABC, Generic[ConfigT]):
    """
    Abstract persistence layer for storing and retrieving ChatMessages.

    A Store represents a backend capable of pushing chat history logs
    and retrieving them per user.
    """

    def __init__(self) -> None:
        self._connected: bool = False
        self._connecting: bool = False

    async def connect(self, config: ConfigT) -> None:
        """
        Establish connection to the backend.

        This method is idempotent. Calling it multiple times must be safe.
        """
        if self._connected:
            return

        self._connecting = True
        try:
            await self._connect_impl(config)
            self._connected = True
        finally:
            self._connecting = False

    async def close(self) -> None:
        """Close connection to backend."""
        if not self._connected:
            return
        await self._close_impl()
        self._connected = False

    @abstractmethod
    async def _connect_impl(self, config: ConfigT) -> None:
        """Backend-specific connection logic."""
        raise NotImplementedError

    @abstractmethod
    async def _close_impl(self) -> None:
        """Backend-specific connection closing logic."""
        raise NotImplementedError

    def _ensure_connected(self) -> None:
        """Ensure connection has been successfully established."""
        if not (self._connected or self._connecting):
            raise RuntimeError(
                f"{self.__class__.__name__} used before connect() was called"
            )

    @abstractmethod
    async def store_message(self, session_id: str, message: ChatMessage) -> None:
        """
        Persist a message into the store.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_history(self, session_id: str, limit: int = 0) -> list[ChatMessage]:
        """
        Retrieve previous messages.

        Returns
        -------
        list[ChatMessage]
            list of chronologically ordered messages.
        """
        raise NotImplementedError
