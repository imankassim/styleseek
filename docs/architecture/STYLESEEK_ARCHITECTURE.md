# StyleSeek — Project Journey, Task Definition and Technical Architecture

> Markdown companion to `STYLESEE1.docx`, the canonical source document. If this file and the
> `.docx` ever disagree, the `.docx` wins — update this file to match.
>
> A complete companion document defining what will be built, why it exists, how the parts
> connect, and how the solution progresses from a static page to an evaluated ML search service.

## Document purpose

| Document | Description |
|---|---|
| Project brief | Defines the problem, users, scope, research question and intended outcomes. |
| Journey map | Shows the evidence-led sequence from discovery through evaluation and productionisation. |
| Architecture | Explains the page, API, data, retrieval, ranking, events, training and operational layers. |
| Delivery guide | Lists work packages, outputs, dependencies, tests, risks and decision gates. |

**Relationship to the beginner handbook.** This document is the architectural and
project-management companion to `StyleSeek_Beginner_Friendly_Build_Journey.docx`. The handbook
teaches the steps and code; this document explains the complete task and the target system design.

## 1. Executive summary

StyleSeek is an original fashion e-commerce prototype inspired by the type of shopping journey
used by large online retailers. Its purpose is not to copy a real retailer. Its purpose is to
investigate whether a staged hybrid search system can improve product discovery over a credible
keyword baseline.

The project begins with a working but deliberately simple website. It then establishes a
searchable product catalogue, an API, event instrumentation and a labelled relevance set. Only
after those foundations exist does the project introduce BM25 lexical retrieval, semantic vector
retrieval, rank fusion, business constraints, learning-to-rank and bounded session
personalisation.

**Primary research question.** To what extent does hybrid lexical and semantic retrieval,
followed by learning-to-rank, improve fashion-product search relevance compared with a tuned
BM25 baseline?

| Dimension | Definition |
|---|---|
| User problem | Shoppers use exact product terms, attributes, occasion language, style language, spelling variants and hard constraints. One search method may not handle all of them well. |
| Technical problem | Retrieve a broad but relevant candidate set quickly, then order it using richer signals without violating price, category, size or stock requirements. |
| ML problem | Learn how to combine lexical, semantic, product and session signals while avoiding leakage, sparse-data overclaiming and popularity feedback loops. |
| Operational problem | Serve results reliably, record model versions, monitor quality and latency, and fall back to simpler search when advanced components fail. |
| Evidence problem | Demonstrate improvement using labelled queries, repeatable experiments, error analysis and a held-out test set. |

## 2. Task definition

### 2.1 What will be built

- An original responsive fashion storefront called StyleSeek.
- A product catalogue containing products, variants, colours, sizes, prices, stock and permitted images.
- A Next.js front end for search, category browsing, product pages, filters and basket simulation.
- A Python FastAPI back end that exposes product, search and event endpoints.
- A PostgreSQL transactional source of truth.
- An OpenSearch index supporting lexical and vector retrieval.
- A query-understanding module for explicit attributes and price constraints.
- An RRF or validated alternative fusion layer.
- A LightGBM learning-to-rank experiment and guarded serving path.
- Anonymous session features for bounded personalisation.
- An evaluation and monitoring layer for relevance, reliability, latency and fallback behaviour.

### 2.2 What will not be built initially

- Real card payments or order fulfilment.
- A copy of ASOS branding, product imagery, descriptions or proprietary code.
- A production-scale customer identity platform.
- Unrestricted LLM control of filters or ranking.
- A transformer or two-tower model promoted without sufficient genuine interaction data.
- Automatic retraining without review and governance.

### 2.3 Target user journeys

| Journey | Example | System responsibility |
|---|---|---|
| Exact search | black Adidas trainers | Preserve exact brand and product terms. |
| Attribute search | green satin midi dress size 12 | Extract and honour structured attributes. |
| Occasion search | smart casual outfit for a summer wedding | Use semantic meaning and fashion metadata. |
| Constraint search | petite black work trousers under £40 | Apply hard eligibility rules. |
| Typo recovery | grren satn midi drss | Use fuzziness, synonyms or correction safely. |
| Session adaptation | broad dress search after viewing neutral midi dresses | Apply a small transparent preference boost without overriding the query. |
| No-result recovery | purple waterproof tuxedo | Avoid random products; show controlled alternatives and relaxed constraints. |

## 3. Requirements and success measures

