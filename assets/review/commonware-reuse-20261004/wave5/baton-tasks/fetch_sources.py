"""Fetch documentation audit sources; verify against the complete pinned Git tree."""
import concurrent.futures
import datetime
import hashlib
import json
import urllib.request
from pathlib import Path

BASE = Path(__file__).parent
REPO = "commonwarexyz/monorepo"
PIN = "534af0ede48affd35b2111522527547b4cc9bf72"
PATHS = [
    "runtime/src/lib.rs", "runtime/src/tokio/mod.rs", "runtime/src/tokio/runtime.rs",
    "utils/src/futures.rs", "parallel/src/lib.rs", "parallel/src/policy.rs",
    "macros/src/lib.rs", "actor/src/lib.rs",
    "consensus/src/multimmit/actors/voter/executor.rs",
    "runtime/src/utils/handle.rs", "runtime/src/utils/supervision.rs",
]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Baton-task-source-audit"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()

tree_bytes = get(f"https://api.github.com/repos/{REPO}/git/trees/{PIN}?recursive=1")
(BASE / "native-tree.json").write_bytes(tree_bytes)
tree = json.loads(tree_bytes)
assert not tree.get("truncated")
blobs = {row["path"]: row["sha"] for row in tree["tree"] if row["type"] == "blob"}

def fetch(path):
    url = f"https://raw.githubusercontent.com/{REPO}/{PIN}/{path}"
    payload = get(url)
    blob = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
    assert blob == blobs[path], path
    destination = BASE / "sources" / "native" / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return {"repo": REPO, "pin": PIN, "path": path, "url": url,
            "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
            "git_blob": blob, "tree_blob": blobs[path], "git_blob_verified": True}

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    sources = list(executor.map(fetch, PATHS))
(BASE / "source-manifest.json").write_text(json.dumps({
    "fetched_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "sources": sources}, indent=2) + "\n")
print(f"Verified {len(sources)} fresh pinned source files")
