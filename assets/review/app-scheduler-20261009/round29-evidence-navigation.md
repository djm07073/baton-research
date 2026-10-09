# Round 29: evidence navigation and scope audit

## Status and scope

Reviewed the latest review README, run record, standalone-preview repair report, browser checker/receipt, attachment fixture code/receipt, source and visual-binding receipts. This is an intermediate evidence audit before 09:57:26 UTC; no overall completion receipt is created or implied. No core, tooling or historical source was edited by this reviewer.

All **94 local links** in the review README resolved to existing files, with no missing Markdown fragments. There were 94 distinct targets before the correction below; after replacing the mutable browser link with the already-linked checkpoint, readback checked 94 occurrences / 93 distinct targets again with zero failures. The final evidence reading path is usable: review README → time-scoped checkpoint/run record → named independent review or machine receipt → preserved failure/pass evidence and source artifacts.

## Time and counts

The run records start `2026-10-09 06:57:26 UTC`, minimum end `2026-10-09 09:57:26 UTC`, and status `active`. The README explicitly calls its 09:40 section a checkpoint and keeps final completion conditional on reaching that minimum time and recording the final audit.

| Evidence | Recorded time / contents | README consistency |
|---|---|---|
| Latest browser | 09:36:31 UTC; 32 pages, 54 unique local article HTTP targets, 19 decoded article images, 24 linked HTML fragment IDs, search and mobile menu, zero failures | Matches the 09:40 claims. |
| Attachment fixtures | 09:37:29 UTC; four passed isolated builder cases | Matches exact copying/minimal scope, lexical escape, symlink escape and directory rejection claims. |
| Native source check | 09:37:51 UTC; 121 references, 59 source files, seven declarations, zero failures | Correctly described as pinned local source/target binding, not remote or runtime verification. |
| Visual receipt binding | 09:37:52 UTC; 19 diagram bindings, zero failures | Correctly distinguishes hash binding from the separate actual pixel-review reports. |
| Run checkpoint | 09:40:25 UTC | Follows the checks it summarizes; does not predate its evidence. |

The browser checker now verifies fragment IDs in fetched HTML documents, in addition to HTTP reachability. It does not recursively navigate downloaded Markdown or fetch external sources. The 24-fragment count is the sum of fragment sets recorded for the 54 unique targets, not an invented page count. Screenshot existence is not generalized to pixel review: root names the desktop App entry/mobile callbacks it actually inspected, while other image-review reports retain their own scope.

The fixture script genuinely builds an isolated temporary repository and checks exact linked bytes, absence of an unlinked copy, unchanged external/navigation behavior and the three rejection cases. Its receipt does not claim protocol/App runtime tests.

## One evidence-link clarification

The 07:27 checkpoint paragraph linked mutable `browser/verification.json` as its browser evidence, but that file now contains the 09:36:31 run. There is no preserved raw 07:27 browser receipt in the snapshot directories. `checkpoint-0727.json` does retain the earlier scoped browser summary and notes that diagram19 changed afterward and was independently viewed/rebuilt.

Recommended root-only wording: “The browser check summarized in [checkpoint evidence](checkpoint-0727.json) loaded 32 pages and 19 diagrams and exercised search/mobile navigation.” Leave the latest browser link in the latest section or browser index. This avoids presenting a later mutable receipt as an earlier immutable one without inventing missing evidence. Root was notified; the checkpoint data itself should remain unchanged.

Root applied that correction. I reread it: the section now cites the checkpoint summary and explicitly states that the original raw receipt was not preserved and the latest mutable file describes a later run.

## Current-reader and historical preservation

- Compared all paths in the Round26 reader snapshot to current bytes. Only two reader files differ: `docs/consensus/block-body.md` and `docs/baton/interfaces.md`, matching the later explicitly recorded body-heading/callback-detail-link simplifications. They are not changes made by the preview builder fix.
- The preview correction changes generated artifact handling and validation evidence; it does not rewrite canonical reader Markdown or the three copied source documents.
- The current paper, historical reuse review and current native audit still match the complete byte hashes independently recorded in Round27. Their downloaded copies match their sources.
- A baseline Git diff across the paper, all archive paths and all preexisting review paths outside this task's new review directory is empty. Historical paper/archive/publication/reuse records remain unchanged.

No other time, link, count or validation-scope inconsistency was found. The requested three-hour interval remains active; final completion and the final bound receipt belong to root after the deadline.

## Final-audit draft readback

Read root's `final-audit.md` draft and checked all 12 local links, with zero failures. Its status and last requirement still correctly say the interval/final snapshot are pending, and its evidence counts and limitations match the recorded checks. Suggested one precision change in its Update row: “schedule pool maintenance and ACK” rather than “maintain pool and ACK,” to preserve the core contract that pool-processing completion is not an extra ACK gate. This suggestion changes neither the protocol design nor the currently valid callback page.