### 3.1 Functional requirements

| ID | Requirement | Evidence |
|---|---|---|
| FR-01 | A shopper can enter a query and receive ranked products. | End-to-end test and screen recording. |
| FR-02 | A shopper can filter by product attributes and availability. | Filter regression tests. |
| FR-03 | The system can run lexical, vector and hybrid retrieval experiments. | Saved configurations and outputs. |
| FR-04 | Every result response includes a search request ID and model/configuration version. | API contract test. |
| FR-05 | Relevant events can be recorded without unnecessary personal data. | Event schema and privacy review. |
| FR-06 | The ranker can fall back to fusion, and semantic retrieval can fall back to lexical search. | Failure-injection tests. |
| FR-07 | Metrics can be calculated from saved judgments and result lists. | Repeatable evaluation harness. |

### 3.2 Non-functional requirements

| Area | Requirement |
|---|---|
| Relevance | Performance is reported using labelled queries and query-type breakdowns, not attractive examples alone. |
| Reliability | Advanced ML failure must not prevent basic lexical search where the lexical service remains available. |
| Latency | Median and p95 response times are measured and reported. Final thresholds are set from prototype evidence rather than invented in advance. |
| Security | Secrets remain outside source code; interfaces validate inputs; deployed environments follow applicable approval requirements. |
| Privacy | Use anonymous sessions and data minimisation. Real participant data requires an appropriate lawful and approved process. |
| Accessibility | Keyboard navigation, labels, focus states, alt text and colour contrast are included. |
| Maintainability | Components are modular, versioned and covered by unit, integration and regression tests. |
| Auditability | Queries, outputs, configurations and model versions can be traced without logging unnecessary sensitive content. |
| Cost | Search, model and infrastructure costs are measured where available and discussed alongside quality. |

### 3.3 Evaluation measures

- NDCG@10 for ordering quality.
- Recall@50 for candidate retrieval coverage.
- No-result rate and explicit-constraint violation rate.
- Catalogue coverage and diversity for broad queries.
- Median and p95 API latency.
- Error, fallback and index-freshness measures.
- Query-level wins and regressions rather than average-only reporting.

**Evidence rule.** No experiment is promoted because it looks more advanced. It remains only if
it solves a named problem, is reproducible, and improves the agreed evidence without creating
unacceptable risks.

## 4. Architecture principles

| Principle | How StyleSeek applies it |
|---|---|
| Baseline first | Begin with static filtering, PostgreSQL search and BM25 before adding semantic or learned ranking. |
| Separation of concerns | The page, API, source database, search index, model code and analytics are separate modules. |
| Source of truth | PostgreSQL owns current product and variant records; the search index is a rebuildable serving copy. |
| Offline and online separation | Embedding generation and model training run outside the live request; serving uses versioned artefacts. |
| Hard constraints before soft preference | Stock, selected size, category and price eligibility cannot be overridden by personalisation. |
| Graceful degradation | Embedding or ranker failure leads to a simpler honest method rather than a broken or invented result. |
| Observability by design | Search request ID, configuration/model version, latency and fallback status are captured from early versions. |
| Governance throughout | Data provenance, licensing, privacy, security and decision records accompany the build. |
| Evidence-led evolution | Each stage is compared with earlier stages on a fixed validation framework. |

Relevant internal guidance describes an operational ML lifecycle spanning requirements, data
ingestion and preparation, model development and testing, deployment, and monitoring and
assurance. The StyleSeek architecture mirrors those concerns at prototype scale. The internal
governance playbook also describes discovery, scoping, delivery, deployment, success metrics,
data quality, integration, monitoring and handover as lifecycle concerns.

## 5. System context architecture

```
SHOPPER
  Searches, filters, views products, selects variants and uses a simulated basket
      │
      ▼
STYLESEEK SYSTEM
  Front end + API + catalogue + search + ranking + event instrumentation
      │
      ├──▶ CATALOGUE SOURCE — Licensed, owned or clearly synthetic product records
      ├──▶ EXPERIMENT & EVALUATION — Judgments, metrics and reports
      └──▶ DEVELOPER / REVIEWER — Builds, tests, deploys and inspects evidence
```

**Context boundaries**

- StyleSeek does not own real payment processing.
- Catalogue inputs must have recorded provenance and usage rights.
- Anonymous behavioural events are part of the prototype only when they have a defined purpose.
- The ML system recommends result order; explicit page sorting and hard filters remain
  user-controlled.

