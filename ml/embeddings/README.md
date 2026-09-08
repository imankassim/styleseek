# ml/embeddings/

Empty by design, not an oversight. Architecture §18's proposed structure puts embedding
experiments here, but the actual code (`search/embeddings.py`, used by
`experiments/EXP21-24_*` and `search/index_vectors.py`) lives under `search/` instead — the same
reasoning as `backend/app/semantic.py`'s self-containment: embedding generation is tightly
coupled to the OpenSearch indexing pipeline it feeds, not a standalone offline-training artefact
separate from it. See `docs/model_cards/hybrid_search_v1.md` for the representation this
produced (EXP22, title-only) and why.
