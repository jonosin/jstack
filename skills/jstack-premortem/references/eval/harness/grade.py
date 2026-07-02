#!/usr/bin/env python3
"""Deterministic grader for jstack-premortem skilltune.

Scores ONE eval run from artifacts the cold-runner produced in <rundir>:
  result.json    runner self-report (schema below)
  transcript.md  the premortem-transcript artifact (verified for the frame)
  report.html    the premortem-report artifact (verified for the frame)
  judge.json     {"judge_score": float in [0,1]} from the COLD JUDGE subagent
                 (absent during the S1 dry-run gate -> neutral fallback)

composite = 0.50*assertion_pass_rate + 0.30*judge_score + 0.20*efficiency

result.json schema (runner self-report):
{
  "declined": bool, "asked_question": bool, "question_count": int,
  "frame_stated": bool, "num_reasons": int,
  "reasons": [{"title": str, "has_assumption": bool, "has_warning": bool}],
  "synthesis": {"most_likely": str, "most_dangerous": str, "hidden_assumption": str,
                "revised_plan": str, "checklist": str},
  "revised_plan_text": str, "chat_output": str,
  "transcript_path": str, "report_path": str
}

Usage: grade.py <evals.json> <eval_id> <rundir> [judge_score]
Prints one JSON line.
"""
import json, re, sys, os, math

GENERIC = {"market","markets","team","product","technology","tech","finance",
           "financial","legal","operations","ops","competition","competitor",
           "competitors","execution","marketing","sales","people","process",
           "money","time","risk","risks"}

def load(p, default=None):
    try:
        with open(p) as f: return f.read()
    except Exception: return default

def sentences(t):
    t = (t or "").strip()
    if not t: return []
    return [s for s in re.split(r"[.!?]+", t) if s.strip()]

def main():
    evals_path, eval_id, rundir = sys.argv[1], sys.argv[2], sys.argv[3]
    judge_cli = sys.argv[4] if len(sys.argv) > 4 else None
    evals = json.loads(load(evals_path))
    ev = next(e for e in evals["evals"] if e["id"] == eval_id)

    try:
        result = json.loads(load(os.path.join(rundir, "result.json"), "{}") or "{}")
    except Exception:
        result = {}
    transcript = (load(os.path.join(rundir, "transcript.md"), "") or "")
    report = (load(os.path.join(rundir, "report.html"), "") or "")
    artifacts_text = (transcript + "\n" + report).lower()

    reasons = result.get("reasons") or []
    num_reasons = result.get("num_reasons")
    if num_reasons is None: num_reasons = len(reasons)
    syn = result.get("synthesis") or {}

    failures = []
    def chk(cond, aid):
        if not cond: failures.append(aid)
        return cond

    frame_rx = bool(re.search(r"6\s*months", artifacts_text)) and \
               bool(re.search(r"fail|looking back|backward", artifacts_text))

    for a in ev.get("assertions", []):
        c, aid = a["check"], a["id"]
        if c == "frame_stated":
            chk(bool(result.get("frame_stated")) and frame_rx, aid)
        elif c == "no_preset_categories":
            titles = [(r.get("title") or "").strip().lower() for r in reasons]
            def is_generic(t):
                w = re.findall(r"[a-z]+", t)
                return len(w) > 0 and len(w) <= 2 and all(x in GENERIC for x in w)
            gen = sum(1 for t in titles if is_generic(t))
            preset_sig = bool(re.search(r"(?m)^#{1,4}\s*(market|team|product|technology|finance|legal)\b", transcript.lower()))
            thresh = max(2, math.ceil(num_reasons * 0.5)) if num_reasons else 2
            chk(num_reasons >= 1 and gen < thresh and not preset_sig, aid)
        elif c == "min_failure_reasons":
            chk(num_reasons >= a["value"], aid)
        elif c == "each_reason_has_assumption_and_warning":
            chk(len(reasons) > 0 and all(r.get("has_assumption") and r.get("has_warning") for r in reasons), aid)
        elif c == "synthesis_has_five":
            keys = ["most_likely","most_dangerous","hidden_assumption","revised_plan","checklist"]
            chk(all((syn.get(k) or "").strip() for k in keys), aid)
        elif c == "revised_plan_mapped":
            plan = (result.get("revised_plan_text") or syn.get("revised_plan") or "").lower()
            mapped = 0
            for r in reasons:
                title = (r.get("title") or "").lower()
                kws = [w for w in re.findall(r"[a-z]{4,}", title) if w not in GENERIC]
                if kws and any(w in plan for w in kws[:5]): mapped += 1
            need = max(2, math.ceil(num_reasons * 0.5)) if num_reasons else 2
            chk(num_reasons >= 1 and mapped >= need, aid)
        elif c == "chat_summary_three_sentences":
            n = len(sentences(result.get("chat_output")))
            chk(1 <= n <= 3, aid)
        elif c == "asked_one_question":
            chk(result.get("asked_question") is True and result.get("question_count") == 1, aid)
        elif c == "declined_premortem":
            chk(result.get("declined") is True and num_reasons == 0 and not (result.get("report_path") or "").strip(), aid)
        else:
            failures.append("UNKNOWN_CHECK:" + aid)

    total = len(ev.get("assertions", []))
    passed = total - len(failures)
    apr = (passed / total) if total else 1.0

    judge_present = False
    judge_score = None
    if judge_cli is not None:
        try: judge_score = float(judge_cli); judge_present = True
        except Exception: judge_score = None
    if judge_score is None:
        jraw = load(os.path.join(rundir, "judge.json"))
        if jraw:
            try:
                judge_score = float(json.loads(jraw).get("judge_score")); judge_present = True
            except Exception: judge_score = None
    if judge_score is None:
        if ev.get("type") == "negative" or result.get("declined") is True:
            judge_score = 1.0
        else:
            judge_score = 0.5
    judge_score = max(0.0, min(1.0, judge_score))

    eff = 1.0
    if ev.get("context_sufficient") and result.get("asked_question"):
        eff -= 0.34
    titles = [(r.get("title") or "").strip().lower() for r in reasons]
    dups = len(titles) - len(set(titles))
    if dups > 0: eff -= min(0.33, 0.11 * dups)
    nchat = len(sentences(result.get("chat_output")))
    if nchat > 3: eff -= min(0.33, 0.11 * (nchat - 3))
    eff = max(0.0, round(eff, 4))

    composite = round(0.50 * apr + 0.30 * judge_score + 0.20 * eff, 4)
    print(json.dumps({
        "eval_id": eval_id, "passed": passed, "total": total,
        "assertion_pass_rate": round(apr, 4), "judge_score": round(judge_score, 4),
        "efficiency": eff, "composite": composite, "judge_present": judge_present,
        "failures": failures,
    }))

if __name__ == "__main__":
    main()
