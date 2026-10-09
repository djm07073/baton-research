# Round 3: visual E2E and navigation audit

Inspected the actual rendered PNGs `diagram-02.png` through `diagram-15.png` with `view_image`, not only Mermaid parse results. Reviewed all participant labels, branch frames, arrow endpoints, message sequencing, completion notes and their corresponding current E2E Markdown. No clipped text, unreadable overlap or missing arrows was observed in the first rendered set.

The table hashes identify the images actually inspected. Three targeted source corrections are made and await replacement rendering/readback; this is not yet a claim that their corrected pixels have passed visual review.

| Diagram | Inspected size | PNG SHA-256 | Visual and semantic review |
|---|---|---|---|
| 02 | 1340×2291 | `be90be3065c5d396cc0e461d8af9de7516ba5004d0be15ef727c03acb7f81f85` | Readable six-participant end-to-end path; custody, execution and ACK arrows remain distinct. Tall overview is linked to its full-size SVG. |
| 03 | 903×1335 | `219d554ce6b428a779112236bc44a0805d1327f2d72eb842dd29ebd3d98ec402` | Admission alternatives and later pool maintenance fit without clipping; selected/unselected remain internal App states. |
| 04 | 1318×1301 | `97bdc6154c266cdb6654d21c675bf3b6c55a936db5928090506e72acca8a2c58` | Found native-header arrow ending at Peer Marshal; source now uses Peer node. Shortened the awkwardly wrapped complete-block constructor label. Replacement render pending. |
| 05 | 936×1722 | `e34510aa31f1a300eb8db78b9a5e89e97767dbfd91a69ee0b32c4596e5852e50` | Nested unavailable/invalid/valid paths are readable; true reply precedes optional dispatch and does not await execution. |
| 06 | 907×1508 | `2019a880e18a93dedfe19fcb0dff00af34b2d6ec582d6b40f16671e179f8a3d0` | Parallel native cut and report/planning branches are explicit; count/deadline and no direction-ACK notes are visible. |
| 07 | 930×1434 | `efb0ce1d761f287210f27c830202e6d750a05789d496e71221a5e337c693679d` | Context rejection, unresolved advisory conflict, missing input and dispatch branches are visually distinct; no canonical rollback is shown. |
| 08 | 1115×2227 | `560747136128377a46d7bd4bcb6121273d6299af45611cf1bc368d072e155e17` | Readable but unnecessarily tall nested self-only result branches. Source now combines exact reuse/import/repair and explicit worker fence. Replacement render pending. |
| 09 | 711×1674 | `30414f7591bd62b34a2102739d8e0606e7e5c5cfa692c1f92d87ba3d44e6afbd` | Execution effects, selected-root preparation, durable application and retention are ordered correctly; failure retains no successful ACK claim. |
| 10 | 899×1371 | `5ab354711f76300753f510245833d479326e6826a80f35256d075d9de9d9deda` | Replay compares exact applied identity, ACKs matching durable work and stops on gaps/conflicts; cursor step says acknowledged continuous prefix. |
| 11 | 919×1524 | `04769dca2c40f512eb6176ba81b48d7a119d839ae502212e70b8dc351386b6b8` | Selected commitment precedes signing; result acceptance checks f+1 full-subject signatures and irrevocable input-state linkage; imported-provenance note visible. |
| 12 | 899×1668 | `853af34ec0cfd311b10e138d01e7017226a682ef96524c22bb15da546aff48d0` | Actual-parent recheck, authenticated freeze and late-result immutability are clear. Page explicitly marks native policy integration as future work. |
| 13 | 1116×1459 | `f6398111bfad969bbdfb1a0ddace1c5d164a367ef7d8db2d3e3680f0567bdb0e` | Marshal/App access precedes Engine::open recovery verify, then start and Running::ready. All arrows and multiline labels fit. |
| 14 | 902×2067 | `aff9c356984bc9ae6b42a097d7db1fe4b24a6894cda7e05c9f7618c1f5acba92` | Certificate plus applicable material precedes worker fence/import; durable completion precedes ACK; failure/imported-provenance paths are visible. |
| 15 | 1359×1542 | `4ad57d548327a9ff26aacb2120f2c897034d59971da2bd6fe877b2fce0a783f3` | Found possible false DA-certificate-before-proposal barrier and leader-only vote impression. Added independent-progress/native-eligibility note and broadcast-vote wording in source. Replacement render pending. |

