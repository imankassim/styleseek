# Risk Register

Source: `STYLESEE1.docx` §16. Reviewed at each stage decision gate (architecture §17).

| Risk / assumption | Impact | Mitigation or evidence | Status |
|---|---|---|---|
| Too little genuine interaction data | Personalised and two-tower models may appear convincing without being valid. | Use human judgments and session features first; label synthetic behaviour; retain advanced models as experiments. | Open |
| Poor catalogue metadata | Semantic and lexical retrieval both degrade. | Quality gates, controlled vocabulary, provenance and error analysis. | Open |
| Popularity bias | Already popular products receive more exposure and clicks. | Separate relevance from popularity, cap soft boosts, monitor catalogue exposure. | Open |
| Position-biased clicks | Top-ranked products receive more clicks regardless of inherent relevance. | Do not equate raw clicks with relevance; use judgments and analyse exposure. | Open |
| Over-personalisation | History overrides the current query. | Apply constraints first and bound personalisation influence. | Open |
| Vector-only overreach | Exact brands, SKUs and hard terms may be missed. | Retain lexical retrieval and validate hybrid fusion. | Open |
| LLM parser unpredictability | Invalid filters or fabricated attributes. | Strict schema, allowed values, deterministic fallback and isolated evaluation. | Open |
| Index staleness | Outdated stock or deleted products remain searchable. | Synchronisation tests, freshness metric and source-of-truth checks. | Open |
| Latency growth | Each added model increases response time. | Retrieve in parallel where appropriate, precompute product embeddings, report p95, simplify if needed. | Open |
| Unlicensed content | Legal and ethical exposure. | Use permitted, owned or clearly synthetic data and media. | Open — see [`docs/data_sheets/catalogue_data_sheet.md`](data_sheets/catalogue_data_sheet.md) |
| Scope expansion | Website features obscure the search research. | Exclude payments and non-essential commerce workflows. | Open |
| Complex local setup | OpenSearch and containers may exceed local constraints. | Begin with simple local alternatives and move heavier services to an approved managed environment only when needed. | Open |

## Project-specific risks (added during delivery)

| Risk / assumption | Impact | Mitigation or evidence | Status |
|---|---|---|---|
| Kaggle dataset is too large for a manual browser download | Stage 4 (catalogue) blocked until dataset is available locally. | Used `kagglehub.dataset_download(...)` with a one-off Kaggle API token auth (`~/.kaggle/access_token`). | Resolved |
| This machine's C: drive had ~0 bytes free, then only ~12.4GB after cleanup — not enough for the full 23.1GB dataset (and risky even at 25GB given archive+extraction can transiently need ~2x) | Stage 4 blocked / risked a long failed download | Switched to `paramaggarwal/fashion-product-images-small` (~572MB, same 44,446-row catalogue/metadata, lower-res images only) — see `docs/data_sheets/catalogue_data_sheet.md`. | Resolved |
| No PostgreSQL or Docker installed locally | Stage 4 blocked — nowhere to run the source-of-truth database | Used a managed free-tier Postgres (Neon) instead of local install, per the deployment architecture's "managed relational database" cloud-oriented role (§10) — connection string kept in git-ignored `database/.env`. | Resolved |
| Naive per-row inserts over a remote (Neon) connection were far too slow for 44k+ rows (~0.35s/row, projected ~4+ hours) | Ingestion impractical at full scale | Switched to psycopg3 pipeline mode (`conn.pipeline()`), which batches statement dispatch instead of round-tripping per statement — full ingest (44,446 products + 216,108 variants) completed in ~69s. | Resolved |
| Kaggle API token was pasted in plaintext in chat rather than saved to a file out-of-band | Token exposed beyond the intended local-file-only handling | Stored only in the git-ignored `~/.kaggle/access_token` file, not persisted anywhere else (not in memory, not in repo); user was advised they can revoke/regenerate it from Kaggle settings if they want to be extra cautious. | Accepted (no further action planned) |
| uvicorn forces `WindowsProactorEventLoopPolicy` on Windows at `.run()` regardless of any asyncio policy set beforehand, which is incompatible with psycopg's async connection mode (needs a selector-based loop) | Backend couldn't connect to the database at all on this machine (local Windows dev) | Switched `backend/app/db.py` from an async to a sync `psycopg_pool.ConnectionPool`; FastAPI runs sync (`def`) route handlers in a thread pool automatically, so this doesn't block the event loop. Revisit if/when Stage 15 moves serving to Linux containers, where this wouldn't have been an issue. | Resolved |
| No Docker/local install for OpenSearch (Stage 8, BM25) | Stage 8 blocked | Used a managed free-tier OpenSearch (Bonsai) instead of local install, same pattern as Neon for Postgres — connection string kept in git-ignored `database/.env`. | Resolved |
| Small, hand-picked relevance judgment set caused genuinely good but ungraded results to score as irrelevant by default ("pooling bias") — hit 3 times during Stage 8 (EXP10, EXP13, EXP14), each time making a real experiment look worse than it was | Early experiment comparisons (e.g. "EXP14 synonyms are worse than EXP12") were backwards | Pooled candidates from multiple experiments' actual top results before trusting any comparison — judgment set grew from 18 to 230 graded products across two pooling passes. See `evaluation/relevance_rubric.md` rule 5. | Resolved |
| Two same-named local Python modules (`mapping.py` in both `search/` and `experiments/EXP14_synonym_expansion/`) collided via Python's by-name module cache, regardless of `sys.path` order — `search/index.py`'s own internal import won, so EXP14 silently rebuilt the *production* OpenSearch index with the wrong (non-synonym) settings on its first run | A full experiment run produced misleadingly plausible results from the wrong index; briefly left the production index rebuilt with correct data but no synonym support | Renamed the colliding module to `synonym_mapping.py`; verified via `client.cat.indices()` that only the intended index existed and was rebuilt correctly afterward. No data was lost. | Resolved |
