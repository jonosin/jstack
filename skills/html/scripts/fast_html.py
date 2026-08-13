#!/usr/bin/env python3
"""fast_html.py — deterministic JSON/Markdown-ish blocks -> branded single-file HTML, PDF, or PNG.

No pip deps. Input is JSON so agents can fill a stable shape instead of rewriting layout.
"""
from __future__ import annotations

import argparse, html, json, os, re, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path
from typing import NoReturn

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATE = SKILL / "assets" / "base-template.html"
CSS = SKILL / "assets" / "tokens.css"
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
    shutil.which("chrome") or "",
]

EX_USAGE, EX_INPUT, EX_CHROME, EX_RENDER = 2, 4, 5, 6


def die(code: int, msg: str) -> NoReturn:
    print(f"fast_html: {msg}", file=sys.stderr)
    sys.exit(code)


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return s or "doc"


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if c and os.path.exists(c):
            return c
    die(EX_CHROME, "no Chrome/Chromium/Brave/Edge found for PDF/PNG render")


def inline_md(text: str) -> str:
    s = esc(text)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def paragraphs(text: str) -> str:
    return "\n".join(f"<p>{inline_md(p.strip())}</p>" for p in str(text).split("\n\n") if p.strip())


def render_list(items, ordered=False) -> str:
    tag = "ol" if ordered else "ul"
    return f"<{tag}>" + "".join(f"<li>{inline_md(str(i))}</li>" for i in items) + f"</{tag}>"


def render_table(rows) -> str:
    if not rows:
        return ""
    if isinstance(rows[0], dict):
        keys = list(rows[0].keys())
        head = "".join(f"<th>{esc(k)}</th>" for k in keys)
        body = "".join("<tr>" + "".join(f"<td>{inline_md(row.get(k,''))}</td>" for k in keys) + "</tr>" for row in rows)
    else:
        keys = rows[0]
        head = "".join(f"<th>{esc(k)}</th>" for k in keys)
        body = "".join("<tr>" + "".join(f"<td>{inline_md(c)}</td>" for c in row) + "</tr>" for row in rows[1:])
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def render_card(card, klass="card") -> str:
    parts = []
    if card.get("kicker"): parts.append(f"<div class='kicker'>{esc(card['kicker'])}</div>")
    if card.get("title"): parts.append(f"<h3>{esc(card['title'])}</h3>")
    if card.get("metric"): parts.append(f"<div class='metric'>{esc(card['metric'])}</div>")
    if card.get("metric_label"): parts.append(f"<div class='metric-label'>{esc(card['metric_label'])}</div>")
    if card.get("text"): parts.append(paragraphs(card["text"]))
    if card.get("items"): parts.append(render_list(card["items"]))
    return f"<article class='{klass}'>{''.join(parts)}</article>"


def render_section(sec) -> str:
    typ = sec.get("type", "text")
    out = ["<section>"]
    if sec.get("kicker"): out.append(f"<div class='kicker'>{esc(sec['kicker'])}</div>")
    if sec.get("title"): out.append(f"<h2>{esc(sec['title'])}</h2>")
    if sec.get("lead"): out.append(f"<p class='lead'>{inline_md(sec['lead'])}</p>")
    if typ == "cards":
        cards = sec.get("cards", [])
        klass = "card third" if len(cards) == 3 else "card"
        out.append("<div class='grid'>" + "".join(render_card(c, klass) for c in cards) + "</div>")
    elif typ == "table":
        out.append(render_table(sec.get("rows", [])))
    elif typ == "quote":
        out.append(f"<div class='quote'>{paragraphs(sec.get('text',''))}</div>")
    elif typ == "callout":
        danger = " danger" if sec.get("tone") == "danger" else ""
        out.append(f"<div class='callout{danger}'>{paragraphs(sec.get('text',''))}</div>")
    else:
        if sec.get("text"): out.append(paragraphs(sec["text"]))
        if sec.get("items"): out.append(render_list(sec["items"], sec.get("ordered", False)))
    out.append("</section>")
    return "\n".join(out)


def build_html(data: dict) -> str:
    tmpl = TEMPLATE.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    meta = "".join(f"<span>{esc(x)}</span>" for x in data.get("meta", []))
    body = "\n".join(render_section(s) for s in data.get("sections", []))
    reps = {
        "{{TITLE}}": esc(data.get("title", "Untitled")),
        "{{EYEBROW}}": esc(data.get("eyebrow", "JSTACK HTML")),
        "{{DEK}}": inline_md(data.get("dek", "")),
        "{{META}}": meta,
        "{{BODY}}": body,
        "{{CSS}}": css,
        "{{DENSITY}}": esc(data.get("density", "normal")),
    }
    for k, v in reps.items(): tmpl = tmpl.replace(k, v)
    return tmpl


def render_pdf(chrome: str, html_path: Path, out: Path):
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer", f"--print-to-pdf={out}", html_path.as_uri()]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    if p.returncode or not out.exists() or out.stat().st_size == 0:
        die(EX_RENDER, f"Chrome PDF render failed: {(p.stderr or p.stdout)[:400]}")


def render_png(chrome: str, html_path: Path, out: Path, size: str):
    profile = out.parent / ("chrome-profile-" + slug(out.stem))
    if out.exists(): out.unlink()
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run", "--no-default-browser-check", "--disable-component-update", "--disable-background-networking", "--force-device-scale-factor=1", "--hide-scrollbars", f"--user-data-dir={profile}", f"--screenshot={out}", f"--window-size={size}", html_path.as_uri()]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    deadline, stable = time.time() + 30, None
    try:
        while time.time() < deadline:
            if out.exists() and out.stat().st_size > 0:
                size_now = out.stat().st_size
                if size_now == stable: break
                stable = size_now
            if proc.poll() is not None and out.exists() and out.stat().st_size > 0: break
            time.sleep(.2)
    finally:
        try: os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception: pass
        shutil.rmtree(profile, ignore_errors=True)
    if not out.exists() or out.stat().st_size == 0:
        die(EX_RENDER, "Chrome PNG render produced no screenshot")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build a deterministic branded HTML doc from JSON.")
    ap.add_argument("input", help="doc JSON")
    ap.add_argument("--out", help="output .html/.pdf/.png path; default from title")
    ap.add_argument("--format", choices=["html", "pdf", "png"], default="html")
    ap.add_argument("--window-size", default="1200,1600", help="PNG viewport, e.g. 1200,1600")
    args = ap.parse_args(argv)
    src = Path(args.input).resolve()
    if not src.exists(): die(EX_INPUT, f"input not found: {src}")
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except Exception as e:
        die(EX_INPUT, f"invalid JSON: {e}")
    html_s = build_html(data)
    out = Path(args.out).resolve() if args.out else src.with_name(slug(data.get("title", src.stem)) + "." + args.format)
    if args.format == "html":
        out.write_text(html_s, encoding="utf-8")
    else:
        chrome = find_chrome()
        with tempfile.TemporaryDirectory() as td:
            hp = Path(td) / "doc.html"
            hp.write_text(html_s, encoding="utf-8")
            if args.format == "pdf": render_pdf(chrome, hp, out)
            else: render_png(chrome, hp, out, args.window_size)
    print(f"Wrote {out} ({out.stat().st_size:,} bytes)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
