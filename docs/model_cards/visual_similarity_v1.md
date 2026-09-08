# Model card: visual similarity (`GET /products/{id}/similar`)

Architecture §12 journey 16, "optional extensions... visual similarity" — an explicitly
separate, optional investigation, never rolled into the frozen core plan
([ADR-3](../decisions/3-freeze-serving-configuration.md)) or the evaluation-gated experiment
catalogue (§14, which has no entry for it). Built after Stage 16's conclusion, at the user's
direction to continue with the architecture's named optional extensions.

## What it does

Given a product, finds other catalogue products whose photo *looks* similar — not the same
category or attributes, purely visual: colour, silhouette, composition of the product photo
itself. Surfaced as a "Similar styles" section on the product detail page.

## How it works

- **Model**: `Qdrant/clip-ViT-B-32-vision` (CLIP ViT-B/32 image tower) via `fastembed`'s ONNX
  runtime — same no-torch convention as `app/semantic.py`'s text embeddings. 512-dim vectors.
- **Offline build**: `search/index_image_vectors.py` embeds every product's catalogue photo
  (44,441 of 44,446 products have one — see `docs/data_sheets/catalogue_data_sheet.md`) into its
  own OpenSearch index, `styleseek_products_v5_image_vectors` (hnsw/cosinesimil/lucene, same
  convention as `search/vector_mapping.py`). No embedding at request time.
- **Online**: `backend/app/visual_similarity.py`'s `find_similar_products` looks up the source
  product's already-stored vector and runs one kNN query against the same index, excluding the
  source itself. No user-supplied image, no ML runtime dependency in the backend at all.
- **Honest degradation**: a product with no catalogue photo, or the index/OpenSearch itself
  being unreachable, both report `available: false` with an empty result list — never a 500,
  same pattern as `/search`'s fallbacks.

## Evaluation

No ground truth exists for "is this visually similar" — `evaluation/relevance_judgments.json`
grades text-query relevance, not image similarity, and building a comparable rubric/judgment set
for this was out of scope for an optional extension. Evaluated qualitatively instead (same
approach as Stage 10's vector-only qualitative analysis, EXP30), spot-checking real results
across categories:

| Source product | Category | Top matches |
|---|---|---|
| Reebok Men Runtone Action Brown Sports Shoes | shoes | 5/5 matches also shoes (Skechers, Fila, Reebok, Nike) |
| Fastrack Men Analogue Plastic White Watch | watches | 5/5 matches also watches (Puma, Carrera, Esprit) |
| Palm Tree Girl's Blossom Drs Pink Dresses | dress | Matches mostly pink/magenta tops and dresses — colour-led, not category-led |
| Palm Tree Girls Sp Jace Sko White Skirts | bottomwear | Matches mostly other white-background flat garments across topwear/dress/shoes — background/colour-led |

**Finding, stated honestly**: match quality depends on the photo's composition. Structured,
3D objects photographed against a plain background (shoes, watches) stay reliably
within-category, because their shape and material dominate the embedding. Flat garment
photography (the majority of the catalogue) is dominated by garment colour and the shared white
background instead, pulling in visually-similar-but-differently-categorised items (a pink top
next to a pink dress) rather than staying strictly within category. This is a property of
general-purpose CLIP embeddings applied to this catalogue's photography style, not a bug in the
retrieval code — the same honest-limitation spirit as `docs/model_cards/hybrid_search_v1.md`'s
BM25/vector findings.

## Known limitations

- **Not evaluated quantitatively** — no relevance judgments exist for visual similarity, unlike
  every other retrieval path in this project. A future extension of the rubric to cover this
  would need genuine (not fabricated) similarity judgments.
- **Colour/background-dominated for flat garment photography** (see finding above) — usable as
  "shoppers who liked this style" rather than "strictly the same kind of item."
- **CLIP ViT-B/32 is general-purpose, not fashion-domain-tuned** — same caveat as
  `BAAI/bge-small-en-v1.5`'s use for text (`docs/model_cards/hybrid_search_v1.md`).
- **Full-catalogue index build takes real time** — measured ~45ms/image single-threaded batch
  rate in isolation (~34 min projected for 44,441 images), though the actual full run took
  longer under concurrent load on this development machine; budget accordingly if rebuilding
  after a catalogue change.
- **Never evaluated for demographic/category skew** in what gets surfaced as "similar" — same
  open item as `docs/ethics/README.md`'s catalogue-representation gap.

## Licence

`Qdrant/clip-ViT-B-32-vision` — MIT (per its Hugging Face repository), consistent with every
other model/data licence in this project (`docs/data_sheets/catalogue_data_sheet.md`).
