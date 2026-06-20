# Session transcript — analytics dashboard

User: I'm building an analytics dashboard. Today we wired up the chart components and the data-fetch hooks.

Assistant: Right. The dashboard is `src/pages/Dashboard.tsx`. Charts use Recharts, wrapped in `src/components/charts/`. Data comes from `useMetrics()` in `src/hooks/useMetrics.ts`, which hits `GET /api/metrics`. The API handler is `src/server/routes/metrics.ts` and reads from the `events` table via `src/server/db/queries.ts`.

User: The charts render correctly now and the date-range filter works. We also added a loading skeleton and an empty state.

Assistant: Confirmed — all three chart types (line, bar, donut) render with live data, the range picker re-fetches, and the skeleton/empty states are in. The `events` table schema is in `src/server/db/schema.sql`.

User: Tomorrow I want users to be able to export the current view as CSV.

Assistant: Understood — CSV export of the currently-filtered metrics view is the next piece. There's no export code yet. The data we'd export is whatever `useMetrics()` currently holds for the active date range.
