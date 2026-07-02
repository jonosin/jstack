"""Mermaid text -> auto-laid-out .excalidraw JSON.

Authors a diagram in Mermaid (LLMs write this well), runs Mermaid's dagre auto-layout via
@excalidraw/mermaid-to-excalidraw inside headless Chromium, and writes a standard .excalidraw
file. Feed the result to render_excalidraw.py to get a PNG.

This kills the manual-coordinate-math problem: you never hand-place boxes/arrows — the layout
engine does it. Styling is Mermaid-plain; use the skill's methodology + color-palette.md for polish,
or post-edit the emitted JSON.

Usage:
    cd .claude/skills/excalidraw-diagram/references
    uv run python mermaid_to_excalidraw.py <input.mmd> [--output out.excalidraw] [--font-size 20]
    # or pipe:  echo "flowchart TD; A-->B" | uv run python mermaid_to_excalidraw.py - -o out.excalidraw

Needs network at run time (imports the pinned libs from esm.sh, same as the renderer).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Pinned to match render_template.html. mermaid-to-excalidraw is also installed in node_modules
# (see package.json) as the version-of-record; we load it in-page via esm.sh because Mermaid needs a DOM.
# Plain esm.sh (NOT ?bundle): bundling this pkg 404s on Mermaid's chunked sub-imports.
MERMAID_LIB = "https://esm.sh/@excalidraw/mermaid-to-excalidraw@2.2.2"
EXCALIDRAW_LIB = "https://esm.sh/@excalidraw/excalidraw@0.18.0?bundle&target=es2020"

PAGE_TEMPLATE = """<!DOCTYPE html><html><head><meta charset="utf-8"/></head><body>
<script type="module">
  import {{ parseMermaidToExcalidraw }} from "{mermaid_lib}";
  import {{ convertToExcalidrawElements }} from "{excalidraw_lib}";
  window.__convert = async function(mermaidText, fontSize) {{
    try {{
      const {{ elements, files }} = await parseMermaidToExcalidraw(mermaidText, {{
        themeVariables: {{ fontSize: String(fontSize) + "px" }},
      }});
      const full = convertToExcalidrawElements(elements);
      return {{ success: true, elements: full, files: files || {{}} }};
    }} catch (err) {{
      return {{ success: false, error: String(err && err.message || err) }};
    }}
  }};
  window.__ready = true;
</script></body></html>"""


def convert(mermaid_text: str, font_size: int = 20) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. Run: uv sync && uv run playwright install chromium", file=sys.stderr)
        sys.exit(1)

    html = PAGE_TEMPLATE.format(
        mermaid_lib=MERMAID_LIB, excalidraw_lib=EXCALIDRAW_LIB
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        errors: list[str] = []
        page.on("requestfailed", lambda r: errors.append(r.url))
        page.set_content(html)
        try:
            page.wait_for_function("window.__ready === true", timeout=45000)
        except Exception:
            browser.close()
            hint = f" (failed requests: {errors[:3]})" if errors else ""
            print(f"ERROR: mermaid/excalidraw modules failed to load from esm.sh{hint}", file=sys.stderr)
            sys.exit(1)
        result = page.evaluate("([t,f]) => window.__convert(t,f)", [mermaid_text, font_size])
        browser.close()

    if not result or not result.get("success"):
        msg = result.get("error", "unknown") if result else "convert returned null"
        print(f"ERROR: Mermaid parse failed: {msg}", file=sys.stderr)
        sys.exit(1)

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "mermaid_to_excalidraw.py",
        "elements": result["elements"],
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
        "files": result.get("files", {}),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Mermaid text -> .excalidraw JSON (auto-layout)")
    ap.add_argument("input", type=str, help="Path to a Mermaid (.mmd) file, or '-' for stdin")
    ap.add_argument("--output", "-o", type=Path, default=None, help="Output .excalidraw path")
    ap.add_argument("--font-size", type=int, default=20, help="Base font size in px (default: 20)")
    args = ap.parse_args()

    if args.input == "-":
        mermaid_text = sys.stdin.read()
    else:
        ip = Path(args.input)
        if not ip.exists():
            print(f"ERROR: File not found: {ip}", file=sys.stderr)
            sys.exit(1)
        mermaid_text = ip.read_text(encoding="utf-8")

    if not mermaid_text.strip():
        print("ERROR: empty Mermaid input", file=sys.stderr)
        sys.exit(1)

    scene = convert(mermaid_text, args.font_size)

    out = args.output
    if out is None:
        out = Path(args.input).with_suffix(".excalidraw") if args.input != "-" else Path("diagram.excalidraw")
    out.write_text(json.dumps(scene, indent=2), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
