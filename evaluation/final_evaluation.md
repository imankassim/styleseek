# Final held-out evaluation

Architecture G11 ("Are the claims supported? Held-out outputs, limitations and negative results
are published.") and §20 Stage 16 ("held-out evaluation"). Configuration frozen per
[`docs/decisions/3-freeze-serving-configuration.md`](../docs/decisions/3-freeze-serving-configuration.md)
before this evaluation was run.

## Method

Every prior comparison in this project (EXP10 through EXP44) evaluated against `train`+`val`
only — verified by grepping every experiment's `run.py` for its `evaluate(..., splits=[...])`
call. `test` (3 queries — rj15 "red dress under £50" / constraint, rj16 "grren shrt" / typo, rj18
"purple waterproof tuxedo" / no_result) was never touched by any tuning decision. This run calls
the live, currently-served `/search` endpoint (via FastAPI's `TestClient`, no mocking) against
exactly that split — the real system a shopper would hit, not a hand-reconstructed
approximation of it.

Reproduce with:

```python
from fastapi.testclient import TestClient
from app.main import app
from metrics import evaluate, print_report

with TestClient(app) as client:
    def search_fn(query):
        return [r["product_id"] for r in client.get("/search", params={"q": query}).json()["results"]]
    rows, summary = evaluate(search_fn, splits=["test"])
    print_report("final held-out evaluation", rows, summary)
```

## Result (2026-09-08)

| Query | Type | ndcg@10 | recall@50 |
|---|---|---|---|
| rj15 "red dress under £50" | constraint | 0.98 | 1.00 |
| rj16 "grren shrt" | typo | 0.00 | 0.00 |
| rj18 "purple waterproof tuxedo" | no_result | 1.00 | 1.00 |

**Overall: ndcg@10 = 0.660, recall@50 = 0.667 (n=3).**

## Reading this honestly

- **n=3 is small.** This is a deliberate consequence of the grouped-split design (architecture
  §3.3's guard against query leakage between splits), not an oversight — but it means this number
  is indicative, not a tight estimate. A single query's score moves the overall mean by roughly
  0.33. Do not read "0.660" as more precise than "somewhere in the 0.4-0.9 range depending on
  which unseen queries you'd ask next."
- **The typo failure is expected, not new.** EXP13 (Stage 8) measured fuzzy matching and found it
  regressed every other query type more than it fixed typos; the deterministic decision was to
  not handle typos at all. rj16 scoring 0 here is that same, already-documented limitation
  showing up in the held-out set — not a surprise this evaluation exists to reveal.
- **Compare against the larger, but not fully held-out, historical numbers with that caveat in
  mind.** The headline numbers quoted throughout
  `experiments/experiment_register.md` (EXP14 BM25 ndcg@10 0.755; EXP34 hybrid fusion ndcg@10
  0.765, recall@50 0.721) were measured on `train`+`val` (n=15), which is what was actually used
  to *choose* between configurations — appropriate for that purpose, but every one of those
  configurations had a chance to fit that data, so they're not directly comparable to this
  n=3 held-out number as if it were the same kind of measurement.
- **The claim this evaluation actually supports**: the frozen configuration continues to behave
  sensibly on queries it has never been tuned against, at the level of detail 3 queries can show
  (a constraint query and a no-result query both scored well; the known typo gap reproduced
  exactly as documented, rather than surfacing some new failure mode). It does **not** support a
  precise quantitative claim at this sample size, and this document says so rather than
  presenting 0.660 as a settled number.

## Negative results carried into this conclusion

Per architecture's negative-result policy (§14), rejected experiments are not omitted from the
final account:

| Experiment | Rejected because |
|---|---|
| EXP13 (BM25 fuzziness) | Fixed the one typo query but regressed every other type net (Stage 8) |
| EXP21 (description-only embeddings) | Catalogue has no description field at all |
| EXP32 (RRF hybrid fusion) | Recall improved but ndcg@10 regressed 27% relative vs BM25 alone |
| EXP40/41/43 (learned ranking: pointwise, tree, LightGBM LambdaRank) | All three families scored well below the hybrid fusion baseline on 178 training rows — G8: learned ranking does not yet beat simpler ranking, consistently across model choice |
| EXP44 (behavioural-feature ranker) | Rejected before running — only synthetic click data existed |
| Category/occasion hard filters (Stage 9) | Looked safe, measurably regressed ndcg@10 0.766→0.660 |
| ThreadPoolExecutor parallel retrieval (Stage 11) | Measured slower (~1050ms) than sequential (~650ms) on this platform |

Full detail for each: `experiments/experiment_register.md` and the individual experiment/
`discarded/` READMEs.
