# Stage 15 (architecture §20 "containers"). run.py's Windows-specific asyncio policy patch is a
# no-op on this Linux base image, so uvicorn is invoked directly rather than via run.py.
#
# Build from the repo root so this can COPY only the backend/ subtree:
#   docker build -f backend/Dockerfile -t styleseek-backend .
# Run (needs DATABASE_URL at minimum; OPENSEARCH_URL and CORS_ORIGINS are optional -- see
# app/config.py):
#   docker run -p 8000:8000 -e DATABASE_URL=... -e OPENSEARCH_URL=... styleseek-backend

FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

# Bakes the embedding model into the image at build time (same cache_dir fastembed resolves at
# runtime) so a fresh container doesn't pay a network download on first search request -- see
# app/semantic.py's preload_model docstring.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5', threads=1)"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
