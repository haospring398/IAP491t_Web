# Local Real-Model Demonstration

> **Update 2026-10-21 — 19-10 run serving (supersedes the pinned legacy run below).** Root `preprocess.py` now emits 53 engineered features, so the legacy run `e7dcdcc3551e46fc93582836f4a74976` can no longer be served. The local demo instead serves one 19-10 baseline run (`runs/<name>/dumped_models/classification/run_manifest.json`, schema 2) pinned by `RUN_PATH` in `web/backend/policy.py` or `IAP_WEB_RUN_PATH`; since 2026-10-23 it is `runs/2026-10-23_web2` (XGBoost selected on validation; local only, `runs/` is not versioned). Disclosed local exceptions approved by the user on 2026-10-21:
> - A positive result from a `target_mode: phishing` run emits `phishing` (UI "Phishing"); a `broad` run emits `spam_or_phishing`. Evidence is validation-only; this is not E0, test-set or phishing-only quality qualification.
> - The served classifier is the manifest's validation-selected `selected_model` with its validation threshold, overriding AD-2's explicit-selection rule for this local demo. BERT selections are refused.
> - The always-visible notice reads "Local demo model: phishing detection accuracy has not been independently established."
> - Startup verifies manifest completeness, every artifact hash, the ordered feature schema, the recorded preprocessing signature and loaded classes/widths. Serving reuses the training preprocessing (`pipeline_cache._process`) and Doc2Vec inference (`preprocess.infer_document_vector`), replacing the frozen legacy settings described below.
> - Since 2026-10-24 a success from the pinned run also carries its AD-14 factor explanation (the selected XGBoost supports exact contributions). Until Q9 is decided, the local catalogue shows `is_html` with the provisional note "known dataset bias" rather than hiding it; Q9 may replace this. Local factors explain this run only and add no quality claim.

Applies to CAP-1 through CAP-6. The user's 2026-10-06 approval authorizes a local demo using the existing pipeline now, followed by a whole-release upgrade. This companion overrides conflicting E0-before-real-inference, exact two-label vocabulary, qualified-bundle-only and Linux/Docker-only clauses **only for this disclosed local legacy demo**. Adopted PRD/UX/architecture remain unchanged historical target documents; their final phishing-only qualification and cloud gates still apply. No implicit cloud or E0 acceptance results from this exception.

## Target and application boundary

| Release | Class 0 | Class 1 | Qualification |
| --- | --- | --- | --- |
| Existing local mixed-positive demo | `legit` / Legit | `spam_or_phishing` / Spam / phishing | Actual compatible artifacts and bounded operational inference; no phishing-only accuracy claim |
| Future phishing-only release | `legit` / Legit | `phishing` / Phishing | Reviewed target-specific E0 and the full existing release contract |

The model remains binary; the shared protocol can represent both release targets. The success envelope is `analysis_status`, `label` and the optional AD-14 `explanation`, accepting these three declared label values only. A visible English notice states that the local model's positive class includes spam and phishing and phishing-only accuracy has not been established. Do not call actual legacy inference a sample or synthetic result. Marked fixtures remain samples and cannot count as actual model execution. Do not add a third model class, score or export instructions; AD-14 factors are the only explanation.

Keep the upload page, explicit Analyze, attempt filename, five states, strict schemas/errors, status observations, retries, server-only Bearer token and shared transport limits/deadlines. Update strict schema/type/UI/test consumers together. Mixed positives must never emit `phishing`; unknown labels fail closed. Preserve no-queue admission, bounded killable child execution, transient uploads, no remote content fetching and no sensitive logs.

## Current local inference release

Use startup-pinned immutable run `e7dcdcc3551e46fc93582836f4a74976` and its XGBoost, Doc2Vec and scaler after full run verification plus loaded object checks. No loose fallback or pointer hot swap. This selection is an existing packaging candidate, not a new quality-based winner decision. Actual inventory confirms widths 100 + 40 = 140 and classes 0/1; startup still verifies those facts rather than trusting this document.

Extract raw-byte engineered features before cleaning; use current `FEATURE_NAMES`, the fitted scaler, and Doc2Vec-first concatenation. Freeze local stopwords to the observed sklearn fallback (preserving negations), skip unavailable WordNet, preserve saved inference defaults and serialize RNG capture/reset/restore with fixed process hash seed and content/release seed. Record settings/code and actual packages for operational attribution. No runtime corpus download, fitting, training or evaluation imports.

Saved Doc2Vec has one inference epoch and negative alpha/min-alpha approximately -0.035. This inherited setting is retained to demonstrate current behavior, not endorsed as sound training or accuracy. Changing it later needs a separately evaluated coherent release. Existing manifest lacks complete preprocessing/environment/label provenance; compatible loading does not establish historical training equivalence.

The native Windows environment may be used for this local demo. Its sibling-venv dependency is an operational limitation and must be documented; never present it as a portable lock or distribute the virtualenv as a self-contained release. Locked Linux/Docker packaging, whole-container cloud resources and timing qualification remain future obligations. Bind both services to loopback; no deployment/publication is authorized.

## Verification and upgrade

Demonstrate real MIME bytes through the adapter, Python API, Next proxy and browser. Record actual case counts, dimensions, repeat/order/restart agreement and operational errors without attributing fixture outputs to accuracy. Required failure checks cover artifact/readiness, auth/correlation, input/MIME/work limits, busy admission, deadline/cleanup/recovery and unavailable service. Distinguish existing failing offline tests from new demo checks.

Upgrade code, preprocessing/resources, dependency environment, classifier, Doc2Vec, scaler and manifest together. Review label provenance and independent evaluation for the new target, qualify its explicit inference/resource settings and only then emit `phishing`. Preserve prior runs/pointer and rollback the whole compatible release. The HTTP/application boundary and existing frontend workflow survive the replacement; quality criteria and E0 remain unresolved until evidence exists.
