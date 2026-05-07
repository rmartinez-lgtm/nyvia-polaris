from openai import OpenAI
from langfuse.decorators import observe, langfuse_context
from config import settings

_client = OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = _client.embeddings.create(input=texts, model=settings.embedding_model)
    return [item.embedding for item in response.data]


@observe(name="embed-query")
def embed_query(query: str) -> list[float]:
    langfuse_context.update_current_observation(
        input=query,
        metadata={"model": settings.embedding_model},
    )
    response = _client.embeddings.create(input=[query], model=settings.embedding_model)
    return response.data[0].embedding
