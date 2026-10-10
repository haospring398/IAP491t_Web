# Email analysis frontend

Next.js App Router, TypeScript and Tailwind frontend from the PhishingEmailDetection project. Selecting a file sends nothing; Analyze sends exactly one nonempty `.eml` file of at most 2 MiB. Results are Legit or Spam / phishing for the current binary model. Spam and phishing share the positive class; phishing-only accuracy has not been established.

## Local development

Node 24.x is required. From the repository root:

```powershell
cd web/frontend
npm.cmd ci
Copy-Item .env.example .env.local
npm.cmd run dev
```

Open http://127.0.0.1:3000. Without a configured AI service the interface works and Analyze reports MODEL_UNAVAILABLE. There is no simulated classification fallback. Files and results are held in memory and cleared on refresh.

## Vercel

Import this GitHub repository and select:

| Setting | Value |
| --- | --- |
| Production branch | master |
| Framework preset | Next.js |
| Root Directory | web/frontend |
| Node.js version | 24.x |
| Install Command | npm ci |
| Build Command | npm run build |
| Output Directory | Default |

Enable **Include source files outside of the Root Directory in the Build Step** so the sibling `web/contracts/` directory is available. Use the frontend directory for this Vercel project; the repository root contains an existing unrelated Vite application.

References: [Vercel shared-source settings](https://vercel.com/docs/monorepos/monorepo-faq), [Node.js versions](https://vercel.com/docs/functions/runtimes/node-js/node-js-versions).

Leave AI variables unset for a UI-only deployment. When a compatible separate HTTPS AI service is hosted, configure **server-only** `ML_API_URL` and `ML_API_TOKEN` in Vercel and redeploy. The token must match that service. Never prefix these with NEXT_PUBLIC or commit a real token. Use separate preview and production credentials. Vercel cannot reach the developer's localhost.

The proxy requires the [shared contract](../contracts/README.md): authenticated POST `/v1/analyze`, GET `/v1/analysis-status?request_id=<uuid>`, matching X-Request-ID, canonical response schemas, trusted deadlines and bounded response/upload consumption. The Python backend, model files and training data are not included in this frontend publication. Hosting and qualifying the AI service is a separate step.

## Verification

```powershell
npm.cmd run contracts:check
npm.cmd test
npm.cmd run lint
npm.cmd run build
npm.cmd run test:integration
$env:PLAYWRIGHT_CHANNEL = 'msedge'
npm.cmd run test:browser
```

Integration tests use a loopback fixture. Browser tests use marked sample responses; neither establishes model accuracy. `test:real-model` is retained for the original full AI repository and requires its Python backend, model artifacts and environment; it does not run from this frontend-only checkout.

Contracts are generated from the sibling schema files. After a coordinated schema revision run `npm.cmd run contracts:generate`, then commit `lib/contracts.generated.ts`. `contracts:check` rejects generated-type drift.

Adapted MIT source attribution is in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [LICENSE](LICENSE).
