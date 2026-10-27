<!-- bmad:context -->
<!-- Verified 2026-10-20 against 5cce305 plus the uncommitted 19-10 pipeline working tree. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## PhishingEmailDetection

Python email-classification pipeline using Doc2Vec and engineered features (19-10 upstream version), plus a local web demo in web/ (Next.js frontend, Python backend) serving one pinned 19-10 baseline run with its label and exact per-result factor explanation (AD-14).
Read README.md for setup. BMad planning artifacts belong in _bmad-output/; web/docs/ holds synced snapshots of them.

## Policy

- Never modify, move or delete Dataset/, paper/, model/, existing runs in runs/, or the legacy web run dumped_models/classification/runs/<run-id>/ (selected by current.json, no longer served). Write each new training/evaluation run to a new runs/<YYYY-MM-DD_name>/ folder.
- Write README content, code comments and commit messages in Vietnamese. Keep web UI copy in English (required by the SPEC) and BMad documents in English (_bmad/config.toml).

## Where things are

- Change corpus loading in load_data.py and feature extraction in preprocess.py.
- Trace training through train.py and artifact verification/publication through artifact_store.py; evaluation through evaluate.py.
- Use analyze_feature_importance.py to investigate reliance on dataset-source features.
- web/backend/adapter.py serves the schema-2 run pinned by RUN_PATH in web/backend/policy.py or the IAP_WEB_RUN_PATH environment variable (currently runs/2026-10-23_web2; runs/ is not in git, so other machines must train it or set the variable). It does not import the root preprocess.py and pipeline_cache.py: web/backend/__init__.py puts web/backend/frozen_pipeline/ first on sys.path, and that folder holds byte-exact copies (from commit dd166b2) of the code that trained the pinned run, so the root pipeline can follow upstream without breaking the demo. The adapter uses private names from them (_parse_email, _safe_decode, _english_stopwords, reset_extraction_stats, infer_document_vector, _process, preprocessing_signature) and rejects runs whose recorded preprocessing signature differs; the signature hashes the copies' bytes, so never edit or reformat them (.gitattributes disables line-ending conversion there). To serve a run trained with newer root code, replace both copies with byte-exact copies of the root files that trained it, re-pin RUN_PATH and run the web backend tests. The web backend tests train their fixture through root train.py but with the frozen modules, because importing web.backend sets the path first.
- Per-result explanations are computed in web/backend/adapter.py from the served classifier's exact contributions; factor display text lives in web/contracts/explanation-factors.json, which must cover every preprocess.FEATURE_NAMES entry, so update it whenever FEATURE_NAMES changes.
- Change the HTTP contract in web/contracts/*.schema.json, then run npm.cmd run contracts:generate in web/frontend; never hand-edit web/frontend/lib/contracts.generated.ts.
- Edit canonical documents in _bmad-output/ or this file, then run node web/scripts/sync-docs.mjs; never edit web/docs/ snapshots directly.

## Running and verifying

- Run pipeline commands and .venv/Scripts/python.exe -m web.backend from the project root; artifact_store.py, the web.backend import and relative --output/--run/--model-dir paths resolve from the working directory.
- Use .venv/Scripts/python.exe as documented in README.md; configure dependencies and NLTK resources there before pipeline runs.
- Pipeline code follows the 19-10 version of buidangduy05/IAP491t_backups (commit ae08251): `train.py --output runs/<YYYY-MM-DD_name>`, `evaluate.py --run runs/<...>`. The pieces missing upstream (specialists.py, pipeline_cache.py, BertEmailClassifier, split_train_validation_test, prepare_semantic_text, attachment inspection) were supplied on 2026-10-21; BERT needs torch/transformers from requirements.txt.
- On 2026-10-27 upstream commits 063bf8b, c387f01 and b535958 were three-way merged file by file against upstream 0175c00 (the histories are unrelated, so git merge does not apply); local additions such as infer_document_vector, baseline --cache-dir/--workers and the column drops in prepare_data were kept. To pull later upstream commits, merge against b535958 the same way.
- Do not use runs/2026-10-19_bert for inference or the web demo: it predates the current preprocessing signature, lacks test arrays and two BERT tokenizer hashes differ from its manifest.
- Before reporting metrics, verify the selected run's manifest and hashes, matching test sample counts, and feature dimensions compatible with the scaler, Doc2Vec and classifiers.
- Use classifiers, Doc2Vec, scaler and test arrays from the same training run; do not substitute legacy loose artifacts.
- Run evaluate.py only when report regeneration is intended; it overwrites evaluation_results.csv and plots in the run folder it is given. Its main guard prevents evaluation on import.
- Root tests: .venv/Scripts/python.exe -m unittest discover -s tests -v. On 2026-10-27, 36 passed and 1 was skipped (the QR test needs zxing-cpp, which requirements.txt omits); this includes test_shap, and test_pipeline's BERT test needs transformers.
- Web backend tests: .venv/Scripts/python.exe -m unittest discover -s web/backend/tests -v (37 tests on 2026-10-24, about 1.5 minutes; they train a small synthetic fixture run and point IAP_WEB_RUN_PATH at it). Frontend checks are in web/backend/README.md; use npm.cmd, not npm, in PowerShell.
- Git work-tree scans are slow because Dataset/ tracks about 542k files: git status exceeded 100 s and a path-limited git diff --stat took about 60 s. Limit git commands to the paths you changed and allow a long timeout.
- Report actual validation performed; no CI configuration was found.

## Conventions that differ from defaults

- Deduplicate before splitting train/test data.
- Extract engineered features from raw email before cleanText removes information needed by extraction.
- Fit the engineered-feature scaler on training data only.
- Derive feature order and count from preprocess.FEATURE_NAMES rather than numeric comments.
- Preserve concatenation order: Doc2Vec followed by scaled engineered features. analyze_feature_importance.py hardcodes DOC2VEC_DIM = 100; update it when changing embedding dimensions.
- Preserve labels 0=legitimate and 1=positive; disclose that SpamAssassin spam is included in the positive class when that corpus is used.
- Preserve Windows path handling in load_data.py when changing corpus access; it supports Enron filenames with trailing dots.

## Known pitfalls

- Verify saved artifacts against current code before reporting metrics; this workspace has contained test arrays with mismatched sample counts and an outdated feature dimension.
- Do not attribute backup logs to the current version without matching code and artifacts.
- Preserve positive-class probability ROC-AUC for both CSV and ROC plots; predicted labels are used for classification metrics.
- Before repeating a costly full evaluation for provenance, inspect the existing successful evaluation log and selected run. Recompute only when evidence is missing, inconsistent or recomputation is explicitly requested.
- Do not restore num_received_hops or has_date_header to FEATURE_NAMES without reassessing source bias; their removal is documented beside FEATURE_NAMES.

<!-- /bmad:context -->
