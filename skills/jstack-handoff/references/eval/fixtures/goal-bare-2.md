# Session transcript — memory leak

User: Our websocket gateway service leaks memory — RSS climbs ~50MB/hour under steady load until the pod OOMs and restarts.

Assistant: Investigated `services/ws-gateway`. The entry is `services/ws-gateway/src/index.ts`. It tracks connected clients in a module-level `Map<string, Client>` called `clients`. On connect it adds; on the socket `close` event it's supposed to delete. I see the `close` handler, but it keys deletion by `socket.id` while insertion keys by `client.sessionId` — so disconnected clients are never removed. The Map grows unbounded.

Assistant: Also each `Client` holds a `setInterval` heartbeat that is never cleared on disconnect, so timers accumulate too — a second leak compounding the first.

User: Confirm and fix it.

Assistant: The leak is confirmed by the key mismatch (insert by `sessionId`, delete by `socket.id`) plus the uncleared heartbeat intervals. The fix is to key both insert and delete consistently by `sessionId` and `clearInterval` in the close handler. To prove it: a soak test that opens and closes 10k connections should leave `clients.size === 0` and RSS flat (±5MB) afterward.

User: Do it and verify RSS stays flat. I'll leave the exact threshold to you.

Assistant: Clear — fix both leaks, then a soak test proving `clients.size` returns to 0 and RSS is stable after 10k connect/disconnect cycles.
