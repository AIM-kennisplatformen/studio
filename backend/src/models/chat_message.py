import time
from dataclasses import dataclass, field
from typing import Literal

@dataclass
class ChatMessage:
    """
    Model representing a single turn in a chat interaction.
    """
    role: Literal["user", "assistant", "system"]
    message: str
    timestamp: float = field(default_factory=time.time)
