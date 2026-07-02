# Research shortlist

Ranked prior art used to design `jstack-html`.

| Rank | Repo / tool | What it gives us | Fit | License |
|---|---|---|---|---|
| 1 | `yz671/viewllm` | Single-binary viewer for LLM-generated HTML artifacts. Confirms the core pattern: agents should emit portable HTML artifacts, not spin up apps for quick views. | Strong conceptual fit for agent output viewing; not a template system. | MIT |
| 2 | `EvotecIT/PSWriteHTML` | Data-to-HTML report generation with declarative sections and no hand-written HTML for every report. | Strong evidence that deterministic report DSLs beat ad-hoc markup; PowerShell-specific, so we borrow the idea only. | MIT |
| 3 | `datavzrd/datavzrd` | CSV/TSV to visual HTML reports from config. | Good pattern for schema-driven, repeatable data pages. Too specialized for general agent docs. | MIT |
| 4 | `pytest-dev/pytest-html` | Single-purpose HTML report generation with stable structure and assets. | Useful report-shape precedent; not suitable as the base for arbitrary docs. | Other |
| 5 | `anyblades/blades` / Pico-style CSS | Lightweight classless/minimal CSS for no-build pages. | Good fallback pattern, but Jono needs on-brand deterministic docs, so this skill bundles its own tokens instead of depending on a CDN. | MIT |
| 6 | Headless Chrome CLI render pattern | Chrome `--print-to-pdf` and `--screenshot` make HTML export deterministic locally. | Best fit for PDF/PNG deliverables. We reuse the local patterns from `~/jstack-sf/tools/invoice.py` and `jstack-sf-caption`. | Chrome binary external |

Local prior art reused:

- `~/ventures/stayframe/clients/serenity-sands/athar-onepager-site/index.html`: editorial one-pager structure, serif/mono tokens, restrained luxury palette, max-width mobile canvas.
- `~/jstack-sf/tools/invoice.py`: JSON/data -> HTML string -> headless Chrome PDF.
- `~/jstack-sf/skills/jstack-sf-caption/scripts/caption.py`: robust Chrome screenshot path with isolated user-data-dir, `--default-background-color=00000000`, and output stabilization polling.
