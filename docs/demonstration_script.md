# Demonstration script

Architecture §18 minimum artefact set: "final held-out evaluation and demonstration script" —
this is the second half, a scripted stakeholder walkthrough. Written 2026-09-08 (brief-fulfilment
audit) alongside `evaluation/final_evaluation.md` (the first half). Every command below is real
and was run against the live system while writing this — not illustrative pseudocode.

**Setup**: `python backend/run.py` (port 8000) and `npm run dev` in `frontend/` (port 3000), both
needing `database/.env`/`backend/.env` with `DATABASE_URL`/`OPENSEARCH_URL` — see the
[README](../README.md#quick-start). The commands below hit the backend directly (`curl`); the
same queries work in the browser at `http://localhost:3000`.

## 1. The target journeys (architecture §2.3), honestly — wins and known gaps together

**Exact search** — brand/product terms preserved:

```
curl -s "http://localhost:8000/search?q=black+nike+shoes" | python -m json.tool
```

Look at `model_version: "hybrid_weighted_fusion_v1"` and the top results — genuine Nike shoes,
boosted brand/title matching (Stage 8, EXP14).

**Attribute search** — colour extracted and hard-filtered:

```
curl -s "http://localhost:8000/search?q=red+dress" | python -m json.tool
```

`interpretation.colour: "Red"` and every result is actually red (Stage 9's hard filter, not a
soft preference) — see `tests/search_regression/test_search_regression.py`'s
`test_attribute_query_respects_colour_and_category`.

**Occasion search** — semantic meaning, not just keyword match:

```
curl -s "http://localhost:8000/search?q=smart+casual+blazer" | python -m json.tool
```

Occasion is surfaced in `interpretation` but deliberately **not** a hard filter — Stage 9 found
filtering on it regressed relevance (real blazers are tagged Formal/Casual in this catalogue,
never "Smart Casual"). Point this out as an evidence-led decision, not an oversight.

**Constraint search** — hard price/colour eligibility:

```
curl -s "http://localhost:8000/search?q=red+dress+under+%C2%A350" | python -m json.tool
```

`interpretation.max_price: 50.0`, every result `price <= 50.0` — this is the query used for
`evaluation/final_evaluation.md`'s held-out set (rj15).

**Typo recovery — known gap, show it honestly:**

```
curl -s "http://localhost:8000/search?q=grren+shrt" | python -m json.tool
```

Results are largely unrelated to "green shirt." This is a deliberate, evidence-based trade-off
(EXP13, Stage 8): fuzzy matching fixed this one query type but regressed every other type more
than it helped. Worth saying out loud in a demo rather than only showing the wins.

**No-result recovery — known gap, show it honestly:**

```
curl -s "http://localhost:8000/search?q=purple+waterproof+tuxedo" | python -m json.tool
```

Returns 24 confident-looking results (purple items — colour filter matched) with **no** signal
that "waterproof tuxedo" wasn't actually found. Architecture §2.3 asks for "controlled
alternatives and relaxed constraints shown transparently"; this doesn't do that yet — vector kNN
has no concept of "no match." See `docs/progress.md`'s brief-fulfilment audit section.

## 2. Session personalisation (Stage 14) — bounded, never overriding intent

```
# fresh session -- COOKIE_JAR can be any writable path
COOKIE_JAR=demo_cookies.txt
curl -s -c $COOKIE_JAR -b $COOKIE_JAR "http://localhost:8000/search?q=dress" | python -m json.tool
# note the top results' colours, then click a Black one twice (its product_id from above, and
# its search_request_id from the response):
curl -s -c $COOKIE_JAR -b $COOKIE_JAR -X POST "http://localhost:8000/events" \
  -H "Content-Type: application/json" \
  -d '{"events":[{"event_type":"click","product_id":"<id>"},{"event_type":"click","product_id":"<id>"}]}'
# same session, same broad query again -- Black items should now lead:
curl -s -c $COOKIE_JAR -b $COOKIE_JAR "http://localhost:8000/search?q=dress" | python -m json.tool
# but an EXPLICIT colour query in the same session is completely unaffected:
curl -s -c $COOKIE_JAR -b $COOKIE_JAR "http://localhost:8000/search?q=blue+dress" | python -m json.tool
```

This is the exact sequence `tests/integration/test_api_contract.py`'s
`test_search_personalisation_boosts_session_preferred_colour` and
`test_search_explicit_colour_ignores_session_click_history` verify automatically.

## 3. Visual similarity (optional extension, built after Stage 16)

Open any product page in the browser, e.g. `http://localhost:3000/products/10035` (a shoe) — the
"Similar styles" section shows other visually similar products. Or directly:

```
curl -s "http://localhost:8000/products/10035/similar?limit=5" | python -m json.tool
```

Worth showing both a shoe/watch (stays reliably within-category) and a flat-photographed
garment (colour/background-dominated instead) — see `docs/model_cards/visual_similarity_v1.md`
for why they behave differently.

## 4. Auditability — every response says what actually served it

Any `/search` response's `model_version` and `fallback_used` fields are not decorative — they
reflect exactly which retrieval path served that specific response (architecture §11
auditability). Trigger the fallback path directly by checking
`tests/integration/test_api_contract.py`'s `test_search_falls_back_to_postgres_when_opensearch_unavailable`
and `test_search_falls_back_to_bm25_only_when_vector_search_unavailable` — both simulate a real
outage and confirm the response says so honestly rather than silently degrading.

## 5. The evidence trail

- `evaluation/final_evaluation.md` — the genuinely held-out result (ndcg@10=0.660,
  recall@50=0.667, n=3) with its honest small-n caveat, plus every rejected experiment and why.
- `experiments/experiment_register.md` — all 23+ experiments, accepted and rejected, with
  numbers.
- `evaluation/results/` — raw ranked result lists for the live system and two comparison
  baselines, saved as inspectable files rather than only summarised metrics.
- `monitoring/report.py` — real p50/p95/p99 latency, fallback rate, zero-result rate from actual
  traffic (`python monitoring/report.py`).
- `docs/progress.md`'s "Brief-fulfilment audit" section — the honest gap list this script's
  sections 1's two "known gap" demos come from.
