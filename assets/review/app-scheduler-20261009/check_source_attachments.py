"""Exercise standalone documentation attachments in an isolated temporary repository."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[3]
results = []
with tempfile.TemporaryDirectory(prefix="baton-doc-attachments-") as temporary:
    outer = Path(temporary)
    fixture = outer / "repository"
    tooling = fixture / "assets/tooling"
    tooling.mkdir(parents=True)
    for name in ("build_docs.mjs", "docs-style.css", "docs-app.js"):
        shutil.copy2(repo / "assets/tooling" / name, tooling / name)
    docs = fixture / "docs"
    (docs / "assets/diagrams").mkdir(parents=True)
    (docs / "SUMMARY.md").write_text("* [Fixture](README.md)\n")
    (docs / "assets/diagrams/render-manifest.json").write_text('{"diagrams": []}')
    env = dict(os.environ, DOCS_MARKED_MODULE=str(repo / "node_modules/marked/lib/marked.esm.js"))
    def build(markdown):
        (docs / "README.md").write_text("# Fixture\n\n" + markdown)
        return subprocess.run(["node", str(tooling / "build_docs.mjs")], env=env, text=True, capture_output=True)
    (fixture / "notes.md").write_bytes(b"# Source\n\nUnchanged reference bytes.\n")
    (fixture / "unlinked.md").write_text("Must not be copied.")
    run = build("[source](../notes.md) [navigation](SUMMARY.md) [remote](https://example.com/file.md)\n")
    assert run.returncode == 0, run.stderr
    html = (fixture / "site/index.html").read_text()
    assert 'href="repository/notes.md" download title="Download source Markdown"' in html
    assert 'href="index.html"' in html and 'href="https://example.com/file.md"' in html
    assert (fixture / "site/repository/notes.md").read_bytes() == (fixture / "notes.md").read_bytes()
    assert not (fixture / "site/repository/unlinked.md").exists()
    results.append({"case": "linked-only-byte-exact-download-and-existing-links", "passed": True})
    (outer / "outside.md").write_text("External fixture; must not be copied.")
    run = build("[escape](../../outside.md)\n")
    assert run.returncode != 0 and "Link outside repository" in run.stderr
    results.append({"case": "lexical-path-escape-rejected", "passed": True})
    (fixture / "linked.md").symlink_to(outer / "outside.md")
    run = build("[symlink](../linked.md)\n")
    assert run.returncode != 0 and "not a repository file" in run.stderr
    results.append({"case": "symlink-escape-rejected", "passed": True})
    (fixture / "directory.md").mkdir()
    run = build("[directory](../directory.md)\n")
    assert run.returncode != 0 and "not a repository file" in run.stderr
    results.append({"case": "directory-attachment-rejected", "passed": True})
report = {"checked_at": datetime.now(timezone.utc).isoformat(), "cases": results,
          "scope": "Isolated docs builder checks, not protocol or App runtime tests"}
Path(__file__).with_name("source-attachments-latest.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