## 6. Logical solution architecture

The logical view shows the main components and the direction of data flow. It is
technology-specific enough to guide implementation but remains independent of a particular cloud
deployment.

```
1. NEXT.JS FRONT END
   Search input • suggestions • filters • result grid • product detail • basket simulation
      │
      ▼
2. FASTAPI APPLICATION LAYER
   /search • /products • /events • validation • orchestration • response contract
      │
      ├──▶ QUERY UNDERSTANDING   — Normalise text, extract attributes, build safe filters
      ├──▶ CUSTOMER CONTEXT      — Anonymous session, recent interactions, selected size
      └──▶ CATALOGUE SERVICE     — Products, variants, price and stock
      │
      ▼
3. CANDIDATE RETRIEVAL
   BM25 lexical retrieval + semantic vector retrieval + optional safe fallback pool
      │
      ▼
4. FUSION
   RRF baseline or another validated score/rank combination
      │
      ▼
5. RE-RANKING
   Transparent rules first • LightGBM learning-to-rank later
      │
      ▼
6. ELIGIBILITY AND DIVERSITY
   Stock • size • category • price • duplicate control • bounded personalisation
      │
      ▼
7. API RESPONSE
   Search request ID • query interpretation • model version • ranked product results
```

**Ordering note.** During implementation, hard filters should be applied as early as supported
and validated again before the result is returned. The diagram groups eligibility near final
ranking to make the policy visible, not to prescribe an inefficient double retrieval.

## 7. Online search request sequence

| Step | Request behaviour |
|---|---|
| 1 | The shopper submits "petite green wedding guest dress under £60". |
| 2 | Next.js sends the query and visible filter selections to `GET /search`. |
| 3 | FastAPI validates the request and creates a search request ID. |
| 4 | The parser extracts `category=dress`, `range=petite`, `colour=green`, `occasion=wedding guest` and `max_price=60` where those values are supported by the catalogue schema. |
| 5 | The lexical retriever searches exact and fuzzy terms across boosted fields. |
| 6 | The semantic service embeds the remaining meaning-focused text and retrieves nearby product vectors. |
| 7 | Fusion combines the independently ordered candidate lists. |
| 8 | Eligibility removes products that violate explicit constraints. |
| 9 | The rule or learned ranker scores the candidates using versioned features. |
| 10 | A bounded session signal and diversity policy may make small final changes. |
| 11 | The API returns ranked products plus interpretation and version data. |
| 12 | The page renders results and records genuine impressions and later clicks. |

**Example response contract**

```json
{
  "search_request_id": "srch_90e1",
  "query": "petite green wedding guest dress under £60",
  "interpretation": {
    "category": "dress",
    "range": "petite",
    "colour": "green",
    "occasion": "wedding guest",
    "max_price": 60
  },
  "model_version": "ltr_v1",
  "fallback_used": false,
  "results": [ ... ]
}
```

## 8. Data architecture

### 8.1 Operational entities

| Entity | Purpose | Key fields |
|---|---|---|
| Product | Shared commercial and descriptive information. | `product_id, title, brand, category, material, fit, occasion, description, price` |
| Product variant | Purchasable colour and size combination. | `variant_id, product_id, colour, size, SKU, stock_quantity` |
| Search document | Denormalised product record used by OpenSearch. | Searchable text, filters, available sizes/colours, stock flag, product vector |
| Search request | One returned result list. | `search_request_id, session_id, query, interpretation, version, latency, fallback` |
| Event | A meaningful action associated with a session or request. | `event_id, type, product_id, position, timestamp` |
| Relevance judgment | Human assessment for offline evaluation. | `query_id, query, product_id, grade` |
| Experiment | Reproducible comparison of one configuration. | `experiment_id, hypothesis, configuration, metrics, decision` |
| Model record | Metadata for a trained and deployed artefact. | `model_version, features, training split, metrics, file checksum, status` |

### 8.2 Storage responsibilities

| Store | Responsibility | Not responsible for |
|---|---|---|
| PostgreSQL | Current products, variants, stock and transactional prototype records. | High-speed vector nearest-neighbour retrieval. |
| OpenSearch | Searchable documents, lexical index, vector fields and retrieval pipelines. | Being the sole authoritative product record. |
| Analytical store or files | Events, experiment outputs, feature datasets and evaluation results. | Serving current stock directly to shoppers without validation. |
| Model registry / versioned artefacts | Embedding and ranking model versions, metadata and deployment status. | Replacing source-code version control. |
| Repository | Code, tests, schemas, configuration templates, ADRs and documentation. | Secrets, raw personal data or unlicensed assets. |

