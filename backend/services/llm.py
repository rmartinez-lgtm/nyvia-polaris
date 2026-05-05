from openai import OpenAI
from config import settings

_client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """Eres Nyvia Brain, el asistente de conocimiento interno de Nyvia, consultora de data y estrategia.

Tu rol:
- Responder preguntas usando EXCLUSIVAMENTE los fragmentos de contexto que se te proveen.
- Citar la fuente de cada afirmación con el formato [Fuente: nombre_archivo, sección].
- Si la información no está en el contexto, decir claramente: "No tengo información sobre eso en la base de conocimiento de Nyvia."
- Ser preciso, directo y profesional.

Idioma: responde siempre en el mismo idioma de la pregunta."""


def ask(question: str, context_chunks: list[dict]) -> str:
    context_text = "\n\n---\n\n".join(
        f"[Fuente: {c.get('source', 'desconocido')}]\n{c.get('text', '')}"
        for c in context_chunks
    )

    response = _client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Contexto disponible:\n{context_text}\n\n---\n\nPregunta: {question}"},
        ],
    )
    return response.choices[0].message.content
