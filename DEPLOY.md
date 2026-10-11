# Deploy Bankism Sentinel

The local build, production mode and smoke test were verified. **No live URL is claimed.** Render and Vercel integrations were discoverable but unconnected, their CLIs were absent, and no provider tokens were found. Connect the services in Codex to allow assisted deployment, or follow the steps below. Account setup, provider queueing and builds determine elapsed deployment time.

## 1 Push the source to GitHub

Create a repository in your own account, then run from `D:\bankism-sentinel`:

```powershell
git init
git add .
git commit -m "Build Bankism Sentinel synthetic guardrail MVP"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/bankism-sentinel.git
git push -u origin main
```

Replace YOUR_ACCOUNT. `.gitignore` excludes credentials, databases, runtime logs and installed dependencies. Review the staged files before pushing. Include `backend/tests/attack_cases.json`; the evaluation endpoint loads this fixed dataset.

## 2 Create the Render backend

In [Render](https://dashboard.render.com), choose New → Blueprint and select the repository. The root `render.yaml` declares a Python free web service:

```text
Root directory: backend
Build: pip install -r requirements.txt
Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
Health check: /health
Python: 3.12.10
```

Render generates independent `INTENT_HMAC_KEY` and `SESSION_SIGNING_KEY` secrets. Set `ALLOWED_ORIGINS` initially to the intended Vercel production origin, or a temporary exact localhost origin for smoke testing. Never set `*`. `ENV=production` refuses missing signing keys or origins and disables API docs. Leave LLM_API_KEY absent for the verified offline demonstration. If enabling Gemini, add it to Render's environment and retain LLM_PROVIDER=gemini/LLM_MODEL=gemini-2.5-flash. For OpenAI, set LLM_PROVIDER=openai and a currently supported structured-output model name in LLM_MODEL. Provider integration is coded and mocked in tests but requires your own live verification.

Copy the actual backend URL after Render reports a successful deployment. Check `/health`. If using a proxy-derived client IP, configure Uvicorn's trusted proxy setting only for Render's documented ingress; never trust arbitrary caller-supplied X-Forwarded-For. Per-session quotas still apply independently.

## 3 Create the Vercel frontend

In [Vercel](https://vercel.com/new), import the same repository:

```text
Root directory: frontend
Framework: Vite
Build: npm run build
Output: dist
Node: 22.12+ (24 is verified locally)
VITE_API_BASE_URL: the actual Render HTTPS URL, without a trailing slash
```

`frontend/vercel.json` includes the SPA fallback, security headers and long-lived caching for hashed assets. Changing VITE_API_BASE_URL requires a new build. Vite environment variables are public: never put server keys in them.

Optional Vercel CLI flow after installing the official CLI and authenticating:

```powershell
cd D:\bankism-sentinel\frontend
npx vercel login
npx vercel link
npx vercel env add VITE_API_BASE_URL production
npx vercel --prod
```

The Render Blueprint/dashboard remains the documented backend creation method. No invented Render CLI command is necessary.

## Optional single-service fallback

To serve the UI and API from one Render URL, use the full repository as the service root (clear `rootDir: backend` in a separate deployment configuration). Set `SERVE_FRONTEND=true`, `VITE_API_BASE_URL` to that service's actual HTTPS origin and `ALLOWED_ORIGINS` to the same origin. Keep the production signing keys.

```text
Build: pip install -r backend/requirements.txt && npm --prefix frontend ci && npm --prefix frontend run build
Start: uvicorn --app-dir backend app.main:app --host 0.0.0.0 --port $PORT --workers 1
Health: /health
```

The build requires Node 22.12+ as well as Python; confirm Node is available in the chosen hosting runtime, or build `frontend/dist` in a trusted build environment and include it in the deployment artifact. Do not use the frontend sibling directory with a backend-only repository root. Use the service's actual assigned URL, never assume its hostname. If configuring an existing backend, its URL is already available in Render. A new service can first deploy the API, then set the frontend environment to the assigned URL and rebuild with this fallback.

`SERVE_FRONTEND=true` mounts the built index and assets after the API routes. A static integration test verifies root HTML, an actual built asset, health and authenticated accounts through the same service. All UI pages use application state at the root URL. Production-mode browser verification of the built UI was performed locally.

Local equivalent after building the frontend:

```powershell
cd D:\bankism-sentinel
$env:SERVE_FRONTEND='true'
.\.venv\Scripts\python.exe scripts/start_production_local.py
# Open http://localhost:8000
```

## 4 Set final CORS origin

Copy the actual Vercel origin into Render ALLOWED_ORIGINS and redeploy the backend. Multiple controlled origins are comma-separated. Optional preview deployment support requires a tightly scoped explicit ALLOWED_ORIGIN_REGEX; there is no default acceptance of arbitrary `*.vercel.app` sites. Avoid enabling previews until needed.

## 5 Verify the real URLs

```powershell
cd D:\bankism-sentinel
.\.venv\Scripts\python.exe scripts/smoke_test.py https://YOUR-ACTUAL-RENDER-HOST
```

Smoke checks health/schema/request IDs, balance, prepare→confirm→execute, malicious memo zero debit, replay zero debit, customer 403 on analyst audit, and parameter substitution zero debit. Open the Vercel site, select Aditi, run the normal transfer, malicious memo and containment demos, then select analyst and inspect the timeline. Verify mobile layout too. Only report a live application after these checks pass at the deployed URLs.

## Free hosting and persistence

Free Render services can spin down; the first request can be slow. The frontend retries only the read-only readiness request with backoff and displays “Waking up the secure server…”. Financial mutations are never automatically retried. If a response is lost after execution, check history; do not submit a new payment without verifying the outcome.

Render free service files are ephemeral. Tables and synthetic seed data auto-create on an empty database; restart/redeploy can reset all balances, intents and audit data. This is acceptable only for the labeled hackathon demo. For durability, configure a paid disk or an external durable PostgreSQL DATABASE_URL; PostgreSQL via psycopg is included. Postgres integration still needs staging validation. Run one worker and one instance; distributed deployments need Redis quotas/budget/cache coordination and an external audit sink. Never rotate signing keys without accounting for outstanding intents and sessions.

An optional uptime monitor may request `/health`, subject to hosting terms and quotas; correctness never depends on keeping the service warm.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Browser cannot call API | Compare exact Origin with ALLOWED_ORIGINS, confirm HTTPS API URL, then redeploy |
| Configuration error in frontend | Set VITE_API_BASE_URL and rebuild Vercel |
| Signing-key startup failure | Use independent random server keys of at least 32 characters; do not add them to Vite |
| Port binding failure | Use `$PORT` on Render, `--host 0.0.0.0`, one worker |
| Slow first request | Wait for the free instance to wake; inspect health; retry readiness, not payment mutations |
| Python install fails | Use .python-version 3.12.10 and the pinned requirements |
| State reset after redeploy | Expected with free SQLite; use durable DB for persistence |
| Audit 403 | Select the analyst demo session; customer tokens intentionally lack access |
| Transfer REVIEW during outage | Fix provider key/model/network, wait for circuit cooldown; do not bypass the guard |
| Transfer limit reached during tests | Run load tests on disposable local demo data with the provided verification launcher |

Configuration references: [Render Blueprint specification](https://render.com/docs/blueprint-spec), [Render free-service limits](https://render.com/docs/free), [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite), [Vercel rewrites](https://vercel.com/docs/routing/rewrites).
