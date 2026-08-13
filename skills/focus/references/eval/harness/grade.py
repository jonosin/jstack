#!/usr/bin/env python3
"""Deterministic grader for the jstack-voice skilltune ruler.

Grades PROSE TEXT (not a protocol). Reads one candidate file per probe named
<rundir>/<probe_id>.txt (the cold runner's raw response) and scores it against
each probe's declared `assertions` in evals.json. No LLM is used here; the soft
voice-fidelity term comes from an optional pre-computed judge file.

composite (per probe) = 0.50*assertion_pass_rate + 0.30*judge_mean + 0.20*efficiency
  - if the judge term is absent, the present weights are renormalized so an
    assertion-only run still yields a composite.

Usage:
  grade.py <evals.json> <rundir> [--judge <judge.json>]
           [--skill-tokens N] [--baseline-tokens M]

  <judge.json> format: {"<probe_id>": [s1, s2, ...], ...}, each s in [0,1].

Prints ONE JSON object (floats rounded to 4 places):
  {train_composite, heldout_composite, train_assertion_pass_rate,
   heldout_assertion_pass_rate, per_probe:{<id>:{passed,total,apr,judge_mean,
   composite,failures:[...]}}, judge_used, efficiency}
"""
import argparse
import json
import os
import re
import sys

FILLER_RE = re.compile(
    r"^(sure|certainly|of course|absolutely|i'?d be happy|happy to|"
    r"great question|good question)\b",
    re.IGNORECASE,
)
MD_STRUCTURE_RE = re.compile(r"^\s*([-*+]\s|#{1,6}\s|\d+[.)]\s)")
PLANNING_RE = re.compile(
    r"(?i)(definition of done|acceptance criteria|implementation plan|"
    r"^#+\s*plan\b|^\s*plan:\s*$)",
    re.MULTILINE,
)
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
SINGLE_LINE_COMMENT_PREFIXES = ("//", "#", "--", ";", "*")


def read(path, default=""):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return default


def first_nonempty_line(text):
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def code_blocks(text):
    return FENCE_RE.findall(text)


def strip_code_fences(text):
    return FENCE_RE.sub("", text)


def check_no_em_dash(text):
    return ("—" not in text) and ("–" not in text)


def check_no_filler_opener(text):
    return FILLER_RE.match(first_nonempty_line(text)) is None


def check_code_fence_present(text):
    return len(code_blocks(text)) >= 1


def check_no_code_comments(text):
    blocks = code_blocks(text)
    if not blocks:
        # no code emitted -> nothing to violate
        return True
    single_line_total = 0
    for block in blocks:
        # block-comment / docstring spans are disallowed outright
        if re.search(r"/\*.*?\*/", block, re.DOTALL):
            return False
        if "<!--" in block and "-->" in block:
            return False
        if re.search(r'"""', block) or re.search(r"'''", block):
            return False
        for raw in block.splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped.startswith(SINGLE_LINE_COMMENT_PREFIXES):
                single_line_total += 1
    return single_line_total <= 1


def check_prose_default(text):
    outside = strip_code_fences(text)
    for line in outside.splitlines():
        if MD_STRUCTURE_RE.match(line):
            return False
        if "|---" in line.replace(" ", ""):
            return False
    return True


def check_no_planning_doc(text):
    return PLANNING_RE.search(text) is None


def check_max_sentences(text, n):
    outside = strip_code_fences(text)
    parts = [p for p in re.split(r"[.?!]+", outside) if p.strip()]
    return len(parts) <= n


def check_nonempty(text):
    return bool(text.strip())


BOX_CHARS = set("│─┌┐└┘├┤┬┴┼╔╗╚╝║═╬▲▼◆→←↑↓▶◀")


def check_contains_all(text, needles):
    t = text.lower()
    return all(str(n).lower() in t for n in (needles or []))


def has_md_structure(text):
    outside = strip_code_fences(text)
    for line in outside.splitlines():
        if MD_STRUCTURE_RE.match(line):
            return True
        if "|---" in line.replace(" ", ""):
            return True
    return False


