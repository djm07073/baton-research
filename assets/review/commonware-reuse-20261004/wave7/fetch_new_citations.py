"""Fetch introduced primary citations and verify source blobs; no protocol execution."""
from pathlib import Path
import json, re, urllib.request, concurrent.futures, hashlib, datetime, subprocess
BASE = Path(__file__).parent
rows = json.loads((BASE / 'new-citation-inputs.json').read_text())
parsed = {}
for row in rows:
    m = re.fullmatch(r'https://github.com/([^/]+/[^/]+)/blob/([^/]+)/([^#]+)(?:#L(\d+))?', row['url'])
    assert m, row
    repo, pin, path, line = m.groups()
    parsed[row['url']] = (repo, pin, path, int(line) if line else None)
def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Baton-doc-source-review'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()
def tree(key):
    repo, pin = key
    data = subprocess.check_output(['gh', 'api', f'repos/{repo}/git/trees/{pin}?recursive=1'])
    value = json.loads(data)
    assert not value.get('truncated')
    output = BASE / 'citation-sources' / repo.replace('/', '-') / pin / 'tree.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return key, {x['path']: x['sha'] for x in value['tree'] if x['type'] == 'blob'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    trees = dict(pool.map(tree, sorted({x[:2] for x in parsed.values()})))
def source(key):
    repo, pin, path = key
    data = get(f'https://raw.githubusercontent.com/{repo}/{pin}/{path}')
    blob = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
    assert blob == trees[repo, pin][path]
    output = BASE / 'citation-sources' / repo.replace('/', '-') / pin / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return key, {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'git_blob': blob, 'tree_blob': trees[repo, pin][path], 'blob_verified': True, 'lines': data.decode().splitlines(), 'local': str(output)}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    sources = dict(pool.map(source, sorted({x[:3] for x in parsed.values()})))
checks = []
for url, (repo, pin, path, line) in parsed.items():
    value = sources[repo, pin, path]
    assert line is None or 0 < line <= len(value['lines']), url
    checks.append({'url': url, 'line': line, 'line_text': value['lines'][line-1] if line else None, **{k:v for k,v in value.items() if k != 'lines'}})
(BASE / 'new-citation-checks.json').write_text(json.dumps({'retrieved_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'unique_sources': len(sources), 'complete_trees': len(trees), 'citations': checks, 'failures': []}, indent=2) + '\n')
print(json.dumps({'fresh_sources': len(sources), 'checked_citations': len(checks), 'complete_trees': len(trees), 'failures': []}))
