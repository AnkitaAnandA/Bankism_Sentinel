# Frontend redesign decisions

1. Audit before implementation: 36 baseline screenshots and `docs/ui-audit.md` were completed before design-system code.
2. Only frontend files change. Keep `services/api.ts` interfaces, route paths, payloads and authentication behavior; no backend changes or security relaxations.
3. Use restrained teal, neutral surfaces, semantic verdict colors and both themes. Persist only theme preference in exception-safe localStorage. Session token stays in API module memory.
4. Self-host Inter and JetBrains Mono variable latin subsets with swap; no font network providers. Lucide SVG icons, CSS motion, no chart/animation dependency. Keep page imports lazy.
5. Money display validates safe integer minor units, converts through BigInt division and formats integer grouping. Never divide monetary amounts into floating-point major units.
6. Customer default is a guided banking demo. Analyst default is the dashboard. Customer nav locks analyst access; analyst views never offer financial confirmation actions.
7. Missing metrics are not invented: dashboard containment is a labeled isolated-evaluation result, not a live ledger total. Browser-measured analyze round trip is explicitly distinct from server latency. Evaluation is user-triggered and avoids automatic quota consumption.
8. Backend account masking is authoritative. Preserve its suffix instead of inventing numeric digits. Registered demo payees are shown as illustrative targets, not a live approved-beneficiary list; backend still approves or rejects every prepare request.
9. Technical JSON copies exclude demo tokens and integrity tags; these values remain in request memory for the existing confirm contract. Never render or persist them.
10. Single-submit refs guard synchronous repeats; disable confirm after expiry. An execute retry reuses the same idempotency key and immutable intent after a transport failure, so uncertain responses do not produce a second payment.
11. Browser fixtures are isolated test response intercepts for empty audit, cold start, errors and expiry. Actual backend exercises verify financial flows. No fixture is bundled into the app.

## Suggested backend changes

- Add a read-only approved-beneficiary endpoint with server-masked account IDs, so the UI can render the authenticated user's authoritative roster.
- Add audited unauthorized-execution totals and analyzed-request latency aggregates to analyst metrics; current verdict counters cannot substantiate either claim.
- Use numeric display suffixes for seeded masked account fields. The existing synthetic IDs end in letters, which the UI must not misrepresent.
- Add an authenticated intent-status/receipt lookup for recovery after an uncertain network response. The existing guard rejects replay safely but does not return the original receipt on idempotent retry; the frontend must not infer a successful execution from a replay denial.

These suggestions are not implemented in the backend.
