# Model card: `hybrid_weighted_fusion_v1`

Architecture §8.1 "Model record", §18. Covers the live `/search` model_version as a whole
(retrieval + fusion + query understanding + eligibility + personalisation) rather than one
narrow ML artefact, because that combination — not any single component — is what a shopper
actually experiences and what the frozen configuration (ADR-3) refers to.

## Intended use

Ranks a fashion product catalogue (44,446 products, `paramaggarwal/fashion-product-images-small`
on Kaggle, MIT-licensed) in response to a free-text shopper query, for a research/learning
prototype demonstrating an evidence-led hybrid search methodology. **Not** intended for
production e-commerce traffic, real purchasing decisions, or any deployment involving real user
PII — see `docs/ethics/README.md`.

## Model components

| Component | What it is | Chosen by |
|---|---|---|
| Lexical retrieval | OpenSearch BM25, boosted fields (`title^3 category_text^2 colours_text^2 occasion^1 brand^1`), synonym expansion | EXP14 (Stage 8) |
| Semantic retrieval | Vector kNN, `BAAI/bge-small-en-v1.5` (fastembed/ONNX, 384-dim), title-only text representation | EXP22 (Stage 10) |
| Fusion | Weighted score fusion, min-max normalised, 90% lexical / 10% semantic | EXP34 (Stage 11) |
| Query understanding | Deterministic regex + controlled-vocabulary parser — colour/gender/price/size as hard filters | Stage 9 |
| Eligibility/diversity | Stock+size confirmation, (title, category, colour) duplicate control | Stage 12 |
| Personalisation | Same-session colour click boost, top-10 window only, gated on no explicit colour in the query | Stage 14 |
| Ranker | None (no learned re-ranking) | Stage 13, G8 = no |

## Training/tuning data

`evaluation/relevance_judgments.json` `train`+`val` splits (15 of 18 labelled queries, 230
graded products after two pooling passes — see `evaluation/relevance_rubric.md` rule 5 for why
pooling was necessary). No model weights were *trained* by this project for retrieval/fusion —
`BAAI/bge-small-en-v1.5` is a pretrained third-party embedding model used as-is (see its own
card below); the fusion weight (90/10) was chosen by grid comparison (EXP32/33/34), not learned.

## Evaluation

- **Development numbers** (train+val, n=15, used to choose this configuration over alternatives):
  ndcg@10 0.765, recall@50 0.721 (EXP34) vs BM25 alone (EXP14) 0.755/unreported and vector alone
  (EXP30) 0.293.
- **Held-out** (test split, n=3, never used to tune anything): ndcg@10 0.660, recall@50 0.667 —
  see `evaluation/final_evaluation.md` for the honest small-n reading of this number.
- **Live production metrics** (real accumulated dev/test traffic, `monitoring/report.py`): p50
  latency ~320ms, p95 ~1042ms, fallback rate ~5%, zero-result rate ~9%.

## Known limitations

- **Typo queries score near zero.** EXP13 measured fuzzy matching and found it regressed every
  other query type more than it fixed typos — deliberately not handled. A shopper who
  misspells will get poor results.
- **Category/occasion are not hard filters**, only surfaced in `interpretation` — Stage 9 found
  filtering on them regressed relevance because catalogue tagging doesn't match how shoppers
  phrase things (e.g. every real blazer is tagged Formal/Casual, never "smart casual").
- **No learned ranking** — three model families were tried and rejected (Stage 13) for
  insufficient training data (178 rows). This is very likely to change the moment genuine
  interaction volume grows; it is not a permanent architectural position.
- **Personalisation is same-session only** — no cross-session profiling, no persistent identity,
  resets to cold-start-neutral on every new session (by design, architecture §11 privacy).
- **Evaluation judgment set is small** (18 labelled queries total) relative to catalogue size —
  every ndcg/recall number in this project, including the held-out one, should be read with that
  in mind.
- **Prices and stock are synthetic** (`is_synthetic_price`, `is_synthetic_variant`) — real for
  colour/category/title/brand, fabricated for anything Kaggle's catalogue didn't include.

## Ethical considerations

See `docs/ethics/README.md` for the full assessment (privacy, popularity/exposure bias,
provenance, no real-user testing). Summary: anonymous sessions only, no protected-characteristic
targeting, all synthetic fields disclosed rather than presented as real, no production traffic.

## Third-party model used

### `BAAI/bge-small-en-v1.5`

- **Publisher**: Beijing Academy of Artificial Intelligence (BAAI).
- **Role here**: sentence embedding model for semantic retrieval (title-only representation,
  EXP22). Not fine-tuned — used exactly as published, via `fastembed`'s ONNX runtime build.
- **Why this model**: architecture named it explicitly as the baseline embedding choice; EXP22's
  comparison against two alternative representations (all-metadata, labelled-structured) using
  the same model confirmed title-only was the best of the three tried, so the model itself was
  never compared against alternatives — only its input representation was.
- **Licence**: MIT (per the model's Hugging Face repository).
- **Known limitation carried into this project**: general-purpose sentence embeddings, not
  fashion-domain-tuned — EXP30 found it identifies relevant candidates BM25 misses entirely on
  some queries, but is not competitive as a standalone ranker (ndcg@10 0.293 vs BM25's 0.755),
  which is why it's a 10%-weighted contributor to fusion rather than the primary ranker.
