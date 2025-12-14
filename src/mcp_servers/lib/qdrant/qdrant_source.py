import os

import torch
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny
from sentence_transformers import SentenceTransformer
from typing import Any, Dict, List


class QdrantSource:
    def __init__(
        self, qdrant_host: str, qdrant_port: int, qdrant_collection: str
    ) -> None:
        load_dotenv()
        self.qdrant = QdrantClient(
            host=qdrant_host, port=qdrant_port, check_compatibility=False
        )

        model_name = os.getenv("EMBEDDING_MODEL", "jinaai/jina-embeddings-v3")
        self.embedding_model = SentenceTransformer(model_name, trust_remote_code=True)
        self.embedding_model.eval()
        # Configuration
        self.collection = qdrant_collection
        pass

    def query_all(self, query_text: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve semantically similar chunks from Qdrant using local Jina embeddings."""
        with torch.no_grad():
            embedding = self.embedding_model.encode(
                [query_text], convert_to_numpy=True, normalize_embeddings=True
            )[0]
            results = self.qdrant.search( # type: ignore[attr-defined]
                collection_name=self.collection,
                query_vector=embedding.tolist(),
                limit=limit,
            )
            return [
        (r.payload or {}) | {"score": float(r.score)} for r in results ]

    def query_on_subset(
        self, question: str, subset: list[str], limit: int = 30
    ) -> list[dict]:
        with torch.no_grad():
            embedding = self.embedding_model.encode(
                [question], convert_to_numpy=True, normalize_embeddings=True
            )[0]

        filt = Filter(
            must=[
                FieldCondition(
                    key="zotero_hash",
                    match=MatchAny(any=subset),  # <-- FIXED
                )
            ]
        )

        results = self.qdrant.search( # type: ignore[attr-defined]
            collection_name=self.collection,
            query_vector=embedding.tolist(),
            limit=limit,
            query_filter=filt,
        )

        return [ (r.payload or {}) | {"score": float(r.score)}   for r in results ]

