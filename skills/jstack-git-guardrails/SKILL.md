---
name: jstack-git-guardrails
description: "Install a PreToolUse hook that mechanically blocks destructive git commands (push, reset --hard, clean -f, branch -D, checkout .) before they execute. Use when setting up git safety guardrails, 'protect my repo from destructive git', or after any near-miss with a destructive git command."
---

# jstack-git-guardrails

A one-time-setup skill. It packages a small, deterministic Claude Code hook that
mechanically blocks a short list of destructive git commands before they run —
turning "the agent should be careful with git" from a prompt-level instruction
into a mechanical control the agent cannot talk its way past.

Adapted from mattpocock/skills (git-guardrails). Not a copy: the upstream script
blocks plain `git push` outright; this version does not (see rationale below).

## What the hook blocks

| Pattern | Why blocked |
|---|---|
| `git push --force` / `git push -f` | Force-push can silently overwrite remote history other people or CI depend on — the single most common way an agent destroys shared work. |
| `git reset --hard` | Discards uncommitted work and unstaged changes with no undo path from inside the session. |
| `git clean -f` / `git clean -fd` (any `-f`-bearing clean) | Permanently deletes untracked files — no trash, no recovery. |
| `git branch -D` | Force-deletes a branch even if it has unmerged commits, silently dropping history. |
| `git checkout .` / `git restore .` | Wholesale-discards working-tree edits across the repo, not a targeted file. |

**Plain `git push` is intentionally NOT blocked.** Pushing to a remote branch is a
normal, user-directed operation throughout this suite (most jstack workflows end
with "commit and push a feature branch for a Vercel preview"). Blocking it would
make the guardrail a nuisance that gets disabled rather than trusted. Only the
force-push variants — the ones that actually rewrite history — are blocked.

## How it works

`scripts/git-guardrails-hook.sh` is a Claude Code `PreToolUse` hook. On every
`Bash` tool call, Claude Code pipes the tool-call JSON to the hook's stdin. The
hook reads `.tool_input.command` with `jq`, checks it against the patterns above,
and:

- **matches a blocked pattern** → prints `git-guardrails: blocked destructive
  command (<reason>). Run it manually if truly intended.` to stderr and exits
  `2` — Claude Code treats exit code 2 as "block this tool call."
- **anything else** (including empty/missing command) → exits `0`, the command
  runs normally.

The hook is intentionally dumb: no LLM call, no state, just a grep chain. That's
what makes it a real guardrail rather than an instruction the agent can reason
its way around.

## Install

1. Copy the script to a stable location outside any single project so it survives
   repo switches:

   ```bash
   mkdir -p ~/.jstack/hooks
   cp ~/jstack/skills/jstack-git-guardrails/scripts/git-guardrails-hook.sh ~/.jstack/hooks/
   chmod +x ~/.jstack/hooks/git-guardrails-hook.sh
   ```

2. Register it as a `PreToolUse` hook with a `Bash` matcher in the harness
   settings file (`~/.claude/settings.json` for a global, all-projects install;
   or `.claude/settings.json` at a project root for that project only). Merge
   this into the existing `hooks.PreToolUse` array — don't overwrite other hooks:

   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Bash",
           "hooks": [
             {
               "type": "command",
               "command": "~/.jstack/hooks/git-guardrails-hook.sh"
             }
           ]
         }
       ]
     }
   }
   ```

   For a project-scoped install, point `command` at
   `"$CLAUDE_PROJECT_DIR"/.claude/hooks/git-guardrails-hook.sh` and copy the
   script there instead of `~/.jstack/hooks/`.

This skill documents the install — it does not perform it. Run the steps above
yourself (or have an agent run them) when you're ready to turn the guardrail on.

## Verify

In a disposable scratch repo (never your real one — this is a live test of a
tool-blocking hook):

```bash
mkdir -p /tmp/git-guardrails-scratch && cd /tmp/git-guardrails-scratch && git init -q
echo hello > file.txt && git add file.txt && git commit -q -m "seed"
```

Then, with the hook installed and a fresh Claude Code session in that directory,
ask it to run `git reset --hard`. Expect the tool call to be blocked and the
message `git-guardrails: blocked destructive command (reset --hard). Run it
manually if truly intended.` to appear. A benign command (`git status`, `git
push` with no flags) should run normally.

You can also test the script directly, without a live session, by feeding it the
same JSON shape Claude Code sends on stdin:

```bash
echo '{"tool_input":{"command":"git reset --hard"}}' | ~/.jstack/hooks/git-guardrails-hook.sh
echo "exit=$?"
# → prints the block message to stderr, exit=2
```

## Uninstall

Remove the hook entry from the `hooks.PreToolUse` array in whichever settings
file you added it to, then delete the copied script:

```bash
rm ~/.jstack/hooks/git-guardrails-hook.sh   # or the project .claude/hooks/ copy
```

## Next skills

| Next | When |
|------|------|
| `/jstack` | Standalone one-time setup — jstack's setup routine is the natural place to check "is the git guardrail installed?" alongside other suite-wide config. |

Otherwise standalone — no required next step once installed.
