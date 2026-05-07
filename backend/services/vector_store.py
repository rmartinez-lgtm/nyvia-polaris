from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from langfuse.decorators import observe, langfuse_context
from config import settings

# Cloud si QDRANT_URL está definido, local para desarrollo
_client = (
    QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    if settings.qdrant_url
    else QdrantClient(path="./qdrant_data")
)


def ensure_collection() -> None:
    existing = [c.name for c in _client.get_collections().collections]
    if settings.qdrant_collection not in existing:
        _client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
        )


def upsert_chunks(chunks: list[dict]) -> None:
    ensure_collection()
    points = [
        PointStruct(
            id=c["id"],
            vector=c["vector"],
            payload={k: v for k, v in c.items() if k not in ("id", "vector")},
        )
        for c in chunks
    ]
    _client.upsert(collection_name=settings.qdrant_collection, points=points)


@observe(name="qdrant-search")
def search(vector: list[float], top_k: int = 5, filters: dict | None = None) -> list[dict]:
    ensure_collection()
    qdrant_filter = None
    if filters:
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()
        ]
        qdrant_filter = Filter(must=conditions)

    response = _client.query_points(
        collection_name=settings.qdrant_collection,
        query=vector,
        limit=top_k,
        query_filter=qdrant_filter,
        with_payload=True,
    )

    results = [{"score": r.score, **r.payload} for r in response.points]

    langfuse_context.update_current_observation(
        metadata={
            "top_k": top_k,
            "num_results": len(results),
            "sources": [r.get("source", "unknown") for r in results],
            "scores": [round(r.get("score", 0), 4) for r in results],
        }
    )

    return results
