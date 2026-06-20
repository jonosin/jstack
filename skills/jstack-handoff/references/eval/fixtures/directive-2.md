# Session transcript — auth flow

User: We just finished refactoring the auth flow. Walk-through done.

Assistant: Summary of where auth stands: login is `POST /api/auth/login` in `src/server/routes/auth.ts`. It verifies the password (argon2) via `src/server/auth/password.ts`, issues a short-lived access JWT and a refresh token stored in the `sessions` table. Refresh is `POST /api/auth/refresh`; logout is `POST /api/auth/logout` (revokes the session row). Middleware `requireAuth` in `src/server/middleware/requireAuth.ts` validates the access token.

User: All the manual happy-path testing passed. Token rotation works, logout revokes correctly.

Assistant: Good. The refresh-token rotation (old token invalidated on use) is implemented and was manually verified. Argon2 params are in `src/server/auth/password.ts` (memory 64MB, time cost 3).

User: Next session: write integration tests for the whole auth flow — login, refresh, logout, and the expired/invalid token cases.

Assistant: Clear. No automated tests exist for auth yet; the test harness is Vitest + Supertest, and there's a test DB helper at `src/server/test/db.ts` that spins up a clean schema per suite.