### 8.3 Data quality gates

- Unique and non-null product identifiers.
- Non-negative price and stock values.
- Valid product-to-variant references.
- At least one permitted image where the UI requires it.
- Allowed categories, colours, sizes and other controlled values.
- Exactly one expected vector dimension per embedded product.
- Search document version tied to its source product version.
- Failure prevents or quarantines an invalid downstream update.

## 9. Offline training and evaluation architecture

```
SOURCE DATA
  Catalogue snapshots • permitted events • human relevance judgments
      │
      ▼
QUALITY & PREPARATION
  Schema checks • provenance • query grouping • train/validation/test split
      │
      ├──▶ EMBEDDING EXPERIMENTS  — Product text variants, model selection, vector generation
      └──▶ RETRIEVAL EXPERIMENTS  — BM25, vector only, hybrid fusion
      │
      ▼
RANKING FEATURES
  Lexical scores • semantic scores • attribute matches • context
      │
      ▼
MODEL TRAINING
  Pointwise baseline • LightGBM LambdaRank • grouped evaluation
      │
      ▼
EVALUATION & ERROR ANALYSIS
  NDCG • Recall • constraint checks • latency • query-type wins and regressions
      │
      ▼
MODEL / CONFIGURATION REGISTRY
  Version • data split • features • metrics • approval status • rollback target
```

**Training controls**

- Split by query rather than random query-product rows.
- Keep the final test queries separate until model selection is complete.
- Version feature generation and use the same logic in training and serving.
- Treat raw clicks as position-biased rather than automatically equal to relevance.
- Clearly label any synthetic behavioural data.
- Retain simpler baselines and negative results.

## 10. Deployment architecture

For a local learning build, services may run through local processes or containers. For a cloud
build, the same logical roles can be deployed using approved managed services. The following
describes roles, not a mandatory vendor-specific configuration.

| Layer | Local / development role | Cloud-oriented role |
|---|---|---|
| Web | Next.js development server. | Static or server-rendered web hosting. |
| API | FastAPI process. | Container or managed application runtime. |
| Operational data | Local PostgreSQL. | Managed relational database. |
| Search | Local or hosted OpenSearch appropriate to the environment. | Managed search and vector service. |
| Events / analytics | PostgreSQL, Parquet or analytical notebook inputs. | Message ingestion plus analytical warehouse or object storage. |
| Training | Local or managed notebook for reproducible experiments. | Managed ML jobs and registry where approved. |
| Secrets | Local environment file excluded from source control. | Managed secret store. |
| Monitoring | Application logs and local metrics. | Central logs, metrics, alerts and dashboards. |

### Availability and fallback paths

| Failure | Expected behaviour |
|---|---|
| Embedding service unavailable | Run lexical retrieval and mark semantic fallback. |
| Vector index unavailable | Run lexical retrieval and omit semantic contribution. |
| Ranker unavailable or invalid | Use RRF or the last approved transparent rule configuration. |
| Session feature service unavailable | Use non-personalised ranking. |
| Event collector unavailable | Do not block search response; record the operational failure where possible. |
| OpenSearch unavailable | Return a controlled service error or an explicitly defined limited fallback. Do not display unrelated products as search results. |
| Catalogue synchronisation failure | Keep the last known serving index, alert, and prevent silent promotion of incomplete data. |

## 11. Security, privacy and governance architecture

| Control area | StyleSeek design response |
|---|---|
| Data provenance | Record source, licence, transformations and whether records are synthetic. |
| Privacy | Prefer anonymous sessions, collect only purposeful events, define retention and avoid protected-characteristic targeting. |
| Input safety | Validate query length, allowed filters, numeric ranges and structured parser outputs. |
| Access | Separate development, deployment and data privileges according to the chosen environment. |
| Secrets | Never commit passwords, tokens or connection strings. |
| Auditability | Version retrieval configuration, parser, embeddings, features, ranker and event schema. |
| Explainability | Expose query interpretation and retain score-feature diagnostics for investigation. |
| Human review | Use review for model promotion, governance decisions and high-impact changes. |
| Responsible ranking | Do not present sponsored ordering as organic relevance; monitor popularity loops and less-represented catalogue ranges. |
| Release approval | Apply the relevant organisational and legal approval processes before any real organisational go-live. |

