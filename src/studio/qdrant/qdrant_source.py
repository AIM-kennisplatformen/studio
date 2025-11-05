import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import torch

class QdrantSource:
	def __init__(self, qdrant_host: str, qdrant_port: int, qdrant_collection: str) -> None:
		load_dotenv()
		self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port, check_compatibility=False)

		model_name = os.getenv("EMBEDDING_MODEL", "jinaai/jina-embeddings-v3")
		self.embedding_model = SentenceTransformer(model_name, trust_remote_code=True)
		self.embedding_model.eval()
		# Configuration
		self.collection = qdrant_collection
		pass

	def query_all(self, query_text: str, limit: int = 50) -> str:
		"""Retrieve semantically similar chunks from Qdrant using local Jina embeddings."""
		with torch.no_grad():
			embedding = self.embedding_model.encode(
				[query_text],
				convert_to_numpy=True,
				normalize_embeddings=True
				)[0]
			results = self.qdrant.search(
				collection_name=self.collection,
				query_vector=embedding.tolist(),
				limit=limit,
			)
			return [r.payload | {"score": float(r.score)} for r in results]
	
	def query_on_subset(self, question: str, subset: list[str], limit: int = 50) -> list[dict]:
		"""Retrieve semantically similar chunks from a subset of the collection. The subset is a list of hashes."""
		with torch.no_grad():
			embedding = self.embedding_model.encode(
				[question],
				convert_to_numpy=True,
				normalize_embeddings=True
			)[0]

		# Build filter to restrict search to the given subset of hashes
		filt = Filter(
			must=[
				FieldCondition(
					key="hash",
					match=MatchValue(value=subset)
				)
			]
		)

		results = self.qdrant.search(
			collection_name=self.collection,
			query_vector=embedding.tolist(),
			limit=limit,
			query_filter=filt,
		)

		return [r.payload | {"score": float(r.score)} for r in results]
