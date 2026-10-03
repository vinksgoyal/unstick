import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(title="Unstick")
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
