---
name: jstack-ggdesign-init
description: DEPRECATED — baked into jstack-init. Design-system (DESIGN.md) initialization now lives in the build path of /jstack-init. Use /jstack-init for new build repos (which can init DESIGN.md deterministically), or run scripts/init_design.py in jstack-init for a standalone design init.
user_invocable: false
---

# jstack-ggdesign-init — DEPRECATED

This skill has been **baked into `jstack-init`**. Do not invoke it.

- New build repo that needs a design system → `/jstack-init` (build path; offers DESIGN.md init).
- Standalone DESIGN.md init in an existing repo →
  `python3 ~/jstack/skills/jstack-init/scripts/init_design.py --repo <path>`.
- Format/lint/export reference moved to `~/jstack/skills/jstack-init/references/design/`.
