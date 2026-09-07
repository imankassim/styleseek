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
| Kaggle dataset requires manual/local download (no Kaggle API credentials configured for this build) | Stage 4 (catalogue) blocked until dataset is available locally. | User downloads dataset manually; ingestion script reads from a local path rather than calling the Kaggle API. | Open |
