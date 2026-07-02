---
name: jstack-ggdesign-init
description: DEPRECATED — do not invoke. Use when you would otherwise reach for jstack-ggdesign-init to initialize a design system (DESIGN.md); that trigger now routes to /jstack-init instead. New build repo needing a design system → /jstack-init (build path, can init DESIGN.md deterministically). Standalone DESIGN.md init in an existing repo → run scripts/init_design.py in jstack-init.
user_invocable: false
---

# jstack-ggdesign-init — DEPRECATED

This skill has been **baked into `jstack-init`**. Do not invoke it.

- New build repo that needs a design system → `/jstack-init` (build path; offers DESIGN.md init).
- Standalone DESIGN.md init in an existing repo →
  `python3 ~/jstack/skills/jstack-init/scripts/init_design.py --repo <path>`.
- Format/lint/export reference moved to `~/jstack/skills/jstack-init/references/design/`.

## Next skills

| Next | When |
|------|------|
| `/jstack-init` | Always — this stub exists only to redirect here (build path, or standalone `init_design.py`). |
