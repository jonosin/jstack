# Session transcript — API pagination

User: The `GET /api/users` endpoint returns all users in one response. With 40k users it's slow and huge. Add pagination.

Assistant: Found it: `src/server/routes/users.ts`, handler `listUsers`. It does `SELECT * FROM users ORDER BY created_at DESC` via `src/server/db/users.ts#getAllUsers()` and returns the full array as JSON. The client that consumes it is `src/client/api/users.ts#fetchUsers()`.

User: What pagination style?

Assistant: Recommended cursor-based (keyset) pagination on `created_at, id` rather than OFFSET — stable under inserts and fast at depth. The response shape would become `{ data: User[], nextCursor: string | null }`. Page size default 50, max 200 via a `?limit=` query param, cursor via `?cursor=`. Discussed but not implemented: the SQL needs a `WHERE (created_at, id) < (:cursorTs, :cursorId)` clause and `LIMIT :limit+1` to compute `nextCursor`.

User: Implement it and prove it works.

Assistant: Understood. The bar: `GET /api/users?limit=50` returns at most 50 records plus a `nextCursor`; following the cursor returns the next page with no overlap and no gaps; an integration test walks all pages and reconstructs the full set exactly once.
