---
name: ggdesign-init
description: DEPRECATED — do not invoke. Use when you would otherwise reach for ggdesign-init to initialize a design system (DESIGN.md); that trigger now routes to /init instead. New build repo needing a design system → /init (build path, can init DESIGN.md deterministically). Standalone DESIGN.md init in an existing repo → run scripts/init_design.py in init.
user_invocable: false
---

# ggdesign-init — DEPRECATED

This skill has been **baked into `init`**. Do not invoke it.

- New build repo that needs a design system → `/init` (build path; offers DESIGN.md init).
- Standalone DESIGN.md init in an existing repo →
  `python3 ~/jstack/skills/init/scripts/init_design.py --repo <path>`.
- Format/lint/export reference moved to `~/jstack/skills/init/references/design/`.

## Next skills

| Next | When |
|------|------|
| `/init` | Always — this stub exists only to redirect here (build path, or standalone `init_design.py`). |