def check_ascii_diagram(text):
    if any(ch in text for ch in BOX_CHARS):
        return True
    for block in code_blocks(text):
        lines = [l for l in block.splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        arrowy = ("->" in block) or ("=>" in block) or ("|" in block)
        edges = sum(l.count("|") + l.count("+") for l in lines) >= 3
        if arrowy and edges:
            return True
    return False


def check_has_structure(text):
    return has_md_structure(text) or check_ascii_diagram(text)


def check_no_gratuitous_structure(text):
    # no markdown bullets / headers / numbered lists / tables outside code fences
    return check_prose_default(text)


def grade_probe(probe, candidate):
    failures = []
    assertions = probe.get("assertions", [])
    for a in assertions:
        c, aid = a.get("check"), a.get("id")
        ok = True
        if c == "no_em_dash":
            ok = check_no_em_dash(candidate)
        elif c == "no_filler_opener":
            ok = check_no_filler_opener(candidate)
        elif c == "code_fence_present":
            ok = check_code_fence_present(candidate)
        elif c == "no_code_comments":
            ok = check_no_code_comments(candidate)
        elif c == "prose_default":
            ok = check_prose_default(candidate)
        elif c == "no_planning_doc":
            ok = check_no_planning_doc(candidate)
        elif c == "max_sentences":
            ok = check_max_sentences(candidate, a.get("value", 2))
        elif c == "nonempty":
            ok = check_nonempty(candidate)
        elif c == "contains_all":
            ok = check_contains_all(candidate, a.get("value", []))
        elif c == "has_structure":
            ok = check_has_structure(candidate)
        elif c == "no_gratuitous_structure":
            ok = check_no_gratuitous_structure(candidate)
        elif c == "ascii_diagram_present":
            ok = check_ascii_diagram(candidate)
        else:
            failures.append("UNKNOWN_CHECK:%s" % aid)
            continue
        if not ok:
            failures.append(aid)
    total = len(assertions)
    passed = total - len([f for f in failures if not f.startswith("UNKNOWN_CHECK:")])
    apr = (passed / total) if total else 1.0
    return passed, total, apr, failures


def composite(apr, judge_mean, efficiency):
    # weights: assertion 0.50, judge 0.30, efficiency 0.20
    if judge_mean is None:
        w_apr, w_eff = 0.50, 0.20
        denom = w_apr + w_eff
        return (w_apr * apr + w_eff * efficiency) / denom
    return 0.50 * apr + 0.30 * judge_mean + 0.20 * efficiency


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evals")
    ap.add_argument("rundir")
    ap.add_argument("--judge", default=None)
    ap.add_argument("--skill-tokens", type=float, default=None)
    ap.add_argument("--baseline-tokens", type=float, default=None)
    args = ap.parse_args()

    data = json.loads(read(args.evals, "{}") or "{}")
    judge_data = {}
    if args.judge:
        try:
            judge_data = json.loads(read(args.judge, "{}") or "{}")
        except Exception:
            judge_data = {}

    # efficiency
    if args.skill_tokens is not None and args.baseline_tokens and args.baseline_tokens > 0:
        ratio = (args.skill_tokens - args.baseline_tokens) / args.baseline_tokens
        efficiency = 1.0 - 0.5 * clamp(ratio, 0.0, 1.0)
    else:
        efficiency = 1.0

    judge_used = bool(judge_data)
    per_probe = {}
    train, heldout = [], []
    train_apr, heldout_apr = [], []

    for probe in data.get("evals", []):
        pid = probe["id"]
        candidate = read(os.path.join(args.rundir, "%s.txt" % pid), "")
        passed, total, apr, failures = grade_probe(probe, candidate)

        scores = judge_data.get(pid)
        if scores:
            judge_mean = sum(scores) / len(scores)
        else:
            judge_mean = None

        comp = composite(apr, judge_mean, efficiency)
        per_probe[pid] = {
            "passed": passed,
            "total": total,
            "apr": round(apr, 4),
            "judge_mean": round(judge_mean, 4) if judge_mean is not None else None,
            "composite": round(comp, 4),
            "failures": failures,
        }
        if probe.get("split") == "heldout":
            heldout.append(comp)
            heldout_apr.append(apr)
        else:
            train.append(comp)
            train_apr.append(apr)

    def mean(xs):
        return round(sum(xs) / len(xs), 4) if xs else 0.0

    out = {
        "train_composite": mean(train),
        "heldout_composite": mean(heldout),
        "train_assertion_pass_rate": mean(train_apr),
        "heldout_assertion_pass_rate": mean(heldout_apr),
        "per_probe": per_probe,
        "judge_used": judge_used,
        "efficiency": round(efficiency, 4),
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
