# Session transcript — Docker image slimming

User: Our production Docker image is 1.2GB. I want it under 200MB.

Assistant: Looked at `Dockerfile` at the repo root. It's a single-stage build `FROM node:20` (the full image, ~1GB base), copies the whole repo including `.git`, dev dependencies, and the `tests/` dir, and runs `npm install` (not `--production`). The app is a compiled Node service; the build output is `dist/`.

User: What would shrink it?

Assistant: Several levers identified: (1) multi-stage build — compile in a builder stage, copy only `dist/` + production `node_modules` into a slim runtime stage. (2) `FROM node:20-slim` or `node:20-alpine` for the runtime stage (alpine base ~50MB). (3) `npm ci --omit=dev` in the runtime stage. (4) a `.dockerignore` excluding `.git`, `tests`, `*.md`, `node_modules`. We sketched the multi-stage Dockerfile but didn't finalize or measure.

User: I want the image under 200MB, verified by `docker images`.

Assistant: Got it. The measurable bar: after `docker build -t web:slim .`, `docker images web:slim` shows a size under 200MB, and the container still starts and serves `GET /health` returning 200.
