#!/usr/bin/env python3
"""Run existing brain processors on dot's computer; never publish or use Actions."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n')
    temporary.replace(path)


def run(repo: Path, args: list[str]) -> dict:
    env = dict(os.environ, SECOND_BRAIN_ROOT=str(repo), PYTHONDONTWRITEBYTECODE='1')
    completed = subprocess.run([sys.executable, *args], cwd=repo, env=env,
                               capture_output=True, text=True, check=False)
    try:
        output = json.loads(completed.stdout)
    except json.JSONDecodeError:
        output = {'stdout_tail': completed.stdout[-2000:]}
    return {'exit_code': completed.returncode, 'output': output,
            'stderr_tail': completed.stderr[-2000:]}


def identity(route: str, source: str) -> str:
    url = urlsplit(source.strip())
    if route == 'x' and url.hostname in {'x.com', 'www.x.com', 'twitter.com', 'www.twitter.com'}:
        match = re.fullmatch(r'/[^/]+/status/(\d+)/?', url.path)
        if not match:
            raise ValueError('X requires a verified status permalink')
        return 'x:' + match[1]
    return source.strip()


def inspect_capture(repo: Path, request: dict) -> dict | None:
    """Recognise an already registered source without finalising it again."""
    sys.path.insert(0, str(repo / 'tools'))
    import sb_capture
    wanted = identity(request['route'], request['source'])
    manifest = repo / 'state/compile-manifest.jsonl'
    records = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()] if manifest.exists() else []
    for item in records:
        path = repo / item['path']
        if path.is_symlink() or not path.is_file():
            raise ValueError('Registered raw source is missing or a symlink; inspect manifest')
        metadata, body_hash = sb_capture.raw_body_hash(path)
        if identity(str(metadata['source_type']), str(metadata['source'])) != wanted:
            continue
        if body_hash != item['body_hash']:
            raise ValueError('Existing source body hash changed')
        _, body = sb_capture.parse_frontmatter(path.read_bytes())
        expected = ('\n' + request['body'].rstrip() + '\n').encode()
        if body != expected or metadata['role'] != request['role']:
            raise ValueError('Source already exists with different bytes/role; use an explicit correction/version route')
        return {'raw_id': item['raw_id'], 'target': item['path'],
                'compile_state': item['state'], 'already_present': True,
                'file_sha256': digest(path.read_bytes())}
    return None


@contextlib.contextmanager
def lock(path: Path):
    try:
        path.mkdir()
    except FileExistsError:
        raise ValueError('RUNTIME_LOCKED: inspect unfinished operation before removing lock')
    try:
        yield
    finally:
        path.rmdir()


def execute(args) -> tuple[dict, int]:
    repo, state = Path(args.repo).resolve(), Path(args.state).resolve()
    if repo == state or repo in state.parents:
        raise ValueError('--state must be outside the brain checkout')
    if not (repo / 'AGENTS.md').is_file() or not (repo / 'tools/sb.py').is_file():
        raise ValueError('--repo must be the intended complete brain checkout')
    state.mkdir(parents=True, exist_ok=True)
    if args.operation == 'doctor':
        required = ['tools/sb.py', 'tools/remote_capture.py', 'tools/remote_compile.py',
                    'tools/remote_compile_verify.py', 'tools/sb_overlay_inputs.py',
                    'schemas/raw-v2.json', 'schemas/canonical-v2.json', 'CONTEXT.md']
        missing = [name for name in required if not (repo / name).is_file()]
        yaml_ready = importlib.util.find_spec('yaml') is not None
        git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo, capture_output=True, text=True)
        return {'ok': not missing and yaml_ready and git.returncode == 0,
                'python': sys.version.split()[0], 'pyyaml': yaml_ready,
                'missing_files': missing, 'git_head': git.stdout.strip(),
                'execution': 'dot runtime; no Actions or publishing',
                'credentials_required_for_local_processing': False}, 0 if not missing and yaml_ready and git.returncode == 0 else 3

    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}', args.id):
        raise ValueError('Use a stable operation ID with letters, digits, dot, underscore or hyphen')
    value = json.loads(Path(args.request).read_text())
    payload_hash = digest(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())
    receipt = state / (args.id + '.json')
    # One lock per checkout in this state directory. Reuse --state for all operations.
    with lock(state / 'operation.lock'):
        previous = json.loads(receipt.read_text()) if receipt.exists() else None
        if previous and (previous['payload_sha256'] != payload_hash or previous['operation'] != args.operation):
            raise ValueError('Operation ID already belongs to a different request')
        if args.operation == 'capture':
            sys.path.insert(0, str(repo / 'tools'))
            import remote_capture
            remote_capture._load(Path(args.request))
            if value['body'] == '@fetch-source':
                raise ValueError('Supply already obtained source Markdown; this driver does not refetch')
            relative = Path(value['target'])
            if (relative.is_absolute() or len(relative.parts) != 2 or
                    relative.parts[0] != 'raw' or relative.suffix != '.md' or
                    (repo / relative).parent.resolve() != (repo / 'raw').resolve() or
                    (repo / 'raw').is_symlink()):
                raise ValueError('Target must be one regular flat raw/*.md path')
            existing = inspect_capture(repo, value)
            if existing:
                report = {'operation': 'capture', 'payload_sha256': payload_hash,
                          'captured': True, 'result': existing, 'verified': False,
                          'next': 'Run sb verify and compile separately when authorised'}
                write_json(receipt, report)
                return report, 0
            if previous or (repo / relative).exists() or (repo / relative).is_symlink():
                raise ValueError('Partial/uncertain capture exists; inspect receipt/raw and use public capture resume if applicable')
        elif previous:
            # Compile may have consumed its input before a later gate failed.
            raise ValueError('Compile already attempted; inspect receipt and public compile show/resume, never replay blindly')

        if args.operation == 'compile':
            dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo, text=True)
            if dirty:
                raise ValueError('Compile requires a clean isolated checkpoint; preserve and checkpoint owned capture changes first')
            if value.get('schema') != 'sb.remote-compile-request/v1':
                raise ValueError('Expected current remote-compile request schema')

        transport = repo / 'state/dot-runtime-requests' / (args.id + '.json')
        if transport.exists() or transport.is_symlink():
            raise ValueError('Existing runtime request requires inspection')
        transport.parent.mkdir(parents=True, exist_ok=True)
        if transport.parent.is_symlink():
            raise ValueError('Runtime request directory must be regular')
        write_json(transport, value)
        report = {'operation': args.operation, 'payload_sha256': payload_hash,
                  'captured': False, 'compiled': False, 'indexed': False,
                  'verified': False, 'phase': 'started', 'steps': []}
        write_json(receipt, report)
        processor = 'tools/remote_capture.py' if args.operation == 'capture' else 'tools/remote_compile.py'
        result = run(repo, [processor, str(transport)])
        report['steps'].append({'command': processor, **result})
        if result['exit_code']:
            report['phase'] = 'blocked'
            write_json(receipt, report)
            return report, result['exit_code']
        report['captured' if args.operation == 'capture' else 'compiled'] = True
        report.pop('captured' if args.operation == 'compile' else 'compiled', None)
        report['phase'] = args.operation + '-processed'
        write_json(receipt, report)
        if args.operation == 'compile':
            steps = [['tools/sb.py', 'views', 'build', '--json'],
                     ['tools/sb_overlay_inputs.py'],
                     ['tools/sb.py', 'overlay', 'update', '--json'],
                     ['tools/sb.py', 'overlay', 'freshness', '--json'],
                     ['tools/remote_compile_verify.py', str(Path(args.request).resolve())]]
            for command in steps:
                result = run(repo, command)
                report['steps'].append({'command': command, **result})
                if result['exit_code']:
                    report['phase'] = 'blocked'
                    write_json(receipt, report)
                    return report, result['exit_code']
                if command[1:3] == ['overlay', 'freshness']:
                    report['indexed'] = True
                write_json(receipt, report)
        result = run(repo, ['tools/sb.py', 'verify', '--json'])
        report['steps'].append({'command': 'sb verify --json', **result})
        report['verified'] = result['exit_code'] == 0 and result['output'].get('ok') is True
        report['phase'] = 'complete' if report['verified'] else 'blocked'
        report['publication'] = 'local to dot checkout; publish reviewed paths separately'
        write_json(receipt, report)
        return report, 0 if report['verified'] else 3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--state', required=True, help='Private receipt directory outside checkout; reuse across operations')
    sub = parser.add_subparsers(dest='operation', required=True)
    sub.add_parser('doctor')
    for name in ('capture', 'compile'):
        command = sub.add_parser(name)
        command.add_argument('--id', required=True)
        command.add_argument('--request', required=True)
    args = parser.parse_args()
    try:
        report, code = execute(args)
    except Exception as exc:
        report, code = {'ok': False, 'phase': 'blocked', 'error': str(exc),
                        'outcome': 'inspect prior receipts before retry; no automatic publish'}, 3
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
