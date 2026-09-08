# Ethics, privacy and limitations assessment

Architecture §11 (security, privacy and governance), §2.2 (explicit non-goals), §16 (risks) and
Stage 16's "conclude" requirement to publish this alongside the final evaluation.

## Scope and purpose

StyleSeek is a research/learning prototype demonstrating an evidence-led hybrid search
methodology (architecture §2.1) — not a real storefront. It is not deployed to production, does
not process payments, and (per §2.2) deliberately excludes "a copy of ASOS branding, product
imagery, descriptions or proprietary code" and "a production-scale customer identity platform."
Everything below should be read with that scope in mind: several risks below are "low, because
this never carries real traffic" rather than "solved for a real deployment."

## Data provenance and licensing

- Catalogue: `paramaggarwal/fashion-product-images-small` (Kaggle), confirmed **MIT**-licensed
  (`docs/data_sheets/catalogue_data_sheet.md`) — permits use, modification and redistribution.
- Price, stock quantity, and size run are **synthetic**, deterministically seeded from
  `product_id` and clearly flagged in the schema (`is_synthetic_price`, `is_synthetic_variant`)
  rather than presented as real. Title, category, colour, brand and occasion are the dataset's
  real values.
- No scraped or proprietary third-party content beyond the licensed Kaggle dataset and the
  MIT-licensed `BAAI/bge-small-en-v1.5` embedding model (`docs/model_cards/hybrid_search_v1.md`).

## Privacy

- Sessions are anonymous random tokens (`backend/app/session.py`) — no account system, no email,
  no name, no real identity ever collected (architecture §11 "prefer anonymous sessions").
- Only two event types are recorded: `impression` and `click`, tied to a session token and a
  `search_request_id` (`database/migrations/3_search_requests_and_events.sql`). No free-text
  fields, no IP address, no device fingerprinting.
- **Retention**: not formally defined — there is no scheduled deletion job for `search_request`/
  `event` rows. Acceptable for a research prototype with no real users generating this data
  (every row so far is from development/testing traffic, per `monitoring/report.py`'s own
  output), but this would need an explicit retention policy before carrying any real usage.
  Documented here as an honest gap, not silently left unmentioned.
- Personalisation (Stage 14) reads only the current session's own recent clicks, never persists
  a cross-session profile, and is bounded (top-10 window, needs 2+ same-colour clicks,
  never overrides an explicit query constraint) — see `backend/app/personalization.py`'s
  module docstring for the full reasoning.

## Bias and fairness

- **No protected-characteristic targeting or inference.** The system has no concept of a
  shopper's demographics beyond what they type — `gender` in the catalogue is a garment
  attribute (e.g. "Men"/"Women" sizing categories inherited from the source dataset), used only
  as a hard filter when a query names it, never inferred or used to profile a session.
- **Popularity/exposure bias is a known, unaddressed risk.** Architecture §16 flags "already
  popular products receive more exposure and clicks" as an open risk — this project's own click
  data comes entirely from development/testing, not genuine independent shoppers, so no
  popularity signal is used in ranking at all (no click-through-rate feature exists anywhere in
  the live path). This sidesteps rather than solves the risk: a real deployment with genuine
  traffic would need the mitigation architecture describes (separate relevance from popularity,
  cap soft boosts) before using behavioural data more broadly.
- **Catalogue representation was not audited** for skew across categories, genders, or price
  bands beyond the data-quality gates already in place (schema validity, controlled vocabulary
  coverage). Whatever imbalance exists in the source Kaggle dataset (e.g. category or gender
  distribution) passes through unexamined.
- **No real user testing.** Every relevance judgment (`evaluation/relevance_judgments.json`) was
  hand-labelled by the project author against a written rubric (`evaluation/relevance_rubric.md`)
  — a reasonable substitute for real shopper feedback in a solo research prototype, but not a
  replacement for it. The architecture's own testing matrix names "user evaluation: blind
  comparison of result lists where appropriately approved" as a distinct, unmet test level here.

## Explainability

- Every `/search` response reports `model_version` and `fallback_used` honestly (architecture
  §11's auditability principle) — a shopper-facing or developer-facing consumer can always tell
  which retrieval path actually served a given response, not just which was attempted.
- `interpretation` in the response surfaces exactly what the deterministic query parser extracted
  (colour, category, occasion, price, size) — no hidden inference the shopper can't see.
- No LLM is used anywhere in the live serving path (architecture §2.2 "unrestricted LLM control
  of filters or ranking" was explicitly out of scope; the optional LLM parser experiment, EXP20,
  was never started).

## Negative results as an ethical/governance practice, not just a scientific one

Every rejected approach in this project (EXP13 fuzziness, EXP21 description embeddings, EXP32
RRF, EXP40/41/43 learned rankers, EXP44 behavioural features, the category/occasion hard filters)
is documented with its measured reason for rejection, not deleted or omitted — see
`evaluation/final_evaluation.md`'s "Negative results" table and `experiments/experiment_register.md`.
This matters ethically as well as scientifically: a system that only ever reports its wins would
misrepresent what was actually learned, including the honest limitation that learned ranking and
real personalisation both remain blocked on insufficient genuine interaction data — the single
risk architecture's own risk register flags most prominently (`docs/risk_register.md`, "Too
little genuine interaction data").

## Summary of open items

- No data retention policy for `search_request`/`event` (acceptable at current scope; would need
  addressing before any real traffic).
- Popularity/exposure bias mitigation not built (currently moot — no real click data exists).
- Catalogue representation not audited for demographic/category skew.
- No real (non-synthetic-session) user evaluation has been conducted.
