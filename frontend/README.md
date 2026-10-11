# Bankism Sentinel frontend

The redesign is a static React/Vite/TypeScript application. It retains all existing API contracts and route-level code splitting. The runtime dependencies added are pinned Lucide icons and self-hosted Inter/JetBrains Mono variable fonts (latin normal subsets, swap). Playwright, axe-core and Prettier are development tools only.

## Local preview

Set `VITE_API_BASE_URL=http://localhost:8000` in an ignored `.env.local`. Run `npm ci`, `npm run build`, then `npm run preview -- --port 4173`. The backend must already be running and allow the preview origin. The existing D-drive server also serves `frontend/dist` at `http://localhost:8000`; a frontend rebuild does not require a backend change.

## Checks

```
npm run build
npm run lint
npm run format:check
npm run test:format
npm run test:ui
node scripts/smoke-local.cjs
```

The browser suite uses the installed Chrome Chromium engine; it never installs a browser. `UI_BASE_URL` changes its target (default preview 4173; smoke default 8000). `PLAYWRIGHT_MODULE` optionally selects an already installed Playwright module. The suite uses only synthetic accounts and makes a real confirmed demo transfer plus an intentionally rejected substitution. Empty audit, expiry, cold-start and error states use explicitly documented browser response fixtures, never production stubs.

## Design system

`src/ui/` contains shared controls, badges, cards, tabs, native modal dialogs with focus management, tooltips, toast, skeleton, empty/error states, spinner, redacted JSON copy, stat tiles, table regions, key/value rows and payment steps. `tailwind.config.ts` maps CSS semantic variables for Tailwind 4; `src/styles.css` defines both themes and responsive layout. Theme preference is the only localStorage value, guarded by try/catch. Authentication and integrity tags are never rendered, copied or persisted.

`docs/ui-audit.md` records the original issues. `DECISIONS.md` records the design choices and suggested backend changes. `docs/ui-verification.json` contains measurements and full screenshot manifest. Do not interpret evaluation-derived containment or browser round-trip latency as live ledger/server metrics.
