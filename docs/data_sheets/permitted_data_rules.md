# Permitted Data Rules

Source: `STYLESEE1.docx` §2.2, §11, §16. These rules apply to every stage of the project, not
just catalogue ingestion.

1. **No proprietary retailer assets.** No ASOS (or any real retailer) branding, product
   imagery, copy or code is used anywhere in StyleSeek. StyleSeek is inspired by the *type* of
   shopping journey large retailers offer, not a clone of one.
2. **Provenance before ingestion.** Every external dataset must have its source, licence,
   transformations and synthetic/real status recorded in `docs/data_sheets/` before it is used
   — see [`catalogue_data_sheet.md`](catalogue_data_sheet.md) as the running example.
3. **Synthetic data is always labelled.** Any generated price, stock, variant, session or event
   data must be clearly marked as synthetic in its schema/metadata and never presented as, or
   mixed silently with, genuine data.
4. **No real personal data.** Sessions are anonymous by default. Real participant data (e.g. for
   a blind user evaluation, architecture §15) requires an appropriate lawful, approved process
   before collection — not assumed permissible by default.
5. **Secrets never enter the repository.** Kaggle credentials, database passwords, API keys and
   connection strings live in a local, git-ignored environment file (or managed secret store in
   a cloud build) — never committed, never hardcoded.
6. **No protected-characteristic targeting.** Personalisation and ranking must not use or infer
   protected characteristics.
7. **Fail closed on invalid data.** Data failing the quality gates in architecture §8.3 is
   quarantined or rejected, never silently passed downstream.