**Prototype boundary.** This architecture document is a technical learning design. Any
deployment using organisational data, participants or production systems must follow the
applicable internal approval, security, privacy and AI-governance process.

## 12. Complete journey roadmap

The journeys are intentionally ordered so each one creates a working or testable foundation for
the next. Rejected experiments remain documented evidence.

| # | Journey | Primary work | Exit outcome |
|---|---|---|---|
| 1 | Investigation setup | Repository, experiment register, ADRs | A traceable project before implementation. |
| 2 | First visible page | Search input, product card, page states | The UI defines the response contract. |
| 3 | Primitive search | Substring and token search | Weak but measurable baselines. |
| 4 | Catalogue | Products, variants, validation and ingestion | Reliable source data. |
| 5 | API | FastAPI health, products and search | A complete page-to-Python path. |
| 6 | Store behaviour | Product detail, basket, filters, sort | A testable shopping journey. |
| 7 | Instrumentation | Sessions, request IDs, impressions and clicks | Traceable behaviour data. |
| 8 | Evaluation | Judgments, NDCG, Recall, latency | Objective selection criteria. |
| 9 | BM25 | Search documents, boosts, fuzziness and synonyms | Strong lexical baseline. |
| 10 | Query understanding | Price, size, colour, category and occasion parsing | Safe structured constraints. |
| 11 | Semantic retrieval | Embedding representation and vector search | Meaning-based candidate retrieval. |
| 12 | Hybrid fusion | RRF and alternative fusion experiments | Combined lexical and semantic candidates. |
| 13 | Rules and diversity | Eligibility, transparent scoring and duplicate control | Safe final candidate policy. |
| 14 | Learning-to-rank | Features, grouped splits, LightGBM and fallback | Learned ordering. |
| 15 | Personalisation | Bounded session features and cold-start fallback | Small contextual adaptation. |
| 16 | Optional extensions | Visual similarity and conversational discovery | Separate advanced investigations. |
| 17 | Full API | Orchestration and response contract | Integrated search service. |
| 18 | Reliability | Failure injection, sync and drift tests | Known failure behaviour. |
| 19 | Dashboards | Quality, latency, errors and regressions | Observable evidence. |
| 20 | Deployment | Containers, CI, monitoring and rollback | Repeatable release. |
| 21 | Final evaluation | Held-out test, model card, data sheet and ethics | Defensible conclusion. |

## 13. Delivery work packages

| ID | Work package | Main outputs | Depends on |
|---|---|---|---|
| WP1 | Discovery and evidence design | Brief, research question, query taxonomy, metrics, risk register | None |
| WP2 | Front-end shell | Static search page, cards, states, accessibility checks | WP1 |
| WP3 | Catalogue and API | Database schema, ingestion, validation, product/search endpoints | WP1, WP2 |
| WP4 | Store interactions | Product page, variants, basket, browsing, filters and sorting | WP3 |
| WP5 | Instrumentation and judgments | Event schema, IDs, relevance rubric, labelled query set | WP3, WP4 |
| WP6 | Lexical retrieval | PostgreSQL experiment, OpenSearch index, BM25 tuning | WP3, WP5 |
| WP7 | Query understanding | Deterministic parser, hard-filter schema, optional LLM experiment | WP5, WP6 |
| WP8 | Semantic and hybrid retrieval | Embedding tests, vector index, RRF and fusion study | WP5, WP6, WP7 |
| WP9 | Safe ranking | Eligibility, diversity and transparent rule baseline | WP8 |
| WP10 | Learning-to-rank | Feature dataset, grouped splits, models, explanation and fallback | WP5, WP8, WP9 |
| WP11 | Session context | Bounded features, cold start, generic comparison | WP4, WP10 |
| WP12 | Operations | Tests, failures, sync, monitoring, containers and CI | All prior serving work |
| WP13 | Final evidence | Held-out results, architecture, model card, data sheet, ethics and demo | WP12 |

## 14. Planned experiment catalogue

> IDs below are quoted verbatim from `STYLESEE1.docx`. The working repo (experiment folders,
> `experiments/experiment_register.md`) uses a plain unpadded numbering instead — `EXP1` for
> `EXP-001`, `EXP10` for `EXP-010`, and so on, same order.

