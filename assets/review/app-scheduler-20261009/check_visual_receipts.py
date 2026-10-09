"""Bind current diagram bytes to the team's actual visual-review receipts."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def main():
    review = Path(__file__).resolve().parent
    diagrams = review.parents[2] / 'docs/assets/diagrams'
    groups = {
        'round25-root-architecture-visual.md': [1],
        'round25-final-png-qa.md': [2, 3, 6, 7, 10, 11, 12, 13, 14],
        'round25-native-visual-qa.md': [4, 5, 15, 16],
        'round23-final-app-pngs.md': [8, 9, 17, 18, 19],
    }
    rows, failures = [], []
    for report, numbers in groups.items():
        receipt = (review / report).read_text()
        for number in numbers:
            name = f'diagram-{number:02d}'
            hashes = {extension: hashlib.sha256((diagrams / (name + extension)).read_bytes()).hexdigest()
                      for extension in ('.mmd', '.png', '.svg')}
            covered = all(hashes[extension] in receipt for extension in ('.mmd', '.png'))
            if not covered:
                failures.append(f'Current source/PNG no longer matches visual receipt: {name}')
            rows.append({'name': name, 'report': report, 'sha256': hashes,
                         'source_and_png_match_receipt': covered,
                         'pixel_review': 'Recent Round21 view reused after identical-byte check'
                         if number in (6, 12) else 'Direct image-tool view in named report'})
    if sorted(row['name'] for row in rows) != [f'diagram-{n:02d}' for n in range(1, 20)]:
        failures.append('Visual receipt coverage is not exactly diagrams01-19')
    result = {
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'diagrams': sorted(rows, key=lambda row: row['name']), 'failures': failures,
        'scope': 'Byte identity with actual human-readable image-review records; this script does not itself inspect pixels or prove protocol behavior. SVG hashes record current companions, not separate pixel reviews.',
    }
    (review / 'visual-receipt-bindings-latest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'diagrams': len(rows), 'failures': failures}, indent=2))
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
