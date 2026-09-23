from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router

app = FastAPI(
    title="PNW Information Chatbot API",
    version="0.1.0",
    description="Public PNW general-information API that protects student privacy and requires source-backed answers.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