| Experiment | Possibility considered | Role |
|---|---|---|
| EXP-001 | Whole-query substring search | Primitive baseline |
| EXP-002 | Token intersection search | Primitive baseline |
| EXP-010 | PostgreSQL full-text search | Architecture comparison |
| EXP-011 | BM25 equal field weights | Lexical baseline |
| EXP-012 | BM25 boosted structured fields | Lexical tuning |
| EXP-013 | BM25 fuzziness | Typo experiment |
| EXP-014 | Synonym expansion | Vocabulary experiment |
| EXP-020 | LLM query parser | Optional parser comparison |
| EXP-021 | Description-only embeddings | Representation comparison |
| EXP-022 | Title plus description embeddings | Representation comparison |
| EXP-023 | All metadata embeddings | Representation comparison |
| EXP-024 | Labelled structured embeddings | Representation comparison |
| EXP-030 | Vector-only retrieval | Semantic baseline |
| EXP-031 | BM25-only retrieval | Lexical comparator |
| EXP-032 | RRF hybrid retrieval | Rank-fusion baseline |
| EXP-033 | Normalised score fusion | Fusion alternative |
| EXP-034 | Weighted score fusion | Fusion alternative |
| EXP-040 | Simple pointwise model | Learned baseline |
| EXP-041 | Tree-based pointwise model | Learned baseline |
| EXP-043 | LightGBM LambdaRank | Ranking candidate |
| EXP-044 | Ranker with behavioural features | Context experiment |
| EXP-050 | Collaborative filtering | Optional recommendation experiment |
| EXP-051 | Two-tower model | Optional sparse-data investigation |

**Negative-result policy.** An experiment may be rejected because it lowers relevance, increases
latency, adds operational complexity, relies on weak synthetic behaviour, creates governance
concerns or duplicates a simpler capability. The code and result remain in the evidence trail.

> The live, working copy of this table (with status/decision columns) is maintained in
> [`experiments/experiment_register.md`](../../experiments/experiment_register.md).

## 15. Testing and acceptance matrix

| Test level | Examples | Acceptance intent |
|---|---|---|
| Unit | Price extraction, colour mapping, RRF calculation, feature generation, eligibility rules. | Small functions behave exactly as defined. |
| Data quality | Unique IDs, non-negative price, valid references, vector dimension, allowed values. | Invalid data cannot silently enter serving. |
| API contract | Required response fields, filter validation, errors and model version. | Front end and back end share a stable contract. |
| Integration | Next.js to FastAPI, database read, search retrieval, event write. | Components work together. |
| Search regression | Fixed exact, attribute, occasion, typo and no-result queries. | Known useful behaviour is protected. |
| Offline evaluation | NDCG, Recall, coverage and query-type breakdown. | Configuration choices are evidence-led. |
| Failure injection | Disable embeddings, ranker, events or search components. | Fallback and error behaviour match the runbook. |
| Performance | Median and p95 latency under representative test conditions. | Quality is considered alongside serving behaviour. |
| Accessibility | Keyboard, focus, labels, alt text and contrast. | Primary journeys remain usable. |
| Security/privacy | Input validation, secret scan, log review and data minimisation. | Prototype does not create avoidable risk. |
| User evaluation | Blind comparison of result lists where appropriately approved. | Human usefulness complements offline metrics. |

## 16. Risks, assumptions and mitigations

| Risk / assumption | Impact | Mitigation or evidence |
|---|---|---|
| Too little genuine interaction data | Personalised and two-tower models may appear convincing without being valid. | Use human judgments and session features first; label synthetic behaviour; retain advanced models as experiments. |
| Poor catalogue metadata | Semantic and lexical retrieval both degrade. | Quality gates, controlled vocabulary, provenance and error analysis. |
| Popularity bias | Already popular products receive more exposure and clicks. | Separate relevance from popularity, cap soft boosts, monitor catalogue exposure. |
| Position-biased clicks | Top-ranked products receive more clicks regardless of inherent relevance. | Do not equate raw clicks with relevance; use judgments and analyse exposure. |
| Over-personalisation | History overrides the current query. | Apply constraints first and bound personalisation influence. |
| Vector-only overreach | Exact brands, SKUs and hard terms may be missed. | Retain lexical retrieval and validate hybrid fusion. |
| LLM parser unpredictability | Invalid filters or fabricated attributes. | Strict schema, allowed values, deterministic fallback and isolated evaluation. |
| Index staleness | Outdated stock or deleted products remain searchable. | Synchronisation tests, freshness metric and source-of-truth checks. |
| Latency growth | Each added model increases response time. | Retrieve in parallel where appropriate, precompute product embeddings, report p95, simplify if needed. |
| Unlicensed content | Legal and ethical exposure. | Use permitted, owned or clearly synthetic data and media. |
| Scope expansion | Website features obscure the search research. | Exclude payments and non-essential commerce workflows. |
| Complex local setup | OpenSearch and containers may exceed local constraints. | Begin with simple local alternatives and move heavier services to an approved managed environment only when needed. |

