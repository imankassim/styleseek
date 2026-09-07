"""Product text embeddings for semantic retrieval (architecture §9 "Offline training and
evaluation architecture" — "Embedding generation... run outside the live request; serving uses
versioned artefacts").

Model: BAAI/bge-small-en-v1.5 via fastembed (ONNX runtime, no torch dependency — a much smaller
local footprint, which mattered given this machine's tight disk space through Stage 4/8). 384
dimensions. Chosen over an API-based embedding service (OpenAI, etc.) specifically to avoid a
new external account/credential dependency for a Stage that doesn't need one — unlike Kaggle/
Neon/Bonsai, nothing here requires the user's own account.
"""

import os

from fastembed import TextEmbedding

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSIONS = 384
_THREADS = os.cpu_count() or 4

_model: TextEmbedding | None = None


def get_model() -> TextEmbedding:
    global _model  # noqa: PLW0603
    if _model is None:
        _model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME, threads=_THREADS)
    return _model


def embed_texts(texts: list[str], batch_size: int = 256) -> list[list[float]]:
    model = get_model()
    return [vec.tolist() for vec in model.embed(texts, batch_size=batch_size, parallel=_THREADS)]


def embed_query(text: str) -> list[float]:
    """bge models are trained with an instruction prefix for queries (not documents) —
    omitting it measurably hurts retrieval quality for this model family."""
    return embed_texts([f"Represent this sentence for searching relevant passages: {text}"])[0]


# Representations compared in EXP22/23/24 (architecture §14 "representation comparison").
# EXP21 ("description-only embeddings") is not implemented — the catalogue has no description
# field at all (every product.description is NULL, see database/ingest.py); embedding an empty
# string for all 44,446 products would be meaningless, not a real experiment. See
# docs/data_sheets/catalogue_data_sheet.md and EXP21's own README for the full reasoning.


def title_only_text(product: dict) -> str:
    return product["title"]


def all_metadata_text(product: dict) -> str:
    parts = [
        product["title"],
        product["brand"] or "",
        product["category"],
        " ".join(product["colours"] or []),
        product["occasion"] or "",
        product["gender"] or "",
    ]
    return " ".join(p for p in parts if p)


def labelled_structured_text(product: dict) -> str:
    fields = [
        ("Title", product["title"]),
        ("Brand", product["brand"]),
        ("Category", product["category"]),
        ("Colour", ", ".join(product["colours"] or []) or None),
        ("Occasion", product["occasion"]),
        ("Gender", product["gender"]),
    ]
    return " | ".join(f"{label}: {value}" for label, value in fields if value)
