# EXP32 — RRF hybrid retrieval

- **Role:** Rank-fusion baseline (architecture §14)
- **Status:** Rejected as the serving choice — see EXP34
- **Run:** `python experiments/EXP32_rrf_hybrid/run.py`
- **Evaluated against:** `evaluation/relevance_judgments.json`, `train`+`val` splits only

## Hypothesis

Combine EXP31 (BM25/EXP14) and EXP30 (vector, title embeddings) via Reciprocal Rank Fusion
(`search/fusion.py`) — the architecture's stated starting point for hybrid retrieval (ADR-1).
RRF uses only rank position, sidestepping the problem of BM25's unbounded score and cosine
similarity's bounded [-1, 1] score living on incomparable scales.

## Result

**ndcg@10 = 0.549, recall@50 = 0.707** (n=15).

| | ndcg@10 | recall@50 |
|---|---|---|
| BM25 alone (EXP31/14) | 0.755 | 0.693 |
| **RRF hybrid (this)** | **0.549** | **0.707** |

Median latency over 5 sample queries: 329ms (vs BM25 alone's ~200-300ms — the added cost is
query embedding, ~104ms measured directly, plus a second OpenSearch round trip).

## Finding

Recall improved (RRF does successfully pull in the extra candidates EXP30 showed vector search
finds), but ndcg@10 regressed sharply — a 27% relative drop. RRF treats both ranked lists as
equally trustworthy by rank position alone, but BM25 (ndcg 0.755) and vector search (ndcg 0.293)
are nowhere near equally reliable rankers here — folding in the much weaker list's rank
positions on equal footing drags down the strong list's precision at the top, exactly where
ndcg@10 is most sensitive.

## Decision

Rejected as configured — it improves recall but regresses the primary ranking-quality metric,
which architecture §17 gate G7 explicitly disallows ("improves agreed evidence *without*...
regressions"). Not moved to `discarded/`: it's the architecturally-specified starting point
(ADR-1) and directly motivated EXP33/34's fix (weight the two lists by how much to trust them,
rather than treating them as equals) — keeping it in `experiments/` preserves that reasoning
chain more legibly than filing it as a dead end.
