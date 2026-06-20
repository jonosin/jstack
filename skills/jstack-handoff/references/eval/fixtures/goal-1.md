# Session transcript — failing build

User: The `web` package build is broken and the test suite is red. I need it green and lint-clean.

Assistant: Inspected `packages/web`. `npm run build` fails with 6 TypeScript errors — mostly `Property does not exist` after a recent refactor of the `User` type in `packages/web/src/types/user.ts` (renamed `fullName` → `displayName`, callers not updated). `npm test` (Vitest) shows 4 failing tests, 2 of them downstream of the same rename, 2 a changed date-format helper in `src/utils/date.ts`.

User: So what's the plan?

Assistant: 1) Update all `fullName` references to `displayName` (grep shows 9 call sites across components + 1 test). 2) Fix the date helper tests — the helper now returns ISO not locale; tests assert the old format, decide which is correct (the helper change looks intentional). 3) Re-run `npm run build`, `npm test`, `npm run lint`. Lint currently has 3 `no-unused-vars` warnings in `src/legacy/`.

User: Right — I want all of that done. Build passing, all tests green, lint zero warnings.

Assistant: Acknowledged. The success bar: `npm run build` exits 0, `npm test` reports 0 failures, `npm run lint` reports 0 errors/warnings — all from `packages/web`.
