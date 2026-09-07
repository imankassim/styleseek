from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import close_pool, open_pool
from app.routers import health, products, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    open_pool()
    yield
    close_pool()


app = FastAPI(title="StyleSeek API", lifespan=lifespan)

# Local dev only — Next.js dev server origin. Revisited when Stage 15 introduces real
# deployment config instead of a hardcoded allowlist.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(products.router)
app.include_router(search.router)
