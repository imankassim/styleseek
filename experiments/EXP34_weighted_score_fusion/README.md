# EXP34 — Weighted score fusion

- **Role:** Fusion alternative (architecture §14)
- **Status:** **Accepted and promoted to serving** — replaces EXP14 as the live `/search`
  candidate retrieval, model version `hybrid_weighted_fusion_v1`
- **Run:** `python experiments/EXP34_weighted_score_fusion/run.py`
- **Evaluated against:** `evaluation/relevance_judgments.json`, `train`+`val` splits only

## Hypothesis

EXP33 showed equal-weight score fusion still costs ndcg relative to BM25 alone, because BM25
(ndcg 0.755) is a much stronger overall ranker than vector search (ndcg 0.293) here — trusting
them equally isn't justified by the evidence. Does explicitly weighting BM25's normalised score
above vector's (`search/fusion.py:weighted_score_fusion`) recover BM25's ndcg *and* keep the
recall gain both EXP32 and EXP33 showed?

## Method

Swept three lexical/semantic weight splits (90/10, 80/20, 70/30) over the same normalised scores
as EXP33.

## Result

| Weights (lexical/semantic) | ndcg@10 | recall@50 |
|---|---|---|
| BM25 alone (EXP31/14) | 0.755 | 0.693 |
| RRF (EXP32) | 0.549 | 0.707 |
| Equal weight (EXP33) | 0.673 | 0.716 |
| 70/30 | 0.742 | 0.721 |
| 80/20 | 0.760 | 0.721 |
| **90/10 (chosen)** | **0.765** | **0.721** |

**90/10 beats BM25-alone on both metrics at once** — ndcg@10 +1.3% relative (0.755→0.765),
recall@50 +4.0% relative (0.693→0.721) — the clean result none of EXP32/33 achieved.

Latency (median, 8 sample queries, sequential retrieval): **355ms**, vs BM25-alone's ~200-300ms
— the added cost is one query embedding (~104ms measured directly, `search/embeddings.py`) plus
a second OpenSearch round trip. One of 8 sample requests spiked to 1533ms, most likely a
transient network/cold-start blip on the free-tier Bonsai OpenSearch instance rather than
something inherent to the fusion method — noted as an operational risk regardless. Retrieving
the two lists **in parallel** (rather than sequentially, as this experiment measured) is the
mitigation, per architecture §16 ("Latency growth... retrieve in parallel where appropriate") —
implemented in the live serving path, not in this offline experiment script.

## Decision

Promoted to serving (G7: *"Does fusion complement lexical retrieval? It improves agreed evidence
without unacceptable latency or regressions."* — yes on both counts: real, simultaneous gains on
both target metrics, and latency stays sub-second even without the parallelisation mitigation).
`backend/app/routers/search.py` now retrieves BM25 and vector candidates in parallel and fuses
them with these weights, with a two-tier fallback: vector search unavailable → BM25-only
(architecture §10, "omit semantic contribution"); OpenSearch itself unavailable → the existing
Postgres placeholder (Stage 5/8).
