# Frontend redesign verification

Verified on the user's Windows PC, 11 October 2026. The new frontend is copied to `D:\bankism-sentinel\frontend` and served by the existing local application at `http://localhost:8000`. A fresh `npm ci` and production build succeeded in the D-drive project. All 41 backend files match the pre-redesign SHA-256 baseline. No backend route, schema, security implementation or backend test was changed.

## Executed checks

- Production TypeScript/Vite build, ESLint and Prettier checks pass.
- 10 precision/masking assertions pass, including negative amounts, one-paise values, Indian grouping, MAX_SAFE_INTEGER, rejection of unsafe/fractional input and preservation of server masking.
- 14 browser flow checks pass: role restrictions; balance; prepare/confirm/execute/receipt; double-click protection; cancellation; Rahul's target; event dialog and Escape; memo injection; evaluation; measured latency/containment scope; substitution rejection; expiry; persisted theme; cold start/error retry; keyboard submission/newline. Sensitive JSON fields are redacted in rendered and copied content; only theme preference is present in localStorage.
- 6 additional D-drive browser smoke checks pass with the actual server CSP active: static loading, prepare/cancel, analyst dashboard/charts, theme toggle, real memo-injection BLOCK and mobile overflow. No CSP relaxation or bypass was used.
- 24 axe-core WCAG 2 A/AA and 2.1 AA scans pass with zero detected violations: empty banking screen, payment review, analyst dashboard and evaluated Attack Lab × two themes × three viewports. These are automated checks on those states, not a general accessibility certification.
- 14 semantic foreground/background pairs meet the 4.5:1 AA threshold. Minimum measured ratio: 5.35:1. Reduced motion is respected; dialogs use native focus trapping and Escape; table regions can be reached and scrolled by keyboard.
- 36 before and 108 after full-page screenshots cover the requested 1440×900, 1024×768 and 390×844 sizes. The after set includes light and dark variants, plus dialog, cancellation, expiry, filtered-empty, containment and substitution states. Manifests and measurements are in `ui-verification.json` and `screenshots/before/manifest.json`.
- Empty audit, expired proposal, cold start and server-error screenshots are explicitly labeled browser fixtures. Actual banking, role, firewall, substitution and evaluation checks use the running FastAPI application with synthetic data.
- Dependency audit reports zero known vulnerabilities at verification time. Existing ESLint emits a support/deprecation notice; no dependency advisory was reported.

## Performance

| Measurement | Result |
|---|---:|
| Main initial JavaScript, gzip | 67,067 bytes (67.07 KB) |
| All JavaScript chunks combined, gzip (conservative upper bound) | 80,575 bytes (80.58 KB) |
| Main JavaScript, uncompressed | Approximately 211.94 KB |
| CSS, gzip | Approximately 7.90 KB |
| Self-hosted latin variable fonts | Inter 48.26 KB + JetBrains Mono 40.40 KB |
| Initial cumulative layout shift, measured Chromium run | 0 |
| Browser runtime errors in the full suite | 0 |

The 200 KB compressed-JS budget passes even when all lazy routes are counted. Fonts are separate assets, use swap and do not block rendering. The main UI font is preloaded; stable skeleton/account/header dimensions and an initial main-area reserve avoid visible loading shifts in the measured run. Page imports remain lazy.

## Preserved boundaries

Financial consent, signing, verification, policy and authorization remain server-owned. The frontend uses a synchronous submission latch and reuses its idempotency key for an uncertain execution retry; it never invents a successful receipt after a replay denial. Confirm controls are hidden for analyst identities and disabled/removed after expiry or terminal state. Raw verdict JSON excludes authentication tokens and integrity tags.

Approved-payee roster, live unauthorized-ledger totals and server latency are not exposed by the existing API. The UI labels demo payee examples, evaluation-derived containment and browser round-trip measurements honestly. Suggested API additions are documented only in `../DECISIONS.md`.

## Reproduce

See `../README.md`. Run `npm run build`, `npm run lint`, `npm run format:check`, `npm run test:format`, `npm run test:ui`, and `node scripts/smoke-local.cjs`. The browser tests use installed Chrome's Chromium engine and never download a browser. Full UI tests default to the frontend preview on port 4173; the D-drive smoke defaults to port 8000.