> The live, working copy of this table is maintained in
> [`docs/risk_register.md`](../risk_register.md).

## 17. Stage decision gates

| Gate | Question | Continue when |
|---|---|---|
| G1: Page | Is the search journey understandable without a back end? | Success, empty, loading and error states are usable. |
| G2: Catalogue | Can trusted product and variant data be rebuilt? | Quality checks pass and provenance is recorded. |
| G3: API | Can the page, Python and database exchange validated data? | Contract and integration tests pass. |
| G4: Evaluation | Can search configurations be compared fairly? | Judgments, metric tests and data splits are frozen. |
| G5: Lexical | Is BM25 a credible tuned baseline? | Validation and error-analysis evidence exists. |
| G6: Semantic | Does vector retrieval add useful candidates? | Wins and failures are measured by query type. |
| G7: Hybrid | Does fusion complement lexical retrieval? | It improves agreed evidence without unacceptable latency or regressions. |
| G8: Ranker | Does learned ranking beat simpler ranking? | Grouped validation improves and fallback works. |
| G9: Personalisation | Does context add value without overriding intent? | Generic and cold-start behaviour remain reliable. |
| G10: Release | Can the system be operated and restored? | Tests, monitoring, versioning, rollback and governance evidence are complete. |
| G11: Conclusion | Are the claims supported? | Held-out outputs, limitations and negative results are published. |

## 18. Proposed repository and artefact structure

```
styleseek/
├── frontend/                  # Next.js pages and components
├── backend/                   # FastAPI routes and orchestration
├── database/                  # schemas, migrations and seeds
├── search/                    # indexing, BM25, vectors and fusion
├── ml/
│   ├── embeddings/
│   ├── learning_to_rank/
│   └── personalisation/
├── experiments/                # reproducible investigations
├── discarded/                  # clean rejected approaches + reasons
├── evaluation/                 # judgments, metrics and reports
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── search_regression/
│   └── data_quality/
├── infrastructure/             # containers and deployment config
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── model_cards/
│   ├── data_sheets/
│   └── ethics/
└── README.md
```

**Minimum artefact set**

- Project charter and scope.
- System context, logical, data, offline ML and deployment architectures.
- Experiment register and architecture decision records.
- Catalogue data sheet and provenance register.
- Relevance rubric and labelled query set.
- Evaluation harness and saved result lists.
- Model card and feature schema.
- Testing evidence and failure-injection report.
- Monitoring dashboard and operational runbook.
- Ethics, privacy and limitations assessment.
- Final held-out evaluation and demonstration script.

## 19. Potential Level 7 evidence mapping

The exact apprenticeship mapping should be checked against the current assessment requirements.
The following is a suggested evidence relationship, not an assessment decision.

| Evidence theme | StyleSeek artefacts |
|---|---|
| AI and ML methods | Lexical baseline, semantic embeddings, hybrid retrieval, learning-to-rank and optional recommendation experiments. |
| Statistics and evaluation | Judgment design, NDCG, Recall, grouped splits, uncertainty and error analysis. |
| Data engineering | Catalogue ingestion, product/variant schema, denormalised index, event pipeline and data-quality gates. |
| Software engineering | Next.js components, FastAPI contract, tests, CI, containers and fallback behaviour. |
| Architecture and scalability | Online request path, offline training path, search index, parallel retrieval, monitoring and deployment views. |
| Governance and ethics | Data provenance, privacy, access, explainability, popularity loops, licensing and release controls. |
| Professional practice | ADRs, experiment register, technical documentation, stakeholder-facing demo and honest negative results. |
| Continuous development | Review of current search and ranking methods, iterative experiments and documented learning checkpoints. |

## 20. Finished implementation plan

