"""Validate documentation navigation, local links and rendered diagrams.

--migration also checks the one-time split against its preserved snapshot.
These checks do not execute or validate the Baton protocol.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET
from check_spec import heading_ids


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--migration', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    docs = repo / 'docs'
    summary = (docs / 'SUMMARY.md').read_text()
    listed = re.findall(r'^\* \[.+\]\((.+\.md)\)$', summary, re.M)
    failures = []
    actual = {p.relative_to(docs).as_posix() for p in docs.rglob('*.md')} - {'SUMMARY.md'}
    if set(listed) != actual or len(listed) != len(set(listed)):
        failures.append('SUMMARY must list every content page exactly once')
    texts = {p: p.read_text() for p in docs.rglob('*.md')}
    texts[repo / 'IMPLEMENTATION_SPEC.md'] = (repo / 'IMPLEMENTATION_SPEC.md').read_text()
    local_links = decisions = 0
    for page, text in texts.items():
        if len(re.findall(r'^```', text, re.M)) % 2:
            failures.append(f'Unclosed fence: {page.relative_to(repo)}')
        for target in re.findall(r'\]\(([^\s)]+)\)', text):
            parsed = urlparse(target)
            if parsed.scheme:
                continue
            local_links += 1
            dest = (page.parent / unquote(parsed.path)).resolve() if parsed.path else page
            if not dest.is_file():
                failures.append(f'Missing link from {page.relative_to(repo)}: {target}')
            elif parsed.fragment and dest.suffix == '.md':
                markdown = dest.read_text()
                ids = heading_ids(markdown) | set(re.findall(r'<a id="([^"]+)"', markdown))
                if unquote(parsed.fragment) not in ids:
                    failures.append(f'Missing anchor from {page.relative_to(repo)}: {target}')
        in_decisions = False
        for line in text.splitlines():
            if line.startswith(('| 항목 | 결정 |', '| Item | Decision |')):
                in_decisions = True
                continue
            if not line.startswith('|'):
                in_decisions = False
            if in_decisions and line.startswith('|') and not line.startswith('|---'):
                cells = [cell.strip() for cell in line.strip('|').split('|')]
                if len(cells) == 2:
                    if cells[1]:
                        failures.append(f'Undecided policy was filled: {cells[0]}')
                    else:
                        decisions += 1
    directory = docs / 'assets/diagrams'
    rust_page = (docs / 'overview/rust-interfaces.md').read_text()
    declarations = re.findall(r'```rust,ignore\n([\s\S]*?)\n```', rust_page)
    exported = (docs / 'assets/interfaces/baton.rs').read_text()
    expected = ('// @generated from docs/overview/rust-interfaces.md; edit that Markdown source.\n'
                '// Existing Commonware API excerpts; not standalone declarations or protocol implementation.\n\n'
                + '\n\n'.join(declarations) + '\n')
    if exported != expected:
        failures.append('Stale Rust export; run npm run docs:interfaces')
    manifest = json.loads((directory / 'render-manifest.json').read_text())
    blocks = [source for p, text in texts.items() if p != repo / 'IMPLEMENTATION_SPEC.md'
              for source in re.findall(r'```mermaid\n([\s\S]*?)\n```', text)]
    if Counter(sha(b.encode()) for b in blocks) != Counter(d['source_sha256'] for d in manifest['diagrams']):
        failures.append('Page Mermaid sources differ from rendered diagram manifest; render changed sources before delivery')
    for item in manifest['diagrams']:
        name = item['name']
        try:
            if sha((directory / f'{name}.mmd').read_bytes().rstrip(b'\n')) != item['source_sha256']:
                failures.append(f'Stale Mermaid asset: {name}')
            ET.parse(directory / f'{name}.svg')
            png = (directory / f'{name}.png').read_bytes()
            if png[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('>II', png[16:24]) != (item['width'], item['height']):
                failures.append(f'Invalid PNG dimensions: {name}')
        except (OSError, ET.ParseError) as error:
            failures.append(f'Invalid diagram {name}: {error}')
    if args.migration:
        record = json.loads((repo / 'assets/tooling/docs-migration.json').read_text())
        original = repo / record['original_archive']
        if sha(original.read_bytes()) != record['original_spec_sha256']:
            failures.append('Original snapshot changed')
        ids = [section for page in record['pages'] for section in page['original_sections']]
        original_ids = re.findall(r'^### (\d+\.\d+) ', original.read_text(), re.M) + ['8']
        if Counter(ids) != Counter(original_ids) or len(ids) != len(set(ids)):
            failures.append('Original sections must be mapped exactly once')
        current = '\n'.join((docs / page['path']).read_text() for page in record['pages'])
        citations = lambda text: Counter(t for t in re.findall(r'\]\(([^\s)]+)\)', text) if urlparse(t).scheme)
        if citations(original.read_text()) - citations(current):
            failures.append('Original external citation occurrences missing after migration')
        if decisions != 39:
            failures.append(f'Expected 39 preserved blank policy cells, got {decisions}')
        legacy_ids = heading_ids(original.read_text())
        # Chapters and subsections are compatibility anchors; the old H1 also
        # remains readable through the root file, without a second editable spec.
        required = {anchor for anchor in legacy_ids if re.match(r'^\d', anchor)}
        anchors = set(re.findall(r'<a id="([^"]+)"', texts[repo / 'IMPLEMENTATION_SPEC.md']))
        if not required.issubset(anchors):
            failures.append(f'Missing legacy anchors: {sorted(required - anchors)}')
        if manifest.get('origin_snapshot_sha256', manifest['specification_sha256']) != record['original_spec_sha256']:
            failures.append('Diagram provenance does not match the original snapshot')
    print(json.dumps({'content_pages': len(listed), 'local_links_checked': local_links,
                      'rendered_diagrams': len(blocks), 'blank_policy_cells': decisions,
                      'migration_checked': args.migration, 'failures': failures}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
