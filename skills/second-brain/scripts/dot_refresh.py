#!/usr/bin/env python3
"""Materialise a connector-supplied Git delta in a new checkout; never fetch/publish."""
import argparse
import base64
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess


def git(repo, *args, data=None, env=None):
    result = subprocess.run(['git', '-C', str(repo), *args], input=data,
                            capture_output=True, check=False, env=env)
    if result.returncode:
        raise ValueError('Git operation failed: ' + result.stderr.decode(errors='replace')[-1000:])
    return result.stdout


def sha(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}', value):
        raise ValueError('Expected a Git SHA1 from the connector')
    return value


def safe_path(value):
    if (not isinstance(value, str) or not value or '\x00' in value or '\\' in value
            or PurePosixPath(value).is_absolute()
            or any(part in {'', '.', '..'} for part in value.split('/'))
            or any(part.casefold() == '.git' for part in value.split('/'))):
        raise ValueError('Unsafe repository-relative path')
    return value


def entry(value, content=False):
    if value is None:
        return None
    expected = {'mode', 'sha', 'content_base64'} if content else {'mode', 'sha'}
    if not isinstance(value, dict) or set(value) != expected or value['mode'] not in {'100644', '100755', '120000'}:
        raise ValueError('Expected a regular/executable/symlink Git blob entry')
    sha(value['sha'])
    if content:
        # Connector base64 may include line wrapping.
        return base64.b64decode(''.join(value['content_base64'].split()), validate=True)


def refresh(args):
    source, output, receipt = Path(args.repo).resolve(), Path(args.output).resolve(), Path(args.receipt).resolve()
    if output.exists() or receipt.exists():
        raise ValueError('Destination/receipt exists; inspect prior outcome before retrying')
    if source == output or source in output.parents or source == receipt or source in receipt.parents or output in receipt.parents:
        raise ValueError('Use separate source, destination and external receipt paths')
    plan = json.loads(Path(args.plan).read_text())
    expected = {'schema', 'repository', 'base_remote_commit', 'target_remote_commit',
                'base_tree', 'target_tree', 'changes'}
    if not isinstance(plan, dict) or set(plan) != expected or plan['schema'] != 'sb.dot-refresh/v1':
        raise ValueError('Invalid connector delta plan schema')
    if plan['repository'] != args.repository:
        raise ValueError('Plan repository differs from requested repository')
    for field in ('base_remote_commit', 'target_remote_commit', 'base_tree', 'target_tree'):
        sha(plan[field])
    cursor = json.loads(Path(args.cursor).read_text())
    if (cursor.get('repository') != args.repository or cursor.get('remote_commit') != plan['base_remote_commit']
            or cursor.get('tree') != plan['base_tree']):
        raise ValueError('Remote cursor does not match the delta base')
    head = git(source, 'rev-parse', 'HEAD').decode().strip()
    if cursor.get('local_commit') != head or git(source, 'rev-parse', 'HEAD^{tree}').decode().strip() != plan['base_tree']:
        raise ValueError('Local checkpoint differs from the cursor/tree')
    if git(source, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('Preserve and checkpoint local changes before refresh')
    if not isinstance(plan['changes'], list):
        raise ValueError('Expected complete connector delta list')
    paths, changes = set(), []
    for change in plan['changes']:
        if not isinstance(change, dict) or set(change) != {'path', 'before', 'after'}:
            raise ValueError('Invalid delta entry')
        path = safe_path(change['path'])
        if path in paths or (change['before'] is None and change['after'] is None):
            raise ValueError('Duplicate or empty delta entry')
        paths.add(path)
        entry(change['before'])
        payload = entry(change['after'], content=True)
        previous = git(source, 'ls-tree', '-z', 'HEAD', '--', ':(literal)' + path)
        expected_before = change['before']
        if expected_before is None:
            if previous:
                raise ValueError('Addition conflicts with existing tracked path: ' + path)
        else:
            prefix = (expected_before['mode'] + ' blob ' + expected_before['sha'] + '\t').encode()
            if previous != prefix + path.encode() + b'\0':
                raise ValueError('Before blob/mode differs at ' + path)
        changes.append((path, change['after'], payload))

    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'clone', '--no-checkout', '--no-hardlinks', '--', str(source), str(output)],
                   capture_output=True, check=True)
    # Clone copies objects/history, not source configuration or credentials.
    git(output, 'remote', 'remove', 'origin')
    git(output, 'read-tree', 'HEAD')
    for path, after, payload in changes:
        if after is None:
            git(output, 'update-index', '--force-remove', '--', path)
        else:
            actual = git(output, 'hash-object', '-w', '--stdin', data=payload).decode().strip()
            if actual != after['sha']:
                raise ValueError('Downloaded blob hash mismatch at ' + path)
            git(output, 'update-index', '--add', '--cacheinfo', after['mode'], actual, path)
    tree = git(output, 'write-tree').decode().strip()
    if tree != plan['target_tree']:
        raise ValueError('TARGET_TREE_MISMATCH: incomplete delta or wrong modes/bytes; source checkout preserved')
    env = dict(os.environ, GIT_AUTHOR_NAME='Dot Runtime', GIT_AUTHOR_EMAIL='dot-runtime@localhost',
               GIT_COMMITTER_NAME='Dot Runtime', GIT_COMMITTER_EMAIL='dot-runtime@localhost')
    message = ('Local byte snapshot of ' + args.repository + ' at ' + plan['target_remote_commit'] + '\n').encode()
    checkpoint = git(output, 'commit-tree', tree, '-p', head, data=message, env=env).decode().strip()
    git(output, 'update-ref', 'refs/heads/dot-snapshot', checkpoint)
    git(output, 'symbolic-ref', 'HEAD', 'refs/heads/dot-snapshot')
    git(output, 'checkout-index', '--all')
    if git(output, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('Refreshed checkout is not clean; source preserved')
    result = {'ok': True, 'schema': 'sb.dot-refresh-result/v1', 'repository': args.repository,
              'remote_commit': plan['target_remote_commit'], 'tree': tree,
              'local_commit': checkpoint, 'checkout': str(output), 'changes': len(changes),
              'history': 'local checkpoint over retained history; not remote Git fast-forward',
              'overlay': 'rebuild/check required', 'published': False}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, sort_keys=True) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('repo', 'output', 'receipt', 'plan', 'cursor', 'repository'):
        parser.add_argument('--' + flag, required=True)
    args = parser.parse_args()
    try:
        result, code = refresh(args), 0
    except Exception as exc:
        result, code = {'ok': False, 'error': str(exc), 'source_preserved': True,
                        'next': 'Inspect any destination before retry; no automatic cleanup or publish'}, 4
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
