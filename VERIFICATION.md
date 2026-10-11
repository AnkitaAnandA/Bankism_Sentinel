# Verification report

Verified on the user's Windows PC, 11 October 2026. Sources were read from the project mirror and the original Pasted text attachment; synced references were not changed. Code was built in the permitted workspace, copied to `D:\bankism-sentinel`, and source hashes compared. Local execution is a synthetic demo, not a publicly hosted or real-bank application.

## Milestones

| Milestone | Result |
|---|---|
| M1 Synthetic bank | Three users, checking/savings accounts, approved/unapproved payees, idempotent seed and atomic debit/credit |
| M2 Input security | Original-preserving normalization, Unicode/spacing/encoding views, typed contextual rule findings |
| M3 Intent and classification | Bounded typed money parser, offline mock, provider adapters, timeout, retry, circuit breaker, TTL/LRU cache, call budget |
| M4 Financial boundary | Canonical HMAC, consent, immutable corrections, ownership, policy recheck, expiry, one-use state and idempotency |
| M5 API and UI | Required APIs, schema-valid error paths, bearer demo identities, CORS, quotas, audit pagination, three React pages |
| M6 Evaluation | 81 labeled cases, three real isolated sandbox configurations, replay/tamper scenarios and measured latency |
| M7 Deployment preparation | Render/Vercel files, examples, production startup, clean install and smoke verification; live hosting outstanding |

## Functional requirements

| Requirement | Status and evidence |
|---|---|
| FR-01 Intake | Implemented; strict fields, typed context, 2,000-character and 16-KiB caps |
| FR-02 Normalize | Implemented; multiple derived views, original preserved, one-depth bounded decoding |
| FR-03 Hybrid detection | Implemented; deterministic findings plus independent offline semantic heuristic; real adapters tested with HTTP mocks only |
| FR-04 Extraction | Implemented; balance/history, transfer, informational/unknown; integer paise, Indian grouping and bounded word amounts |
| FR-05 Policy | Implemented; ownership, role, approved payee, currency, positivity, balance and limits |
| FR-06 Intent Lock | Implemented; sorted compact UTF-8 canonical JSON, HMAC-SHA256, constant-time comparison, separate state |
| FR-07 Consent | Implemented; server-generated review, tag confirmation, cancellation, new lock for corrections |
| FR-08 Verdict API | Implemented; schema checks include 401/403/404/409/413/422/429/500 and CORS preflight rejection; request IDs |
| FR-09 Attack suite | Implemented; isolated offline evaluation endpoint and comparison UI |

## Executed checks

- Fresh Python environment installation succeeded with the final pinned dependencies.
- 134 pytest tests passed; `reports/tests.xml` records the test run. Framework deprecation warnings remain because the requested ORJSONResponse and httpx TestClient interfaces are still supported but deprecated in the current framework.
- Strict mypy passed on all 28 application files, with no exclusions. Ruff and Black passed. TypeScript production build and ESLint passed.
- Python and npm advisory audits returned no known vulnerabilities for the final pins at verification time. Reports retain the initial and final audit results for reproducibility.
- Six individual HMAC field-tamper cases and all state-table combinations passed. Guard tests independently exercise authorization, consent, tag, expiry, field mismatch, updated beneficiary policy, duplicate key and classifier health.
- Sixteen concurrent guard executions produced exactly one transfer. A fault after debit rolled back debit, credit, state and ledger record.
- Production smoke: health/schema/request ID; balance; transfer journey; malicious memo/no debit; replay/no second debit; customer 403 on analyst events; substituted payment fields/no debit. All seven passed.
- Browser walkthrough: customer transfer prepared, confirmed and marked EXECUTED; malicious memo returned BLOCK; substituted payment returned BLOCK with unchanged balance; the evaluation table populated; analyst audit and counts loaded. Narrow/mobile and 1280-pixel desktop layouts were inspected.

## Comparative evaluation

81 synthetic cases: 44 malicious, 25 benign, 12 ambiguous. B uses MockClassifier, not a live LLM. A/B deliberately omit financial authorization inside isolated disposable ledgers; unsafe behavior is not selectable in application execution.

| Configuration | Recall / contextual containment | False positives | Unauthorized sandbox transfers | Schema validity | Valid completion | Replay prevention | Tamper rejection |
|---|---:|---:|---:|---:|---:|---:|---:|
| A Keyword-only | 29.5% | 16% | 20 | 100% | 100% | 0% | 0% |
| B Mock-only | 9.1% | 0% | 26 | 100% | 100% | 0% | 0% |
| C Hybrid + lock + guard | 100% | 0% | 0 | 100% | 100% | 100% | 100% |

Recall includes the replay, tamper and outage control results; do not interpret it as pure model detection recall. Replay/tamper dataset denominators are each one; regression tests supply broader coverage. `reports/evaluation.json` is the raw result. This is feasibility evidence on synthetic cases, not assurance for real banking or a held-out production benchmark.

## Performance

| Path | Samples | p50 ms | p95 ms | p99 ms | Throughput |
|---|---:|---:|---:|---:|---:|
| HTTP analyze, offline | 100 | 9.805 | 13.166 | 19.740 | 98.85 requests/s |
| HTTP prepare | 100 | 15.169 | 30.319 | 47.716 | 56.70 requests/s |
| HTTP execute | 100 | 16.149 | 47.415 | 66.376 | 17.86 full journeys/s |
| Deterministic core including SQL policy | 500 | 1.036 | 2.171 | 2.675 | Not measured |

Local fresh-table startup to first health response: **1.398 seconds**. Main frontend JS: **193.07 kB / 61.41 kB gzip**; lazy pages approximately 3.19, 6.31 and 6.84 kB. HTTP benchmark is sequential localhost, not a parallel saturation test. Execute throughput includes prepare/confirm overhead. Real LLM and hosted cold-start latency were not measured. Raw files: `reports/core.json`, `reports/load.json`.

## Remaining work

Public Vercel/Render deployment could not be performed with the currently unconnected integrations and absent CLI tokens. No public URL is claimed. Connect those services and push the source to a chosen repository, or use the exact Blueprint/Vercel steps in `DEPLOY.md`, then run smoke tests against the real backend URL and verify the real frontend.

Real provider verification and a live Postgres integration test remain outstanding. Real-bank identity, step-up confirmation, fraud controls, durable external audit, distributed quotas, stronger held-out detection evaluation and secure key lifecycle are future production work. The local D-drive application and synthetic financial boundary are verified; public hosting is not yet completed.
