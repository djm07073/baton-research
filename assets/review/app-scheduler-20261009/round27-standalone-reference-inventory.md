# Round 27: standalone preview reference inventory

## Read-only scope

Inspected current `assets/tooling/build_docs.mjs`, all Markdown links under `docs/`, the three directly linked repository artifacts and their local-reference graph. Only this report is written by this reviewer. Root owns failure reproduction, builder/checker changes and browser verification; no source/core/builder edit or standalone-browser success is claimed here.

The inspected builder copies `docs/assets` to `site/assets` and rewrites `.md` targets only when they are a listed content page. Repository artifacts outside `docs/` therefore retain paths based on the repository layout instead of the generated site layout. Their on-disk existence satisfies the Markdown link checker but does not establish reachability from a standalone `site/` HTTP root.

## Direct inventory

Exactly **five links target three files outside `docs/`**. All targets are regular existing Markdown files inside `baton-research`; none is a symlink, and none of these five URLs has a fragment or query.

| Source page / line | Repository target | Bytes |
|---|---|---|
| `docs/execution/qmdb.md:5` | `assets/review/commonware-reuse-20261004/README.md` | 16,536 |
| `docs/reference/integration.md:125` | `assets/review/commonware-reuse-20261004/README.md` | 16,536 |
| `docs/reference/sources.md:11` | `baton-paper.md` | 60,575 |
| `docs/reference/sources.md:12` | `assets/review/app-scheduler-20261009/native-audit.md` | 9,091 |
| `docs/reference/sources.md:13` | `assets/review/commonware-reuse-20261004/README.md` | 16,536 |

These are research/source artifacts, not missing pages in the current 32-page implementation navigation. The source page already distinguishes the current audit from historical paper/reuse evidence.

## Smallest complete mapping

Copy only those three exact referenced files into a dedicated namespace such as `site/references/<repository-relative-path>`, and rewrite generated page hrefs relative to the generated page destination. For example, `site/reference/sources.html` can reach `../references/baton-paper.md`. Keeping the repository-relative suffix avoids collisions between the two review files named README and any future artifacts with the same basename. This mapping does not require changing canonical Markdown paths.

Present them explicitly as original reference/source artifacts or downloads. A byte-exact raw Markdown reference is an honest bounded offering; it should not appear to be a rendered continuation of the implementation navigation. There is no fragment requirement for the current five links. Do not claim a complete browsable historical archive from this three-file fix.

If root instead chooses HTML rendering, the implementation must decide how to handle the reference pages' own links. Rendering only these three files while leaving their inner relative links clickable reproduces the same failure one click later.

## Why not recursively publish the historical archive here

| Direct artifact | Its local links | Distinct targets |
|---|---:|---:|
| `baton-paper.md` | 2 | 1 compatibility entry |
| Earlier reuse review index | 84 | 84 files: 63 Markdown, 21 JSON |
| Current native audit | 2 | 2 Markdown reports |

Following local Markdown links transitively reaches **253 existing non-doc files**, totalling **4,278,368 bytes** in this snapshot: 164 Markdown, 67 JSON, 18 SVG, 2 text and 2 Rust files. It also reaches 31 current-doc backlinks and three directory links (`wave2/pool/sources`, `wave4/pool-builder/sources`, `wave5/pool-source/sources`). All resolved paths remain within the repository; those directories are not copyable as single linked files. None of the direct artifact Markdown contains Mermaid blocks.

That larger graph is unnecessary for repairing the five current navigation links. Avoid copying the repository or whole assets/review tree merely to make the server expose paths; generated `site/` should remain a bounded documentation artifact, not a repository root server.

## Path and reader checks for the owning implementation

- Classify URL schemes before filesystem resolution. Preserve HTTPS and other existing external links; handle local paths using their source Markdown directory, not the generated HTML directory.
- Resolve/decode the local source path once and require containment within the research repository. For copy inputs, use actual regular files and account for symlink resolution; reject escape outside the repository rather than copying unrelated workspace files.
- Derive a normalized repository-relative destination under the dedicated reference namespace and verify output containment. Never concatenate a raw `../../` URL directly into the copy destination.
- Preserve exact bytes and verify copied file hashes. Escape rewritten hrefs using the builder's existing HTML handling. Do not rewrite GitHub citations to uncommitted local content or change the native source pin.
- Preserve fragments if later supported, or reject unsupported artifact-fragment combinations visibly during build. The current targets need neither anchors nor Markdown fragment generation.
- Check actual rendered href targets from an HTTP server whose document root is only `site/`; source-file existence alone misses this defect. Confirm the original body/audit text is available and the browser behavior is clear for source artifacts.

## Snapshot hashes

| Artifact | SHA-256 |
|---|---|
| `baton-paper.md` | `73030de6f907c59c5f16baa4388f3f46f167efb6af8940da94fc4165260cdf0c` |
| Earlier reuse review README | `6ac4236755bd88c81890888d0265748cedd1297796cdc44bb936ef7fd5df0cae` |
| Current native audit | `6d131a1b579f84659fe39b59f547822c4f35b048597304d45908ce0559e0df18` |

Disposition: the direct reference scope is small and fully inventoried. A bounded copy/rewrite can fix it without changing documentation contracts, implementing a new archive renderer, or modifying preserved historical research.

## Independent review of root's applied fix

Read the actual builder diff after root implemented the fix. The implementation uses `site/repository/<repoRelative>` rather than this report's illustrative `references/` name; both have the required isolated namespace. The actual patch passes this review for the current link set:

- Current navigation and SUMMARY targets are rewritten before attachment handling, so no current content page becomes a download.
- The attachment Map deduplicates the three source files. Repository-relative paths preserve original subdirectories and avoid basename collisions.
- Lexical source containment is checked first; `realpath` containment and regular-file validation run before copying. The derived destination is beneath `site/repository`, with no unresolved parent traversal.
- Only direct source Markdown files are copied. Their inner archive graph is deliberately not rendered or advertised as a standalone HTML archive.
- The generated hrefs have the `download` attribute and `title="Download source Markdown"`, making the artifact behavior explicit.

I inspected the freshly generated `site/reference/sources.html`, `site/reference/integration.html` and `site/execution/qmdb.html`: all five expected hrefs point to `../repository/...` with those attributes. I read all three generated files and compared their complete bytes and SHA-256 to the originals; all match the snapshot hashes above. The reviewed builder SHA-256 is `953171ace14315b7098e82201c42ac26520203a7b7744de6a7731102c336879c`.

This remains a focused fix for the current normal relative URLs. It does not claim support for rendering arbitrary repository Markdown, artifact fragments, or URL-encoded future attachment names. None of those is required by the inventoried links.

## Browser evidence and its precise scope

Read root's preserved `browser/snapshot-093501-local-links-failed/verification.json`. It records the three expected unique 404s: `/baton-paper.md`, `/assets/review/app-scheduler-20261009/native-audit.md`, and `/assets/review/commonware-reuse-20261004/README.md`; the last has three source pages. This is an observed standalone HTTP failure, not merely inferred source-link breakage.

Also read the expanded `browser/check.cjs`. It serves only generated `site/`, loads all 32 navigation pages, decodes article images, checks navigation counts, and fetches every unique same-origin article-link URL over HTTP. It removes fragments for that HTTP check. Source Markdown anchor validation remains the separate docs check. Search behavior, mobile menu and selected desktop/mobile screenshots remain covered by the same browser run.

I did not run a second competing browser session or claim the pending root pass as my own. Root owns the post-fix HTTP/browser result and the actual three-hour completion. The independent diff, generated hrefs and byte-exact attachment checks reveal no further correction needed.
