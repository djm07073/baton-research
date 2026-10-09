"""Check current native link targets and excerpt signatures locally, without compiling."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess


REVIEW = Path(__file__).resolve().parent
RESEARCH = REVIEW.parents[2]
NATIVE = RESEARCH.parent
COMMIT = '6233438985d8249d2b2bc1204191d5d405652288'
BASE = f'https://github.com/0xEyrie/monorepo/blob/{COMMIT}/'


def git(*args):
    return subprocess.check_output(['git', '-C', str(NATIVE), *args])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalize(text):
    return re.sub(r'\s+', '', re.sub(r'(?m)^\s*//[^\n]*', '', text))


def main():
    failures, references, sources = [], [], {}
    head = git('rev-parse', 'HEAD').decode().strip()
    if head != COMMIT:
        failures.append('Native HEAD differs from the documented integration commit')
    pattern = re.compile(re.escape(BASE) + r'([^\s)#]+)(?:#(L\d+(?:-L\d+)?))?')
    for page in sorted((RESEARCH / 'docs').rglob('*.md')):
        for line, text in enumerate(page.read_text().splitlines(), 1):
            for match in pattern.finditer(text):
                source, fragment = match.groups()
                path = PurePosixPath(source)
                if path.is_absolute() or '..' in path.parts:
                    failures.append(f'Invalid native source path: {source}')
                    continue
                if source not in sources:
                    blob = git('show', f'{COMMIT}:{source}')
                    local = (NATIVE / source).read_bytes()
                    sources[source] = {
                        'lines': len(blob.splitlines()),
                        'pinned_sha256': digest(blob),
                        'working_sha256': digest(local),
                        'matches_pin': blob == local,
                    }
                    if blob != local:
                        failures.append(f'Working source differs from pin: {source}')
                bounds = [int(n) for n in re.findall(r'\d+', fragment or '')]
                valid = all(1 <= n <= sources[source]['lines'] for n in bounds)
                if not valid:
                    failures.append(f'Out-of-bounds source anchor: {source}#{fragment}')
                references.append({'page': str(page.relative_to(RESEARCH)),
                                   'line': line, 'source': source,
                                   'fragment': fragment, 'valid_bounds': valid})

    exported = (RESEARCH / 'docs/assets/interfaces/baton.rs').read_text()
    bindings = {
        'propose': 'consensus/src/lib.rs',
        'verify': 'consensus/src/lib.rs',
        'report': 'consensus/src/lib.rs',
        'broadcast': 'consensus/src/lib.rs',
        'stage_block': 'consensus/src/multimmit/marshal/mailbox.rs',
        'put_block': 'consensus/src/multimmit/marshal/mailbox.rs',
        'Update': 'consensus/src/multimmit/marshal/types.rs',
    }
    declarations = []
    for name, source in bindings.items():
        blob = git('show', f'{COMMIT}:{source}').decode()
        if name == 'Update':
            expression = r'pub struct Update<B: Block>\s*\{[^}]+\}'
        else:
            expression = rf'(?m)^\s*(?:pub\s+)?(?:async\s+)?fn {name}\([^;{{]+(?=[;{{])'
        actual = re.search(expression, blob)
        excerpt = re.search(expression, exported)
        matches = bool(actual and excerpt and normalize(actual[0]) == normalize(excerpt[0]))
        declarations.append({'name': name, 'source': source,
                             'line': blob[:actual.start()].count('\n') + 1 if actual else None,
                             'matches_ignoring_whitespace_and_comments': matches})
        if not matches:
            failures.append(f'API excerpt differs: {name}')

    result = {
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'native_commit': COMMIT, 'native_head': head,
        'references': references, 'sources': sources,
        'excerpt_sha256': digest(exported.encode()), 'declarations': declarations,
        'failures': failures,
        'scope': 'Local current-pin file/line/blob and signature checks only; no semantic proof, remote URL check, Rust compilation or App/runtime test',
    }
    (REVIEW / 'native-source-targets-latest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'references': len(references), 'source_files': len(sources),
                      'declarations': len(declarations), 'failures': failures}, indent=2))
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
