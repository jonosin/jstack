#!/usr/bin/env python3
"""veo_gen — generic Veo 3.1 video generation via Vertex AI.

Wraps the google-genai SDK (vertexai=True) for Veo video generation, mirroring
the CLI shape of jstack-imgen's `gi`. General-purpose: prompt + files come from
the caller.

STATUS: live. The i2v/t2v submit path (generate(), below) is implemented and
working — real client.models.generate_videos(...), polls the long-running op to
completion (15-min ceiling), saves the mp4. `--dry-run` validates resolved config
+ billing project + cost estimate and prints the invocation WITHOUT calling the
API (spends nothing) — use it to verify before the first real submit. Veo model
ids rotate (`-preview` -> `-001`); if a run 404s, confirm the id + allowed
durations in Model Garden and pin via GEMINI_VIDGEN_MODEL.

Usage:
  veo_gen.py --prompt "..." --first-frame still.png -o out.mp4
  veo_gen.py --prompt "..." --duration 8 --resolution 1080p --aspect-ratio 9:16
  veo_gen.py --dry-run --json --prompt "..." --first-frame still.png

Agent-native flags (parsed by veo_gen, not forwarded):
  --json            emit a structured JSON envelope instead of raw text
  --dry-run         print resolved config + billing project; do not call (no billing)
  -h, --help        print this usage and exit
  --version         print veo_gen version and exit

Exit codes (typed, mirrors gi):
  0   ok
  2   usage error (missing/invalid args or flags)
  3   config error (no GCP project set)
  4   auth / billing error
  5   model unreachable (404 / INVALID_ARGUMENT)
  6   input / file error
  7   dependency missing (google-genai not installed)
  10  unknown upstream failure

Config: project comes from GEMINI_VIDGEN_PROJECT, GOOGLE_CLOUD_PROJECT, or
~/.jstack/config.env. Env var -> ~/.jstack/config.env -> default.

Env overrides:
  GEMINI_VIDGEN_MODEL     model id (default: veo-3.1-generate-001)
  GEMINI_VIDGEN_PROJECT   GCP project to bill (overrides GOOGLE_CLOUD_PROJECT)
  GEMINI_VIDGEN_LOCATION  region (default: us-central1 — Veo is regional, NOT global)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

VERSION = "0.1.0"

# Typed exit codes (mirror gi)
EX_OK = 0
EX_USAGE = 2
EX_CONFIG = 3
EX_AUTH = 4
EX_MODEL = 5
EX_INPUT = 6
EX_DEP = 7
EX_UNKNOWN = 10

# Short aliases -> full model id. Verify the live id in Model Garden before first run.
MODEL_ALIASES = {
    "standard": "veo-3.1-generate-001",
    "fast":     "veo-3.1-fast-generate-001",
}

# Pricing per OUTPUT-SECOND (USD), with audio. Verified 2026-06.
COST_PER_SECOND = {
    "veo-3.1-generate-001":      0.40,
    "veo-3.1-fast-generate-001": 0.15,
}

DEFAULT_MODEL = "veo-3.1-generate-001"
DEFAULT_LOCATION = "us-central1"   # Veo is regional, NOT global


# -- helpers --------------------------------------------------------------

def load_config():
    """Load key=value pairs from ~/.jstack/config.env (lower-priority source)."""
    cfg = {}
    path = os.path.expanduser("~/.jstack/config.env")
    if os.path.isfile(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def resolve_model(name, cfg):
    if name in MODEL_ALIASES:
        return MODEL_ALIASES[name]
    if name.startswith("veo-"):
        return name
    return None


def resolve_project(cfg, cli_val):
    if cli_val:
        return cli_val
    return (os.environ.get("GEMINI_VIDGEN_PROJECT") or
            cfg.get("GEMINI_VIDGEN_PROJECT") or
            os.environ.get("GOOGLE_CLOUD_PROJECT") or
            cfg.get("GOOGLE_CLOUD_PROJECT") or "")


def resolve_location(cfg, cli_val):
    if cli_val:
        return cli_val
    return (os.environ.get("GEMINI_VIDGEN_LOCATION") or
            cfg.get("GEMINI_VIDGEN_LOCATION") or
            DEFAULT_LOCATION)


def classify_error(err_text):
    t = err_text.lower()
    if any(x in t for x in ("unauthori", "unauthenticated",
                            "permission_denied", "credential", "403")):
        return "auth"
    if "resource_exhausted" in t or "429" in t:
        return "rate_limit"
    if any(x in t for x in ("not found", "not_found", "404")):
        return "model"
    if any(x in t for x in ("invalid_argument", "bad request", "400")):
        return "input"
    return "unknown"


def error_class_to_code(err_class):
    return {
        "auth":       EX_AUTH,
        "rate_limit": EX_UNKNOWN,
        "model":      EX_MODEL,
        "input":      EX_INPUT,
        "unknown":    EX_UNKNOWN,
        "usage":      EX_USAGE,
        "config":     EX_CONFIG,
        "dep":        EX_DEP,
    }.get(err_class, EX_UNKNOWN)


def cost_estimate(model, duration):
    rate = COST_PER_SECOND.get(model)
    if rate is None or duration is None:
        return None
    return round(rate * float(duration), 2)


def emit_envelope(ok, model, project, location, prompt, first_frame, out_files,
                  duration=None, resolution=None, aspect_ratio=None,
                  error=None, error_class=None, exit_code=0, cost=None):
    envelope = {
        "ok": ok,
        "model": model,
        "project": project,
        "location": location,
        "prompt": prompt,
        "first_frame": str(first_frame) if first_frame else None,
        "duration": duration,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "files_out": out_files,
        "cost_estimate": cost,
        "error": error,
        "error_class": error_class,
        "exit_code": exit_code,
    }
    print(json.dumps(envelope))


def _dep_check():
    try:
        import google.genai  # noqa: F401
    except ImportError:
        print("veo_gen: error: google-genai SDK not installed. Run: pip install google-genai",
              file=sys.stderr)
        sys.exit(EX_DEP)


def generate(project, location, model, prompt, first_frame, duration,
             resolution, aspect_ratio, out_path):
    """LIVE submit path — Veo on Vertex via google-genai (vertexai=True).

    i2v when first_frame is a local path or GCS URI; t2v when first_frame is None.
    Long-running op: submit, then poll to completion (clips take minutes). Output is
    saved as inline bytes to out_path. Implemented per references/veo-vertex-backend.md.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(vertexai=True, project=project, location=location)

    image = None
    if first_frame:
        ff = str(first_frame)
        if ff.startswith("gs://"):
            # GCS URI — infer mime from extension (png/jpg).
            mime = "image/png" if ff.lower().endswith(".png") else "image/jpeg"
            image = types.Image(gcs_uri=ff, mime_type=mime)
        else:
            if not os.path.isfile(ff):
                raise FileNotFoundError(f"first-frame not found: {ff}")
            image = types.Image.from_file(location=ff)

    cfg_kwargs = dict(
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        number_of_videos=1,
        generate_audio=True,
    )
    if duration is not None:
        cfg_kwargs["duration_seconds"] = int(duration)

    submit_kwargs = dict(model=model, prompt=prompt,
                         config=types.GenerateVideosConfig(**cfg_kwargs))
    if image is not None:
        submit_kwargs["image"] = image

    op = client.models.generate_videos(**submit_kwargs)

    # Long-running op — poll to completion (minutes). Cap the wait so a stuck op
    # doesn't hang forever; Veo clips finish in a few minutes.
    waited = 0
    while not op.done:
        time.sleep(10)
        waited += 10
        op = client.operations.get(op)
        if waited > 900:  # 15 min ceiling
            raise TimeoutError("Veo op did not finish within 15 min; check the console.")

    resp = getattr(op, "response", None)
    vids = getattr(resp, "generated_videos", None) if resp else None
    if not vids:
        # Surface RAI / safety blocks rather than failing silently.
        rai = getattr(resp, "rai_media_filtered_reasons", None) if resp else None
        raise RuntimeError(f"no video in response (op done but empty). rai={rai}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for i, gv in enumerate(vids):
        # number_of_videos=1, but write i-suffixed names if a model returns several.
        dest = out_path if i == 0 else out_path.with_name(
            f"{out_path.stem}-{i}{out_path.suffix}")
        gv.video.save(str(dest))
        written.append(str(dest))
    return written


# -- main -----------------------------------------------------------------

def main():
    cfg = load_config()

    ap = argparse.ArgumentParser(
        description="veo_gen — generic Veo 3.1 video generation via Vertex AI",
        add_help=False,
    )
    ap.add_argument("--prompt", required=False, help="Generation prompt")
    ap.add_argument("--first-frame", default=None, type=Path,
                    help="First-frame still for i2v (local path or GCS URI). Omit for t2v.")
    ap.add_argument("-o", "--out", default=None, help="Output .mp4 path")
    ap.add_argument("--model", default=None,
                    help=f"Model alias (standard, fast) or full veo-... id. Default: {DEFAULT_MODEL}")
    ap.add_argument("--duration", default=None, help="Output duration in seconds (~4-8; verify allowed set)")
    ap.add_argument("--resolution", default="1080p", help="720p | 1080p (default: 1080p)")
    ap.add_argument("--aspect-ratio", default="9:16", help="9:16 | 16:9 (default: 9:16)")
    ap.add_argument("--project", default=None, help="GCP project (overrides config)")
    ap.add_argument("--location", default=None, help="Vertex AI location (default: us-central1)")
    ap.add_argument("--json", action="store_true", dest="json_mode")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    ap.add_argument("--version", action="store_true")
    args = ap.parse_args()

    if args.help:
        print(__doc__)
        sys.exit(EX_OK)
    if args.version:
        print(f"veo_gen {VERSION}")
        try:
            import google.genai
            print(f"google-genai {google.genai.__version__}")
        except Exception:
            pass
        sys.exit(EX_OK)

    json_mode = args.json_mode

    # Resolve model
    model_input = (args.model or os.environ.get("GEMINI_VIDGEN_MODEL", "")
                   or cfg.get("GEMINI_VIDGEN_MODEL", ""))
    if model_input:
        model = resolve_model(model_input, cfg)
        if not model:
            msg = (f"unknown model: {model_input}. Use an alias "
                   f"({', '.join(MODEL_ALIASES.keys())}) or a full veo-... id")
            if json_mode:
                emit_envelope(False, model_input, "", "", args.prompt or "", args.first_frame,
                              [], error=msg, error_class="usage", exit_code=EX_USAGE)
            else:
                print(f"veo_gen: error: {msg}", file=sys.stderr)
            sys.exit(EX_USAGE)
    else:
        model = DEFAULT_MODEL

    project = resolve_project(cfg, args.project)
    location = resolve_location(cfg, args.location)
    prompt = args.prompt or ""
    cost = cost_estimate(model, args.duration)

    # Dry run — fully working, no API call, no billing
    if args.dry_run:
        if json_mode:
            emit_envelope(True, model, project, location, prompt, args.first_frame, [],
                          duration=args.duration, resolution=args.resolution,
                          aspect_ratio=args.aspect_ratio, cost=cost, exit_code=0)
        else:
            print("[dry-run] would call Veo on Vertex AI (no API call, no billing)")
            print(f"  project:      {project or '<unset>'}  (billing pinned via GEMINI_VIDGEN_PROJECT)")
            print(f"  location:     {location}  (Veo is regional, NOT global)")
            print(f"  model:        {model}")
            print(f"  mode:         {'i2v' if args.first_frame else 't2v'}")
            print(f"  first_frame:  {args.first_frame if args.first_frame else '<none>'}")
            print(f"  duration:     {args.duration or '<unset>'}s")
            print(f"  resolution:   {args.resolution}")
            print(f"  aspect_ratio: {args.aspect_ratio}")
            print(f"  out:          {args.out or '<unset>'}")
            print(f"  prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
            if cost is not None:
                print(f"  ~cost:        ${cost:.2f}  ({COST_PER_SECOND.get(model)}/s x {args.duration}s)")
            else:
                print("  ~cost:        <unknown — pass --duration to estimate>")
        sys.exit(EX_OK)

    # Pre-flight checks (mirror gi)
    if not project:
        msg = ("no GCP project set. Export GOOGLE_CLOUD_PROJECT (or GEMINI_VIDGEN_PROJECT), "
               "or add it to ~/.jstack/config.env")
        if json_mode:
            emit_envelope(False, model, "", location, prompt, args.first_frame, [],
                          error=msg, error_class="config", exit_code=EX_CONFIG)
        else:
            print(f"veo_gen: error: {msg}", file=sys.stderr)
        sys.exit(EX_CONFIG)

    if not prompt:
        msg = 'missing prompt. Pass --prompt "..."'
        if json_mode:
            emit_envelope(False, model, project, location, "", args.first_frame, [],
                          error=msg, error_class="usage", exit_code=EX_USAGE)
        else:
            print(f"veo_gen: error: {msg}", file=sys.stderr)
        sys.exit(EX_USAGE)

    if not args.out:
        msg = "missing output path. Pass -o <file.mp4>"
        if json_mode:
            emit_envelope(False, model, project, location, prompt, args.first_frame, [],
                          error=msg, error_class="usage", exit_code=EX_USAGE)
        else:
            print(f"veo_gen: error: {msg}", file=sys.stderr)
        sys.exit(EX_USAGE)

    _dep_check()

    out_path = Path(args.out)
    try:
        out_files = generate(project, location, model, prompt, args.first_frame,
                             args.duration, args.resolution, args.aspect_ratio, out_path)
    except Exception as e:
        err_str = str(e)
        err_class = classify_error(err_str)
        code = error_class_to_code(err_class)
        if json_mode:
            emit_envelope(False, model, project, location, prompt, args.first_frame, [],
                          error=err_str, error_class=err_class, exit_code=code)
        else:
            print(f"veo_gen: error: {err_str}", file=sys.stderr)
        sys.exit(code)

    if json_mode:
        emit_envelope(True, model, project, location, prompt, args.first_frame, out_files,
                      duration=args.duration, resolution=args.resolution,
                      aspect_ratio=args.aspect_ratio, cost=cost)
    else:
        for f in out_files:
            print(f"wrote {f}")
        if cost is not None:
            print(f"~${cost:.2f} ({model}, {args.duration}s)")
    sys.exit(EX_OK)


if __name__ == "__main__":
    main()
