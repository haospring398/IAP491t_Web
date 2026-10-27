# Web workspace

This folder contains the frontend, Python backend, shared contracts and documentation for
handover to another developer. Keep `frontend/` and `contracts/` together.

```text
web/
  backend/            Local Python API, inference adapter, samples and tests
  frontend/           Next.js application, server proxy, tests and MIT attribution
  contracts/          Runtime schemas and shared transport policy
  docs/               Linked snapshots of spec, UX, architecture and requirements
  scripts/            Refresh documentation snapshots from this repository
```

## Run locally

Use Node 24.x. From the PhishingEmailDetection repository root:

```powershell
cd web/frontend
npm.cmd ci
Copy-Item .env.example .env.local
npm.cmd run dev
```

If you received `web/` as a standalone folder, enter its `frontend/` directory
instead. Open `http://127.0.0.1:3000`. To use the existing real local model, follow
the [Python-service instructions](backend/README.md): start it from the parent
project root, then configure server-only `ML_API_URL=http://127.0.0.1:8000` and the
same generated `ML_API_TOKEN` for the frontend. Empty configuration returns an
unavailable error with no classification. Demo hiển thị Legit, hoặc Phishing (run
`target_mode: phishing`) / Spam / phishing (run `broad`), kèm thông báo rằng độ chính
xác phát hiện phishing chưa được đánh giá độc lập. Backend cần một run 19-10 đã train
(xem `RUN_PATH` trong hướng dẫn backend).
See [frontend instructions](frontend/README.md) for checks and service boundaries.

The frontend's bundler and tracing root resolve to this `web/` folder, so its
build excludes the parent Python pipeline and corpora. Relative imports resolve
the sibling schemas regardless of whether the whole repository or only `web/`
is copied. The frontend source root is `web/frontend/` in this repository,
or `frontend/` in a standalone web workspace; keep sibling contracts available.

## Share with another developer

Copy this folder while excluding Python `__pycache__/` directories and `*.py[cod]`,
`frontend/node_modules/`, `frontend/.next/`,
`frontend/test-results/`, `frontend/playwright-report/`, `*.tsbuildinfo` and local
`.env*` files. Include `.env.example`, package files, schemas, source, tests and
MIT attribution. The recipient installs dependencies using `npm.cmd ci`.

The [documentation index](docs/README.md) points to the current spec, UX and
architecture snapshots. They are handover references; canonical BMad documents
remain in the parent repository's `_bmad-output/`. After changing canonical
documents, refresh the snapshots from this repository:

```powershell
node web/scripts/sync-docs.mjs
```

The snapshot refresh requires the full PhishingEmailDetection repository;
it is not needed to build or develop the copied frontend. Sharing `web/` includes
the Python service code and the frozen preprocessing copies in
`backend/frozen_pipeline/`; its model artifacts, the other root pipeline modules
(`train.py`, `evaluate.py`, `artifact_store.py`), datasets and Python environment
remain in the parent project. Running the current backend
requires that full project and its working model environment. Local real-model operational tests are separate
from pending phishing-only E0 eligibility and future cloud deployment. Nhãn Phishing
của run 19-10 là ngoại lệ local dựa trên bằng chứng validation, chưa qua E0.