| Stage | Focus | Completion output |
|---|---|---|
| 1 | Create project controls | Repository, experiment register, ADRs, scope and permitted data rules. |
| 2 | Build the visible search journey | Static Next.js search route, card, grid and all page states. |
| 3 | Create primitive baselines | Substring and token search, with failures recorded. |
| 4 | Build product foundation | PostgreSQL product/variant model, ingestion and quality gates. |
| 5 | Connect the application | FastAPI endpoints and typed front-end requests. |
| 6 | Complete search-related commerce | Product detail, size/colour, basket simulation, browsing, filters and sorting. |
| 7 | Instrument and label | Sessions, search IDs, events, relevance judgments and splits. |
| 8 | Create lexical baseline | PostgreSQL comparison, OpenSearch BM25 and controlled tuning. |
| 9 | Understand queries | Deterministic attributes and constraints, optional LLM parser experiment. |
| 10 | Add semantic retrieval | Embedding-text experiments, product vectors and vector-only analysis. |
| 11 | Build hybrid retrieval | RRF baseline, alternative fusion comparisons and parity tests. |
| 12 | Guarantee safety | Eligibility, transparent rule ranking and diversity control. |
| 13 | Train learned ranking | Grouped feature data, simple learned baseline, LightGBM and fallback. |
| 14 | Add bounded context | Session features and optional advanced recommender experiments. |
| 15 | Operationalise | Regression, failure, sync and drift tests; containers, CI, deployment and monitoring. |
| 16 | Conclude | Freeze, held-out evaluation, model/data documentation, ethics and complete journey publication. |

**Final architecture recommendation.** Use Next.js for the user interface, FastAPI for
orchestration, PostgreSQL as the product source of truth, OpenSearch for BM25 and vector
retrieval, RRF as the initial fusion baseline, explicit eligibility rules, LightGBM LambdaRank
only after sufficient labelled data, anonymous bounded session features, and a separate offline
evaluation and training path with versioned artefacts and fallbacks.

## 21. Sources and reference material

The following sources informed the architecture framing. Internal documents should be
interpreted within their intended organisational context; StyleSeek adapts their lifecycle and
control themes to a learning prototype.

| Source | Relevance |
|---|---|
| Internal: `StyleSeek_Beginner_Friendly_Build_Journey.docx` | Existing beginner handbook containing the detailed step and code journey. |
| Internal: `User Applications Standard.pdf` | Describes a secure operational ML lifecycle including requirements, ingestion and preparation, development and testing, deployment, monitoring and assurance. |
| Internal: `AI Project Governance Playbook v0.2.pptx` | Describes lifecycle phases including discovery, scoping, delivery, deployment, data quality, success metrics, integration, monitoring and handover. |
| Internal: `BT CDH 2.0 - Target Architecture Specification & Recommendation Blueprint (4).pdf` | Provides internal examples of data-quality assertions, failure gating, lineage, policy tags and workflow consolidation. |
| Internal: `Architecture Resources.aspx` | Points to internal data governance, architecture, security, privacy, API gateway and cloud-data resources. |
| OpenSearch hybrid search documentation | Describes hybrid keyword and semantic search, search pipelines, score normalisation and RRF. |
| OpenSearch hybrid optimisation documentation | States that the best combination depends on data, behaviour and domain, and uses query sets, judgments and configurations for experiments. |
| LightGBM LGBMRanker documentation | Documents the LightGBM ranking estimator and LambdaRank objective. |
| LightGBM advanced topics | Documents integer relevance labels for LambdaRank and notes position bias in implicit-feedback ranking data. |

## 22. Final project narrative

StyleSeek should be presented as an evidence-led architecture journey, not as a website on which
AI was added at the end. The front end creates the observable user behaviour. The API creates a
controlled boundary. The catalogue creates reliable searchable information. The evaluation set
creates an objective decision mechanism. Lexical retrieval creates a strong baseline. Semantic
retrieval broadens meaning-based recall. Fusion combines complementary candidates. Rules protect
eligibility. Learning-to-rank is introduced only when the data supports it. Personalisation
remains bounded by explicit intent. Operations, monitoring and governance make the result
credible.

**The final story.** Build a working version, test it, identify a limitation, design the
smallest useful experiment, measure the result, retain or reject the change, and preserve the
evidence. The architecture grows only when the evidence justifies the additional complexity.

---

- The task is clear.
- The architecture is modular.
- The data has a source of truth.
- The search has a credible baseline.
- The ML has an evaluation contract.
- The service has fallbacks.
- The journey includes negative results.
- The final claims remain traceable to evidence.
