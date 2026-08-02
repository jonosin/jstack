#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; SCRIPT = ROOT / "scripts" / "apify_contact_results.py"
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    (root/'input.json').write_text(json.dumps({'urls':[{'url':'https://stay.example/'}]}))
    (root/'raw.json').write_text(json.dumps([{'seedUrl':'https://stay.example/','url':'https://stay.example/contact','email':'hello@stay.example'}]))
    (root/'run.json').write_text(json.dumps({'data':{'id':'run','defaultDatasetId':'data','status':'SUCCEEDED','usageTotalUsd':0.01}}))
    (root/'properties.json').write_text(json.dumps([{'property':'Stay','website':'https://stay.example/'}]))
    out=root/'out'
    subprocess.run([sys.executable,str(SCRIPT),'--cohort',str(root/'input.json'),'--raw',str(root/'raw.json'),'--run',str(root/'run.json'),'--properties',str(root/'properties.json'),'--output-dir',str(out)],check=True,capture_output=True,text=True)
    row=json.loads((out/'contact-results.json').read_text())[0]
    assert row['status'] == 'published_unverified' and row['emails'][0]['source_url'].endswith('/contact')
print('PASS: source-linked Apify email output stays unverified until mail-domain review')
