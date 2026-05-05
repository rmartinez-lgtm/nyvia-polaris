from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.embeddings import embed_query
from services.vector_store import search
from services.llm import ask

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    top_k: int = 5
    filters: dict | None = None


class SourceChunk(BaseModel):
    source: str
    score: float
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")

    query_vector = embed_query(req.question)
    chunks = search(query_vector, top_k=req.top_k, filters=req.filters)

    if not chunks:
        return ChatResponse(
            answer="No tengo información sobre eso en la base de conocimiento de Nyvia.",
            sources=[],
        )

    answer = ask(req.question, chunks)
    sources = [
        SourceChunk(
            source=c.get("source", "desconocido"),
            score=round(c.get("score", 0), 4),
            text=c.get("text", "")[:300],
        )
        for c in chunks
    ]
    return ChatResponse(answer=answer, sources=sources)
