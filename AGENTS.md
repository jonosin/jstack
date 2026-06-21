# jstack — Agent Contract (the jstack skill suite)

This repo is the **canonical home of the venture-agnostic `jstack-*` skills** — the composable
agent skills that shape how an agent talks, hands off sessions, captures knowledge, drafts
messages, scaffolds/tunes other skills, and analyzes media. Each `skills/<name>/` dir is the
single source of truth; every harness (`.agents`, `.claude`, `.codex`, `.hermes/skills/jstack`)
**symlinks straight back here** — there is no second forked copy. Edit the file in this repo and
every harness sees it.

**You (the agent) work in this repo to author and improve skills.** A human curates and installs
them. This is where you come to *create*, *skillify*, or *skilltune* a `jstack-*` skill — keep that
work here, not in `~/second-brain` (knowledge) or `~/jstack-sf` (the StayFrame venture).

> **Shareable repo — keep it clean.** This repo is meant to be shared. It must contain **no personal
> identity, no absolute machine paths (`/Users/...`), no project codenames, no API keys.** Use
> home-relative `~/...` paths only. Personal values live in `~/.jstack/config.env` (gitignored) and
> are read at runtime via **env var → `~/.jstack/config.env` → built-in default**. `tools/secrets-gate.sh`
> enforces this and **must pass before every push** (see §Before pushing).

---

## 1. Read order (progressive disclosure — don't read the whole repo)

1. **`AGENTS.md`** (this file) — orientation + how to behave here.
2. **`README.md`** — the human-facing catalog: every skill, its job, and its extra setup.
3. **`skills/jstack/SKILL.md`** — the **authoring convention** (naming, scaffolder, symlink layout,
   the required `## Next skills` table, adapting external skills). Read before creating any skill.
4. **The target `skills/<name>/SKILL.md`** — read the skill you're about to improve before touching it.
5. **`.env.example`** — the full list of config keys and their resolution order.

Token discipline: open only the skill you're working on. Don't read sibling skills you don't need.

---

## 2. The work you do here — author & improve `jstack-*` skills

Four operations, each owned by a skill. Pick by intent:

| Intent | Operation | Drive with |
|--------|-----------|------------|
| **New skill** from scratch or from a successful interactive session | Scaffold → author | `skills/jstack/scripts/new-jstack-skill.sh <name> --desc "…"`, then `skill-creator` to write the `SKILL.md` body |
| **Codify** a working session into a new deterministic skill, or **harden** a fuzzy skill into scripts | Skillify (eval-gated) | `/jstack-skillify` |
| **Tune** an existing skill's accuracy/efficiency against an eval set | Skilltune (metric-driven loop) | `/jstack-skilltune <name>` |
| **Restructure / audit** an existing `SKILL.md` against the AgentSkills spec | Author | `skill-creator` |

**Naming convention (authoritative copy: `skills/jstack/SKILL.md`):**
- `jstack-<skill>` — daily, venture-agnostic → **lives here**.
- `jstack-<venture-code>-<skill>` — venture-specific (e.g. `jstack-sf-*` = StayFrame) → **does NOT
  live here**; it lives in that venture's own repo (see §4). Never use a colon in a skill dir name.

**Never hand-create skill dirs or symlinks.** Run the scaffolder — it creates the canonical dir +
starter `SKILL.md` and symlinks it (direct to this repo) into every installed harness. It is
idempotent: re-running repairs/retargets symlinks without touching the `SKILL.md` body.

**Every skill ends with a `## Next skills` table** — the recommended next hop(s). Any workflow step
that reaches "generate a video/clip" routes through `/jstack-vidgen`, never a backend directly.

---

## 3. Where things live

```
jstack/
  AGENTS.md             # this contract        CLAUDE.md → @AGENTS.md
  README.md             # human-facing skill catalog + setup
  .env.example          # all config keys (copy → ~/.jstack/config.env)
  skills/               # the canonical jstack-* skills (symlinked into every harness)
    jstack/             #   the authoring convention + scaffolder (new-jstack-skill.sh)
    jstack-setup/       #   installs the suite + writes config
    …                   #   one dir per skill — the single source of truth
  vendor/               # bundled helpers (e.g. gemini-vision `gv` wrapper for jstack-vision)
  tools/secrets-gate.sh # pre-push scan for identity/paths/keys — RUN BEFORE EVERY PUSH
```

---

## 4. Routing — what belongs where (don't crowd this repo)

| If you're working on… | Go to | Why |
|---|---|---|
| A **venture-agnostic** `jstack-*` skill (voice, handoff, savetobrain, vision, skillify, skilltune, …) | **here** (`~/jstack/skills/`) | This is their canonical home. |
| A **StayFrame** (`jstack-sf-*`) skill, its craft canon, or its toolkit | **`~/jstack-sf`** (private venture repo, its own `AGENTS.md`) | Venture skills + IP live with the venture, not in the shareable suite. Start at `~/jstack-sf/skills/jstack-sf/SKILL.md` (the router) and obey `~/jstack-sf/playbook/`. |
| **Knowledge** — a durable fact, decision, research synthesis, or "save this" | **`~/second-brain`** via `/jstack-savetobrain` | The brain stores knowledge; this repo stores skills. Never write the brain's `wiki/` from here. |
| A **product / app / internal build** | **`~/builds/<project>`** (or `~/.hermes/` for Hermes-native skills) | Code for products doesn't belong in the skill suite. |

Rule of thumb: **this repo = generic reusable skills.** Anything venture-specific, knowledge, or a
shippable product belongs in one of the repos above.

---

## 5. Binding conventions (all agents)

- **Skills follow the AgentSkills format** — a `SKILL.md` with YAML frontmatter (`name`, `description`),
  so they load in any harness. Author/restructure with `skill-creator`.
- **Config resolution is always** env var → `~/.jstack/config.env` → built-in default. Never hardcode a
  personal value into a committed skill.
- **`## Next skills` table is required** on every skill (see §2).
- **Eval-gate behavior changes.** `/jstack-skillify` and `/jstack-skilltune` are eval-gated so a skill's
  behavior can't silently regress — don't bypass the eval to force a green result.
- **Cite paths home-relative** (`~/jstack/skills/<name>/SKILL.md`), never absolute machine paths.

---

## 6. Before pushing

The repo is shareable. **Before any `git push`, run `bash tools/secrets-gate.sh` from the repo root.**
It scans tracked + untracked files for personal identity, machine paths, GCP project ids, and key
patterns, and exits non-zero on a hit. If it fails, move the offending value into
`~/.jstack/config.env` and genericize the file — never commit the secret.
