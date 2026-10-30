- source_spec: `_bmad-output/implementation-artifacts/spec-reliable-evaluation-artifacts.md`
  summary: Add a training-run manifest to prove that test arrays, scaler, Doc2Vec, and classifiers belong together.
  evidence: Equal sample counts and feature widths can still allow artifacts from separate runs to produce plausible but invalid metrics; train.py currently emits no shared run identifier.
- source_spec: `_bmad-output/implementation-artifacts/spec-reliable-evaluation-artifacts.md`
  summary: Publish evaluation CSV and plots as one consistent report set.
  evidence: evaluate.py writes the CSV before rendering plots, so plotting failure can leave new metrics beside old images; this behavior predates the current fix.
- source_spec: `_bmad-output/implementation-artifacts/spec-reliable-evaluation-artifacts.md`
  summary: Refresh the ROC-AUC warning in AGENTS.md after the evaluation change.
  evidence: The managed context block says the CSV uses predicted labels, but evaluate.py now uses positive-class probabilities for both CSV and plot; editing the managed block belongs in a project-context refresh.
  resolved: 2026-10-20 bmad-project-context refresh; the AGENTS.md block states positive-class probability ROC-AUC for both CSV and ROC plots.

- source_spec: '_bmad-output/implementation-artifacts/spec-move-backend-to-web.md'
  summary: Document the web/backend package and its test command in the root agent guidance.
  evidence: Existing AGENTS.md covers only the root pipeline; this workflow defers agent-guidance edits. Current service README already documents the relocated package and passing suite.
  resolved: 2026-10-20 bmad-project-context refresh; the AGENTS.md block documents web/backend's dependency on root modules and its test command.


- source_spec: `_bmad-output/implementation-artifacts/spec-web-standalone.md`
  summary: Let backend tests in a git clone of web/ (no bundle) get the exact NLTK stopwords/wordnet the fixture was trained with, e.g. by shipping them beside the fixture.
  evidence: The fixture records lemmatization and NLTK stopwords; without web/model/nltk_data or the root .venv data the preprocessing signature differs and adapter tests fail at MODEL_COMPATIBILITY.
- source_spec: `_bmad-output/implementation-artifacts/spec-web-standalone.md`
  summary: Tie bundled NLTK data to each run and verify it at bundle time (stopwords against the manifest, a hash of wordnet.zip).
  evidence: web/model/nltk_data is shared and replaced by every bundle; wordnet content is not part of the preprocessing signature, so a different wordnet.zip changes lemmatization without rejection.
