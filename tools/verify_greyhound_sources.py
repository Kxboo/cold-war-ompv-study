"""Verify pinned Greyhound source hashes and line references using a local clone.

Read-only: uses git show at the recorded commit, regardless of worktree changes.
No credentials, network access or game capture are required.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def verify(clone, source_map):
    commit = source_map['commit']
    sources, checked = {}, 0
    for source in source_map['sources']:
        result = subprocess.run(['git', 'show', f'{commit}:{source["path"]}'],
                                cwd=clone, capture_output=True, check=True)
        data = result.stdout
        if hashlib.sha256(data).hexdigest() != source['sha256']:
            raise ValueError('source hash mismatch: ' + source['path'])
        lines = data.decode('utf8').splitlines()
        if len(lines) != source['line_count']:
            raise ValueError('line count mismatch: ' + source['path'])
        sources[source['id']] = lines
    for reference in source_map['references']:
        lines = sources[reference['source']]
        start, end = reference['start'], reference['end']
        if not 1 <= start <= end <= len(lines):
            raise ValueError('invalid range: ' + reference['id'])
        data = ('\n'.join(lines[start-1:end]) + '\n').encode('utf8')
        if hashlib.sha256(data).hexdigest() != reference['excerpt_sha256']:
            raise ValueError('excerpt hash mismatch: ' + reference['id'])
        checked += 1
    return {'commit': commit, 'verified_source_files': len(sources),
            'verified_line_references': checked,
            'scope': 'Source identity and citation ranges; not capture or shader correctness'}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--greyhound', type=Path, required=True, help='Existing Greyhound clone')
    parser.add_argument('--source-map', type=Path, default=Path(__file__).resolve().parents[1] / 'evidence/greyhound-source-map.json')
    args = parser.parse_args()
    try:
        result = verify(args.greyhound, json.loads(args.source_map.read_text(encoding='utf8')))
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, 'Source verification failed: ' + str(error) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
