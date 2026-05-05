from openai import OpenAI
from config import settings

_client = OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = _client.embeddings.create(input=texts, model=settings.embedding_model)
    return [item.embedding for item in response.data]


def embed_query(query: str) -> list[float]:
    response = _client.embeddings.create(input=[query], model=settings.embedding_model)
    return response.data[0].embedding
