from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, eval

app = FastAPI(title="Nyvia Brain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(eval.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "nyvia-brain"}