## Changes required by the visual review

- **04 / `e2e/block-body.md`:** the native signed-header arrow must terminate at a peer native endpoint. Using aggregate `Peer node` allows both independent channels without implying Marshal receives native data messages. The complete-block build label now fits a plain-language diagram without a wrapped Rust identifier.
- **08 / `e2e/canonical.md`:** combine three self-only branches into “Reuse exact work, verify import, or execute / repair.” Preserve exact index/block/predecessor check, incompatible-worker fencing, durable state/output/applied-identity linkage, ACK and Marshal cursor persistence. Detailed alternatives remain in prose and core callback pseudocode.
- **15 / `e2e/native-consensus.md`:** clarify that DA certificate assembly and leader proposal progress are independent while native eligibility still applies. Label votes as broadcast to peers so the selected receiving view-owner lifeline is not mistaken for a leader-only aggregation protocol.

Sources and embedded Mermaid are synchronized for 04/08/15. Root owns the targeted render and global manifest update.

## Navigation and reader-claim review

The local reading route is docs README → Baton integration → callback behavior → scheduling. Architecture, Rust API excerpts and E2E pages support that route. All nine E2E pages remain in SUMMARY. Each reviewed embedded diagram has its matching full-size SVG link; long sequences remain readable through that link rather than forcing a screenshot-width view.

The pages now distinguish existing Engine/Marshal functionality from proposed App execution and incomplete Baton native policy integration. The leader page explicitly labels its second sequence as required future integration. The result/state-sync pages preserve exact input/base/runtime identity and direct/imported provenance. Canonical/recovery prose separately covers floor-reset overlap and the absence of an Update generation field; the normal diagrams depict ordinary delivery rather than inventing a generation property.

These are document/visual checks. No protocol execution, benchmark or live network behavior was tested.

## Replacement-pixel verification

Viewed the actual replacement PNGs 04, 08 and 15 after root's targeted render. All three pass visual and semantic readback: peer-node endpoint is correct, the canonical flow is shorter without dropping exact-parent or durability gates, and native independent progress/broadcast recipients are explicit. No clipped labels, overlapping text or hidden arrowheads were observed.

| Diagram | Replacement size | Verified PNG SHA-256 | Result |
|---|---|---|---|
| 04 | 1318×1284 | `fc1ed94a16226ad9a8ebe5bfc40dd9af8f92d6d8c23c86fdc707fe4ff4abcf25` | Pass |
| 08 | 1115×1885 | `333708dff1f35f45f398bf6c2316830485f24629262cdd4f24f2ab9054ecbed7` | Pass |
| 15 | 1359×1599 | `a87e3ea2e862b1925567feb073ad81fbc27a4f1c6d2af591961714e89a146772` | Pass |

The earlier table intentionally records the first inspected image set; this replacement table supersedes only its 04/08/15 pending statuses. All 14 assigned E2E diagrams now have direct visual readback. Root separately reported successful docs check/build/diff checks; this reviewer does not substitute those automated results for the pixel and semantic inspection above.

## Suggested next independent review

Exercise adversarial App event traces rather than repeating rendering: a successful verify finishes after the same block is already applied; a local propose is canceled after staging; native parent validation fails while a child body verify succeeds; an import/floor transition overlaps retained Updates and a late speculative worker. For each trace identify the existing owner, exact identity check, retained work, ACK eligibility and restart behavior. The goal is to expose a missing concrete handoff or needless extra layer without choosing still-open policy defaults or writing protocol implementation.
