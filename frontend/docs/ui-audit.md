# Bankism Sentinel UI audit — before redesign

Captured before design implementation on 11 October 2026. 36 full-page images in `screenshots/before/` cover 12 states at 1440×900, 1024×768 and 390×844. Real requests exercised balance, prepare/confirm/execute, BLOCK, clarification, analyst audit and evaluation. Empty audit, cold start and connection failure used browser-only response fixtures, explicitly labeled in filenames; no backend code or records were changed to simulate them. Installed Chrome supplies the Chromium engine; no browser installation was performed.

## Visual hierarchy
- Bank: headline is oversized relative to useful controls, balances consume an entire row, and the empty verdict card takes a third of the screen. Replace with a compact guided introduction, primary chat column and account rail.
- Payment review is below chat AND transaction history at 390px, around 1,200px down the page. Place the review immediately after the request, before history; scroll to newly created review without moving an established reading position.
- Dashboard: all four counters receive equal prominence; financial containment is absent. Add explicitly sourced evaluation containment and latency summaries, never invented production metrics.

## Spacing and alignment
- Empty chat occupies 580px on desktop with small controls centered inside a large blank area. Use purposeful prompt cards and tighter section spacing.
- Dense event rows and long evidence generate a 2,600px dashboard at 1024px. Constrain previews, add inspectable event details and filtering, keep pagination.
- Account, chat and verdict headings use different inset sizes. Apply 4px spacing tokens and reusable card headers.

## Typography
- Serif marketing headline conflicts with the security-console content. Use self-hosted variable sans throughout; mono only for payloads and identifiers.
- Many secondary labels/captions are approximately 9–11px, difficult on mobile. Set body 14–16px and readable 12px minimum captions.
- Masked identifiers show suffixes such as 'King'/'Ings' from synthetic account IDs. Preserve authoritative server masking; normalize the bullet prefix, never fabricate numeric account digits.

## Color and contrast
- Muted teal, tiny pale captions and subtle borders are low contrast. Introduce semantic foreground/surface/border tokens and verify actual computed contrast.
- Dark sidebar/light content is fixed; no dark preference. Add complete light/dark themes with a persisted, exception-safe toggle.
- Verdict colors are inconsistent between chat, result and event table. One shared badge palette must communicate via text and icon as well as color.

## Inconsistent components
- Unicode symbols and arrow glyphs substitute for icons and vary in weight and baseline. Use one lucide set with hidden decorative SVGs and named icon-only buttons.
- All buttons look alike except confirmation; no unified loading, danger or focus states. Build shared primitives first.
- Repeated empty/loading/error layouts lack consistent icon, explanation and action structure. Use reusable states, toast and skeleton patterns.

## Confusing flows
- Customers can navigate to an analyst page and only then learn it is unavailable. Lock that nav item with a clear accessible explanation; redirect after changing roles.
- Analyst can open banking controls for an identity without customer accounts. Remove transaction actions for analyst sessions.
- Balance reply says 'Authorized read-only request' but displays no balance in the chat. Render returned read-only information directly beside the verdict.
- Transfer has no progress steps, remaining-time countdown, receipt ID or obvious next action. Add guided review, countdown, guarded single submission and execution receipt.
- Clarification asks for details in text but offers no quick reply. Add amount suggestions for the original named payee, then re-prepare through the unchanged API.
- Attack lab treats all text presets as equivalent even though replay/outage require state. Group presets and retain explicit explanation of stateful evaluation.
- Lock OFF label could imply the application's guard is disabled. Describe comparison mode as 'Unsafe baseline sandbox', while continuously stating actual guard remains enabled.

## Missing states
- Busy chat lacks analysis status; failed submission loses the local request draft. Show pending/error turn states and preserve retry text.
- Empty event table has no header or structured next step. Use informative empty state.
- Cold start is static text; error message is visually abrupt and has no status dot. Give both stable-height, accessible, recoverable connection cards.
- Payment success still looks like a proposal, and terminal states can incorrectly appear expired later. Prioritize terminal status over countdown.

## Mobile layout
- Large top navigation consumes 180px before content; customer actions are buried. Replace with compact header and persistent labeled bottom navigation.
- Both balance cards squeeze side-by-side at 390px. Collapse account information above chat with expandable account details.
- Review and JSON must fit the viewport; tables may scroll within their own region, never horizontally move the page.

## Accessibility
- No skip link, semantic chat log, Enter-send shortcut or screen-reader analysis status. Add these and respect reduced-motion preferences.
- Role select label does not clearly distinguish persona from privilege. Name it 'Acting as' and show role in option text.
- Technical results are always expanded and 'none' is used as a threat headline. Lead with human explanation, expand optional diagnostics, provide redacted copyable JSON.
- Expiry and busy states must actually disable controls; race protection needs a synchronous ref latch, not only React's queued state update.

## Scope decisions
Only `frontend/` will change, including this documentation and verification scripts. Existing API paths, schemas and auth contracts stay intact. Beneficiary roster, live unauthorized-transfer count and server analyze latency are absent from current schemas. Display configured demonstration targets as examples (not an approved roster), and label measured browser round-trip latency and evaluation-derived containment with their scope. Suggested backend additions will be recorded in `frontend/DECISIONS.md`.
