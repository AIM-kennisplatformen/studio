"""Response shapes for the assets endpoint."""

from typing import TypedDict

from src.models.auth import AuthentikUser


class AssetsCounts(TypedDict):
    """Counts of loaded knowledge graph data."""

    entities_count: int
    relations_count: int
    questions_count: int


class AssetsSuccess(TypedDict):
    """Successful assets response."""

    status: str
    user: AuthentikUser
    version: str
    data: AssetsCounts


class AssetsError(TypedDict):
    """Assets response when knowledge graph data is unavailable."""

    status: str
    message: str
    version: str
