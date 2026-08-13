#!/usr/bin/env python3
"""skilltune live dashboard generator (dependency-free, file://-safe).

Usage:
    dashboard.py <sandbox-dir> [--force]

- Reads   <sandbox>/history.json   (the loop's structured memory).
- Writes  <sandbox>/data.js        (always: `window.DATA = {...}`).
- Writes  <sandbox>/dashboard.html (once; --force rewrites the shell).

Open dashboard.html in a browser. The shell loads data.js via a <script> tag
(works on file:// where fetch() is CORS-blocked), auto-reloads every 5s, and
stops reloading when DATA.status != "running" OR when you click Stop.

Expected history.json schema (all fields optional; the dashboard degrades):
{
  "skill": "jstack-foo",
  "status": "running" | "stopped" | "done",
  "baseline_composite": 0.83,        # baseline value (a metric value if `metric` is set)
  "target": 0.95,
  "best": {"version": "v3", "composite": 0.91},
  "experiments": [
    {"exp": 1, "version": "v1", "category": "structure",
     "hypothesis": "tighten the width rule", "train": 0.86, "heldout": 0.84,
     "delta": 0.02, "decision": "KEEP"}
  ],
  "coverage": {"structure": {"experiments": 2, "kept": 1, "best_delta": 0.03, "saturated": false}},

  # OPTIONAL — only for pure non-normalized metric targets (bundle size, latency,
  # tokens, lint count). Absent => composite convention: y-axis [0,1], higher better.
  # NOTE: composite [0,1] values are stored as-is but DISPLAYED as percentages
  # (x100, 2 decimals, "%"); raw-metric runs keep their real units.
  # When set, the chart scales the y-axis to [min,max], labels the unit, and shows the
  # better-direction; train/heldout/baseline/target then hold raw metric values.
  "metric": {"name": "bundle size", "unit": "KB", "direction": "lower", "min": 0, "max": 400}
}
"""
import sys, os, json


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: dashboard.py <sandbox-dir> [--force]")
    sb = sys.argv[1]
    force = "--force" in sys.argv
    hist_path = os.path.join(sb, "history.json")
    data = {}
    if os.path.exists(hist_path):
        try:
            with open(hist_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            data = {"status": "running", "error": f"history.json unreadable: {e}", "experiments": []}
    with open(os.path.join(sb, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
    html_path = os.path.join(sb, "dashboard.html")
    if force or not os.path.exists(html_path):
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(HTML)
    print("dashboard:", html_path)


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>skilltune — live</title>
<script src="./data.js"></script>
<style>
  :root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--fg:#e6edf3;--mut:#8b949e;
        --keep:#3fb950;--revert:#f85149;--near:#d29922;--neutral:#6e7681;--accent:#58a6ff}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--fg);
       font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}
  header{display:flex;align-items:center;gap:16px;flex-wrap:wrap;
         padding:14px 20px;border-bottom:1px solid var(--line);background:var(--panel)}
  h1{font-size:15px;margin:0;font-weight:600}
  .badge{padding:2px 10px;border-radius:10px;font-size:11px;font-weight:700;text-transform:uppercase}
  .b-running{background:rgba(88,166,255,.15);color:var(--accent)}
  .b-done{background:rgba(63,185,80,.15);color:var(--keep)}
  .b-stopped{background:rgba(248,81,73,.15);color:var(--revert)}
  .stat{color:var(--mut)} .stat b{color:var(--fg)}
  .spacer{flex:1}
  button{font:inherit;cursor:pointer;border:1px solid var(--line);background:#21262d;
         color:var(--fg);padding:6px 14px;border-radius:6px}
  button:hover{border-color:var(--accent)}
  #stop{border-color:var(--revert);color:var(--revert)}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:20px}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:16px}
  .panel.full{grid-column:1/3}
  .panel h2{font-size:12px;margin:0 0 12px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
  table{width:100%;border-collapse:collapse;font-size:12px}
  th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
  th{color:var(--mut);font-weight:600}
  td.num{text-align:right;font-variant-numeric:tabular-nums}
  .dec{font-weight:700;padding:1px 7px;border-radius:5px;font-size:11px}
  .KEEP{background:rgba(63,185,80,.15);color:var(--keep)}
  .REVERT{background:rgba(248,81,73,.15);color:var(--revert)}
  .NEAR_MISS{background:rgba(210,153,34,.15);color:var(--near)}
  .NEUTRAL{background:rgba(110,118,129,.2);color:var(--neutral)}
  .cov{display:flex;flex-wrap:wrap;gap:8px}
  .cell{border:1px solid var(--line);border-radius:6px;padding:8px 10px;min-width:120px}
  .cell .c-name{font-size:11px;color:var(--mut)}
  .cell .c-bar{height:4px;border-radius:2px;background:var(--line);margin:6px 0 4px;overflow:hidden}
  .cell .c-fill{height:100%;background:var(--accent)}
  .cell.sat{opacity:.5} .cell.sat .c-fill{background:var(--neutral)}
  .empty{color:var(--mut);padding:20px;text-align:center}
  text{fill:var(--mut);font:10px ui-monospace,monospace}
</style>
</head>
<body>
<header>
  <h1>skilltune</h1><span id="skill" class="stat"></span>
  <span id="badge" class="badge b-running">running</span>
  <span class="stat">baseline <b id="base">–</b></span>
  <span class="stat">best <b id="best">–</b></span>
  <span class="stat">target <b id="target">–</b></span>
  <span class="stat">exp <b id="count">0</b></span>
  <div class="spacer"></div>
  <span class="stat" id="tick"></span>
  <button id="stop">&#9209; Stop</button>
</header>

<div class="grid">
  <div class="panel full"><h2 id="chartTitle">composite over experiments</h2><div id="chart"></div></div>
  <div class="panel full"><h2>mutations — keep / revert / near-miss</h2><div id="muts"></div></div>
  <div class="panel full"><h2>coverage matrix</h2><div id="cov" class="cov"></div></div>
</div>

<script>
const D = window.DATA || {};
const exps = D.experiments || [];
const status = D.status || "running";
// optional metric block: {name, unit, direction:"lower"|"higher", min, max}.
// absent => composite convention: [0,1], higher is better.
const M = D.metric || null;
const LO = (M && M.min!=null) ? M.min : 0;
const HI = (M && M.max!=null) ? M.max : 1;
const U  = (M && M.unit) ? (" "+M.unit) : "";
// Display rule: [0,1] composite scores are SHOWN as percentages (x100, 2dp, "%").
// Raw-metric runs keep their real units. The stored values + chart scaling stay [0,1].
const fmt = v => (v==null||isNaN(v)) ? "–"
  : (M ? Number(v).toLocaleString(undefined,{maximumFractionDigits:2})+U
       : (Number(v)*100).toFixed(2)+"%");
const fmtAxis = t => (M ? Number(t).toLocaleString(undefined,{maximumFractionDigits:2}) : (t*100).toFixed(0)+"%");

document.getElementById("skill").textContent = D.skill ? "· "+D.skill : "";
document.getElementById("base").textContent = fmt(D.baseline_composite);
document.getElementById("best").textContent = D.best ? fmt(D.best.composite)+(D.best.version?" ("+D.best.version+")":"") : "–";
document.getElementById("target").textContent = fmt(D.target);
document.getElementById("count").textContent = exps.length;
const badge = document.getElementById("badge");
badge.textContent = status; badge.className = "badge b-"+status;
document.getElementById("chartTitle").textContent =
  (M ? (M.name||"metric") : "composite") + " over experiments";

// ---- SVG line chart (hand-rendered, no deps) ----
(function(){
  const W=920,H=240,pad=36;
  const xs = exps.map((e,i)=> e.exp!=null ? e.exp : i+1);
  const maxX = Math.max(1, ...xs);
  const span = (HI-LO)||1;
  const px = x => pad + (x/(maxX||1))*(W-2*pad);
  const py = v => H-pad - (Math.max(0,Math.min(1,(v-LO)/span)))*(H-2*pad);
  const path = key => exps.filter(e=>e[key]!=null)
     .map((e,i)=> (i?"L":"M")+px(e.exp!=null?e.exp:i+1).toFixed(1)+" "+py(e[key]).toFixed(1)).join(" ");
  const hline = (v,color,dash) => v==null?"":
     `<line x1="${pad}" y1="${py(v)}" x2="${W-pad}" y2="${py(v)}" stroke="${color}" stroke-dasharray="${dash}" stroke-width="1"/>`;
  const dots = key => exps.filter(e=>e[key]!=null)
     .map(e=>`<circle cx="${px(e.exp!=null?e.exp:1)}" cy="${py(e[key])}" r="3" fill="${key==='heldout'?'#a371f7':'#58a6ff'}"/>`).join("");
  let g="";
  for(let i=0;i<=4;i++){ const t=LO+span*i/4;
    g+=`<line x1="${pad}" y1="${py(t)}" x2="${W-pad}" y2="${py(t)}" stroke="#21262d"/>`+
       `<text x="6" y="${py(t)+3}">${fmtAxis(t)}</text>`; }
  const better = M ? (M.direction==="lower" ? " · ↓ lower better" : " · ↑ higher better") : "";
  const chart = exps.length ? `<svg viewBox="0 0 ${W} ${H}" width="100%">
    ${g}
    ${hline(D.baseline_composite,'#8b949e','4 3')}
    ${hline(D.target,'#3fb950','2 4')}
    <path d="${path('train')}" fill="none" stroke="#58a6ff" stroke-width="2"/>
    <path d="${path('heldout')}" fill="none" stroke="#a371f7" stroke-width="2" stroke-dasharray="5 3"/>
    ${dots('train')}${dots('heldout')}
    <text x="${W-pad}" y="14" text-anchor="end">train ● · held-out ◇ · baseline -- · target --${better}</text>
  </svg>` : `<div class="empty">no experiments yet</div>`;
  document.getElementById("chart").innerHTML = chart;
})();

// ---- mutations table ----
(function(){
  if(!exps.length){ document.getElementById("muts").innerHTML='<div class="empty">no experiments yet</div>'; return; }
  const rows = exps.slice().reverse().map(e=>`<tr>
    <td class="num">${e.exp??""}</td><td>${e.version??""}</td><td>${e.category??""}</td>
    <td>${(e.hypothesis??"").replace(/[<>]/g,"")}</td>
    <td class="num">${fmt(e.train)}</td><td class="num">${fmt(e.heldout)}</td>
    <td class="num">${e.delta>0?"+":""}${fmt(e.delta)}</td>
    <td><span class="dec ${e.decision||'NEUTRAL'}">${e.decision||"–"}</span></td></tr>`).join("");
  document.getElementById("muts").innerHTML = `<table><thead><tr>
    <th>#</th><th>ver</th><th>category</th><th>hypothesis</th>
    <th class="num">train</th><th class="num">held</th><th class="num">Δ</th><th>decision</th>
    </tr></thead><tbody>${rows}</tbody></table>`;
})();

// ---- coverage matrix ----
(function(){
  const cov = D.coverage || {};
  const keys = Object.keys(cov);
  if(!keys.length){ document.getElementById("cov").innerHTML='<div class="empty">no coverage yet</div>'; return; }
  document.getElementById("cov").innerHTML = keys.map(k=>{
    const c=cov[k]||{}; const n=c.experiments||0; const kept=c.kept||0;
    const pct = n? Math.round(kept/n*100):0;
    return `<div class="cell${c.saturated?' sat':''}">
      <div class="c-name">${k}${c.saturated?' · saturated':''}</div>
      <div><b>${kept}</b>/${n} kept</div>
      <div class="c-bar"><div class="c-fill" style="width:${pct}%"></div></div>
      <div class="c-name">best Δ ${c.best_delta!=null?(c.best_delta>0?"+":"")+fmt(c.best_delta):"–"}</div>
    </div>`;
  }).join("");
})();

// ---- live reload + sticky Stop/Resume ----
const PERIOD=5;
let paused = localStorage.getItem("skilltune-paused")==="1" || status!=="running";
let left=PERIOD, timer=null;
const stopBtn=document.getElementById("stop"), tick=document.getElementById("tick");
function render(){
  stopBtn.innerHTML = paused ? "&#9654; Resume" : "&#9209; Stop";
  if(status!=="running"){ tick.textContent="run "+status+" — auto-refresh off"; stopBtn.disabled=(status!=="running"&&!paused)?false:false; }
  else tick.textContent = paused ? "paused" : ("refresh in "+left+"s");
}
function loop(){
  if(paused || status!=="running"){ render(); return; }
  left--; render();
  if(left<=0){ location.reload(); return; }
  timer=setTimeout(loop,1000);
}
stopBtn.onclick=()=>{
  paused=!paused;
  localStorage.setItem("skilltune-paused", paused?"1":"0");
  if(paused){ clearTimeout(timer); } else { left=PERIOD; loop(); }
  render();
};
render(); if(!paused && status==="running") loop();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
