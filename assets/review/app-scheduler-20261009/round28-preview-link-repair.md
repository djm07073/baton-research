# Standalone preview reference repair

The expanded browser checker first reproduced three distinct HTTP 404s in the built site. The five affected reader links all point outside docs/ to three Markdown artifacts: the research paper, historical reuse review index and current native audit. The Markdown source links were valid on disk; the site builder omitted those files. The preserved failed browser receipt is in `browser/snapshot-093501-local-links-failed/verification.json`.

The builder now keeps navigation/SUMMARY rewrites and copies only directly linked source Markdown files into `site/repository/<repository-relative-path>`. Download attributes label these as source artifacts. It does not render a second archive, copy the whole repository, or promise that downloaded files' nested links resolve independently. Both lexical and resolved filesystem paths must stay inside the repository, and each attachment must be a regular file. The three copied files are byte-exact; the independent Round27 inventory records their hashes.

Verification:

- Fresh build: 32 pages, 19 diagrams, 3 source attachments.
- Expanded browser run: 32 pages, 19 decoded images, 54 unique local article HTTP targets and 24 linked HTML fragment IDs; no failures. Search and mobile menu passed.
- Isolated builder fixtures: byte-exact linked-only copying and existing navigation/external link behavior; lexical escape rejected; symlink escape rejected; directory attachment rejected. See `check_source_attachments.py` and `source-attachments-latest.json`.
- Root directly inspected the fresh desktop App entry and mobile callbacks screenshots after the successful browser run. Neither showed clipping or a misleading component boundary. Other screenshots are not automatically claimed as newly pixel-reviewed.

This is documentation tooling validation, not execution or testing of the proposed App or native protocol. It does not complete the requested three-hour interval before 09:57:26 UTC.

A later browser pass additionally completed all three source downloads and compared their bytes with the originals. It records source/HTML hashes for all 32 checked pages, allowing the final snapshot to verify that the checked build and reader bytes have not changed. This later receipt remains timestamped in `browser/verification.json`; the earlier fragment/HTTP run is preserved in the pre-download-check snapshot.
