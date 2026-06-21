#!/usr/bin/env python3
"""Deterministic grader for jstack-challenge skilltune.

Scores a single eval run from ground-truth artifacts (NO LLM judge):
  <rundir>/actions.log   TSV of every codex-advisor-stub.sh call: "<action>\t<arg>"
  <rundir>/result.json   eval-runner self-report (engine, fell_back, background,
                         prompt_file, surfaced, declined, tool_calls, ...)
  <prompt_file>          the six-section briefing the agent wrote (if any)

composite = 0.70 * assertion_pass_rate + 0.30 * efficiency_score   (protocol, not prose)

Usage: grade.py <eval_json_inline_path> <eval_id> <rundir>
Prints one JSON object: {eval_id, passed, total, assertion_pass_rate, efficiency,
                          composite, failures:[...]}
"""
import json, re, sys, os

def load(p, default=None):
    try:
        with open(p) as f: return f.read()
    except Exception: return default

def main():
    evals_path, eval_id, rundir = sys.argv[1], sys.argv[2], sys.argv[3]
    evals = json.loads(load(evals_path))
    ev = next(e for e in evals["evals"] if e["id"] == eval_id)

    # --- load artifacts ---
    actions = []
    raw = load(os.path.join(rundir, "actions.log"), "") or ""
    for line in raw.splitlines():
        if not line.strip(): continue
        parts = line.split("\t")
        actions.append((parts[0], parts[1] if len(parts) > 1 else ""))
    try:
        result = json.loads(load(os.path.join(rundir, "result.json"), "{}") or "{}")
    except Exception:
        result = {}
    pf = result.get("prompt_file") or ""
    prompt = load(pf, "") if pf else ""
    prompt = prompt or ""
    pl = prompt.lower()

    acts = [a for a, _ in actions]
    failures = []
    def chk(cond, aid):
        if not cond: failures.append(aid)
        return cond

    for a in ev.get("assertions", []):
        c, aid = a["check"], a["id"]
        if c == "probe_first":
            chk(len(acts) >= 1 and acts[0] == "probe", aid)
        elif c == "probe_count_eq":
            chk(acts.count("probe") == a["value"], aid)
        elif c == "run_called":
            chk("run" in acts, aid)
        elif c == "run_not_called":
            chk("run" not in acts, aid)
        elif c == "no_script_calls":
            chk(len(acts) == 0, aid)
        elif c == "engine_eq":
            chk(result.get("engine") == a["value"], aid)
        elif c == "fell_back_eq":
            chk(bool(result.get("fell_back")) == a["value"], aid)
        elif c == "background_true":
            chk(result.get("background") is True, aid)
        elif c == "surfaced_nonempty":
            chk(bool((result.get("surfaced") or "").strip()), aid)
        elif c == "declined":
            chk(result.get("declined") is True and "probe" not in acts, aid)
        elif c == "spawned_claude_advisor":
            chk(result.get("spawned_claude_advisor") is True, aid)
        elif c == "prompt_six_sections":
            heads = len(re.findall(r"(?m)^#{1,4}\s*\d", prompt)) + \
                    len(re.findall(r"(?m)^\s*\d\.\s+\w", prompt))
            kw = sum(k in pl for k in ["advisor", "founder", "kill", "reframe",
                                       "interrogat", "verdict"])
            chk(heads >= 6 or kw >= 5, aid)
        elif c == "prompt_adversarial":
            adv = any(k in pl for k in ["pressure-test", "pressure test", "attack",
                                        "skeptic", "no incentive to be liked"])
            items = len(re.findall(r"(?m)^\s*\d[\.\)]\s+\w", prompt)) + pl.count("?")
            chk(adv and items >= 5, aid)
        elif c == "surfaced_verdict_first":
            s = (result.get("surfaced") or "").strip().lower()
            first = s.splitlines()[0] if s else ""
            chk(result.get("verdict_first") is True or "verdict" in first, aid)
        elif c == "main_agent_position":
            chk(result.get("took_position") is True, aid)
        else:
            failures.append(f"UNKNOWN_CHECK:{aid}")

    total = len(ev.get("assertions", []))
    passed = total - len(failures)
    apr = (passed / total) if total else 1.0

    # efficiency: meaningful tool-calls vs the eval's budget
    maxc = ev.get("max_calls")
    tc = result.get("tool_calls")
    if maxc and isinstance(tc, (int, float)) and tc > 0:
        eff = min(1.0, maxc / tc)
    else:
        eff = 1.0
    composite = round(0.70 * apr + 0.30 * eff, 4)
    print(json.dumps({
        "eval_id": eval_id, "passed": passed, "total": total,
        "assertion_pass_rate": round(apr, 4), "efficiency": round(eff, 4),
        "composite": composite, "failures": failures,
    }))

if __name__ == "__main__":
    main()
