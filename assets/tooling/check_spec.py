"""Check the single Markdown specification and its exported diagrams.

This checks documentation artifacts, not protocol behavior or implementation.
Run after rendering. Optional --source-cache directories contain files arranged
by upstream repository path, from the exact source revision cited in the spec.
"""
import argparse
import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlparse


def heading_ids(markdown):
    ids, seen = set(), {}
    fenced = False
    for line in markdown.splitlines():
        if line.startswith("```"):
            fenced = not fenced
            continue
        match = re.match(r"^#{1,6}\s+(.+)$", line)
        if match and not fenced:
            title = re.sub(r"[`*]", "", match[1]).lower()
            slug = re.sub(r"[^\w\- ]", "", title).replace(" ", "-")
            count = seen.get(slug, 0)
            seen[slug] = count + 1
            ids.add(slug if not count else f"{slug}-{count}")
    return ids


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--source-cache", action="append", type=Path, default=[])
    parser.add_argument("--source-repo-cache", action="append", default=[],
                        metavar="REPOSITORY=DIRECTORY",
                        help="Additional pinned Commonware application source cache")
    args = parser.parse_args()
    repo_caches = {"monorepo": args.source_cache}
    for item in args.source_repo_cache:
        repository, separator, directory = item.partition("=")
        if not separator or not directory:
            parser.error("--source-repo-cache expects REPOSITORY=DIRECTORY")
        repo_caches.setdefault(repository, []).append(Path(directory))
    pins = {"monorepo": "534af0ede48affd35b2111522527547b4cc9bf72",
            "constantinople": "3b6c92e76bf582855615844a4175b8304808f6a9"}
    spec = args.spec.resolve()
    markdown = spec.read_text()
    failures = []
    if len(re.findall(r"^```", markdown, re.M)) % 2:
        failures.append("Unclosed code fence")
    local_count = source_count = source_checked = blank_decisions = 0
    for target in re.findall(r"\]\(([^\s)]+)\)", markdown):
        parsed = urlparse(target)
        if parsed.scheme:
            if parsed.netloc != "github.com" or not parsed.path.startswith("/commonwarexyz/") or "/blob/" not in parsed.path:
                continue
            source_count += 1
            repository = parsed.path.split("/")[2]
            revision, source_path = parsed.path.split("/blob/", 1)[1].split("/", 1)
            if revision != pins.get(repository):
                failures.append(f"Unexpected Commonware revision: {target}")
            caches = repo_caches.get(repository, [])
            if caches:
                candidates = [cache / source_path for cache in caches]
                source = next((p for p in candidates if p.is_file()), None)
                if source is None:
                    failures.append(f"Source not cached: {source_path}")
                    continue
                source_checked += 1
                line = re.fullmatch(r"L(\d+)(?:-L(\d+))?", parsed.fragment)
                if line:
                    size = len(source.read_text().splitlines())
                    if not 1 <= int(line[1]) <= int(line[2] or line[1]) <= size:
                        failures.append(f"Source line outside file: {target}")
            continue
        local_count += 1
        path = (spec.parent / unquote(parsed.path)).resolve() if parsed.path else spec
        if not path.is_file():
            failures.append(f"Missing local target: {target}")
        elif parsed.fragment and path.suffix == ".md":
            if unquote(parsed.fragment) not in heading_ids(path.read_text()):
                failures.append(f"Missing Markdown heading: {target}")
    # A selected policy is an intentional document decision, never a lint fix.
    in_decisions = False
    for line in markdown.splitlines():
        if line.startswith("| 항목 | 결정 |"):
            in_decisions = True
            continue
        if in_decisions and not line.startswith("|"):
            in_decisions = False
        if in_decisions and line.startswith("|") and not line.startswith("|---"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) == 2:
                if cells[1]:
                    failures.append(f"Undecided policy cell was filled: {cells[0]}")
                else:
                    blank_decisions += 1
    blocks = re.findall(r"```mermaid\n([\s\S]*?)\n```", markdown)
    directory = spec.parent / "assets/diagrams"
    manifest_path = directory / "render-manifest.json"
    if not manifest_path.is_file():
        failures.append("Missing diagram render manifest")
    else:
        manifest = json.loads(manifest_path.read_text())
        if manifest["specification_sha256"] != sha(spec.read_bytes()):
            failures.append("Diagram manifest does not match current Markdown")
        if len(manifest["diagrams"]) != len(blocks):
            failures.append("Diagram count differs from Markdown")
        for item, source in zip(manifest["diagrams"], blocks):
            name = item["name"]
            try:
                if item["source_sha256"] != sha(source.encode()):
                    failures.append(f"Stale source hash: {name}")
                if (directory / (name + ".mmd")).read_text() != source + "\n":
                    failures.append(f"Stale exported source: {name}")
                ET.parse(directory / (name + ".svg"))
                png = (directory / (name + ".png")).read_bytes()
                if png[:8] != b"\x89PNG\r\n\x1a\n":
                    failures.append(f"Invalid PNG header: {name}")
                dimensions = struct.unpack(">II", png[16:24])
                if dimensions != (item["width"], item["height"]):
                    failures.append(f"PNG dimensions differ from render: {name}")
            except (OSError, ET.ParseError, ValueError) as error:
                failures.append(f"Diagram artifact error {name}: {error}")
    result = {"specification_sha256": sha(spec.read_bytes()),
              "local_links_checked": local_count,
              "commonware_links": source_count,
              "cached_source_locations_checked": source_checked,
              "blank_policy_decisions": blank_decisions,
              "diagrams": len(blocks), "failures": failures,
              "scope": "Documentation links, structure and exported artifacts only"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(failures))


if __name__ == "__main__":
    main()
