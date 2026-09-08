from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_cors_origins
from app.db import close_pool, open_pool
from app.routers import events, health, products, search
from app.semantic import preload_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    open_pool()
    preload_model()  # so the first real search doesn't pay the ONNX model load cost
    yield
    close_pool()


app = FastAPI(title="StyleSeek API", lifespan=lifespan)

# Defaults to the local Next.js dev server; set CORS_ORIGINS (comma-separated) in deployment
# (Stage 15, see backend/Dockerfile) to the real deployed frontend origin instead.
# allow_credentials is needed so the anonymous session cookie (app/session.py) round-trips.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(products.router)
app.include_router(search.router)
app.include_router(events.router)
