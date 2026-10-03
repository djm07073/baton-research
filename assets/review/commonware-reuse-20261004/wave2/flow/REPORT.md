# Independent current-document flow and Mermaid review — wave 2

Reviewer: `/root/reuse_flow_review_v2`. Canonical repository: `/Users/leojin/Documents/Codex/2026-09-30/task/overpass-research`. Only this REPORT.md was written by this reviewer. No reader page, render, interface export, protocol source, GitBook page or commit was changed.

Review snapshot ended: 2026-10-03T20:11:09.809366+00:00. Git HEAD: `38f64555e27fb88feb2a1f4be6ae2c133c6082e7`. The working tree contains concurrent root edits; hashes below identify the actual reviewed bytes, rather than assuming HEAD contains them.

## Verdict

The current inline Mermaid and detailed execution/storage pages are coherent on the major safety and ownership requirements. Executor computes completed unsealed effects and manages the logical execution tree, certification and active-validator peer sync. Storage prepares selected roots and owns canonical mutation, queries, durability, physical retention and recovery. Root preparation precedes full-result signing without compulsory hashing on every attempt. Direct/imported provenance, actual ancestor applicability, clone-wide fences, no-wait cut behavior and pending/invalid/custody distinctions remain explicit.

Three local wording corrections should precede publication. The first two are definite cross-page ownership contradictions. The third removes remnants of the eliminated extra body interface. An additional small diagram API precision correction is recommended. These are documentation findings, not claims of a runnable adapter or protocol defect. No new Bank, root, signing-boundary, continuation or other policy was adopted.

Root has announced render regeneration. Existing full-size `.mmd`/SVG/PNG assets were still old during this audit; their mismatch is tracked as pending work, not a newly discovered design failure. This review assesses current inline diagram sources, and does not approve the final rendered/publication snapshot.

## Required local corrections

### F1 — P2: leader introduction still asks Executor to choose direction

Location: `docs/e2e/leader.md:3`.

Current wording: “asks Executor to choose a valid direction”. This directly contradicts the same page's Baton planning lifeline, `docs/baton/direction.md:7–9`, and the canonical `Baton::plan` contract in `docs/overview/rust-interfaces.md:156–184`. Direction candidate selection is Baton-owned. The Executor has no plan method.

Correction: “It closes a report window, evaluates a valid direction through Baton::plan, and disseminates the result.” Keep the following native proposal-freeze sentence. No diagram/control-path change is needed.

### F2 — P2: interface guide and Baton module retain the old canonical writer owner

Locations: `docs/overview/interfaces.md:35` says “Executor::commit owns canonical mutation”; `docs/baton/README.md:9` says “Executor serializes canonical application through a single writer”.

These statements assign the actual mutation/writer to Executor, whereas the adopted reuse split and `docs/overview/rust-interfaces.md:286–340`, `docs/execution/README.md:20–32`, and the current canonical sequence put that authority in Storage. Executor validates/selects/orchestrates and returns Storage's durable result. This distinction matters for cloned DatabaseSet handles, cancellation safety and import/recovery paths.

Corrections:

- Interface guide: “Executor::commit coordinates the canonical path; Storage owns canonical mutation. Canonical mutation must not be canceled like an advisory job.” Retain the no-wait and background planning language.
- Baton responsibilities: “Executor orchestrates canonical application through Storage's single writer.” Optionally update line 7 to name Storage for physical application, while leaving the direct Orderer→Executor path intact.

The native evidence does not choose our application module boundary, but it explains why an explicit writer boundary is substantive: `DatabaseSet` is Clone, mutation methods use shared handles, and native `finalize` cancellation can lose the database. `&mut self` on one facade does not fence every alias.

### F3 — P3: body prose still presents removed helper names as unexplained contracts

Locations: `docs/consensus/block-body.md:32–41` uses `commitment(&StoredBody)`, `build(ProducerContext) -> Some/None`, publication “via publish”, and `on_retire` after the page now correctly instructs direct Automaton/Relay/Reporter attachment.

These are not methods in the five application traits or the upstream callbacks. The surrounding explanation is semantically useful, but the unlabeled function spelling makes the reader infer another body API to implement. The BlockService Rust page explicitly removes that duplicate seam and says native Relay has no on_retire.

Correction: recast these paragraphs as direct callback semantics: the propose response gets the completed retained body's digest; a definite build decline closes the response while temporary dependencies keep it pending; Relay schedules retained-body lookup and buffered dissemination; native publication retirement is a proposed lifecycle handoff and never by itself permits archive release. If internal helpers are retained as examples, label them optional internal pseudocode without an additional public trait. Preserve the exact current pending/invalid/storage-failure and custody requirements.

## Small source-diagram precision correction

`docs/e2e/block-body.md:25` shows `Mailbox::broadcast_shared(body)`. At the adopted pin, `broadcast_shared` takes `recipients: Recipients<P>` and `message: Arc<M>` (`broadcast/src/buffered/ingress.rs:127–132`). Since the diagram uses the exact upstream name, show `Mailbox::broadcast_shared(recipients, shared_body)` or explicitly call the arrow an abstract broadcast enqueue. Recipient policy remains open; adding the argument does not select it. This is a signature depiction issue, not an extra wait or actor requirement.

## Independently inspected evidence

The original source files retained by wave 1 were read directly, rather than accepting earlier review verdicts. Each hash below is computed from the retained bytes. Their retained native manifests identify source commit `534af0ede48affd35b2111522527547b4cc9bf72`.

| Native source location | Independently checked semantics |
|---|---|
| `consensus/src/lib.rs:116–174,224–264` | Propose and verify return receiver futures; temporary missing dependencies stay pending; false is permanent invalidity; synchronous Relay/Reporter callback signatures; no retire callback |
| `broadcast/src/buffered/ingress.rs:99–132` | Subscribe waits for local cached/future availability, get is a local query, broadcast_shared has recipients and Arc message; local Feedback is not remote durable custody |
| `resolver/src/lib.rs:149–179` | Consumer delivery validates requested keys and distinguishes response dispositions; subscriber cancellation may discard validation result |
| `consensus/src/multimmit/types/block.rs:47–117` | Producer Context is reconstructed from producer header coordinates and parent; producer parent is not merged execution-parent state |
| `glue/src/stateful/db/mod.rs:291–334` | Unmerkleized→merkleize→Merkleized/root; new child batch is made from a sealed parent; generic Unmerkleized exposes no common key-operation API |
| `glue/src/stateful/db/mod.rs:474–499,508–567` | Barrier true requires all flush completions; shutdown Closed/Aborted returns false; other flush errors panic; DatabaseSet is Clone; sealed fork; native finalize(batch) applies then returns barrier; cancellation loses active DB |
| `storage/src/qmdb/any/batch.rs:1297–1356,1228–1230` | Pending write normalization and staged-read caveats; sealing appends CommitFloor; checkpoint batching can change storage history and cannot be assumed to produce matching roots |

| Retained source | SHA-256 |
|---|---|
| `assets/review/commonware-reuse-20261004/block-wave1/sources/native/consensus/src/lib.rs` | `fa8d210fd35444cfe10ba5926083147db3baffd9a2ca2e32d6fd405fa52e9470` |
| `assets/review/commonware-reuse-20261004/block-wave1/sources/native/broadcast/src/buffered/ingress.rs` | `6e740792e66aeb9c51e6cb02f5ba671cd8dd72e044ee4adf8631c35fa5394d19` |
| `assets/review/commonware-reuse-20261004/block-wave1/sources/native/resolver/src/lib.rs` | `3f490165744ec253b4b6a1e10a51a34192c62ece9008bdb6a1c1f315d80764bb` |
| `assets/review/commonware-reuse-20261004/block-wave1/sources/native/consensus/src/multimmit/types/block.rs` | `f5f5f5ce4a43944e7a54467c6f796bd988c1bba0a8ff5e793dbf2c757827de34` |
| `assets/review/commonware-reuse-20261004/storage-wave1/pin-glue-src-stateful-db-mod.rs` | `36036c705fc5e2b78cf3bae2bed816d25481f612f624ef93abfac1b3c4a39201` |
| `assets/review/commonware-reuse-20261004/storage-wave1/pin-storage-src-qmdb-any-batch.rs` | `35b1c70f82cf9f0de607f13908b272b15c6f5aed6b1e06491c6b7ac51ff0d582` |

## Whole E2E and source-diagram assessment

All 31 reader pages in docs/SUMMARY.md were read, along with SUMMARY itself, AGENTS, README, BATON_HANDOFF and the research paper. The cited historical prefix-plan §§7.1–7.2 and submission-readiness §§23 and 25 were read as provenance. Their old advisory-only membership and candidate defaults were not treated as current requirements. Current wave-1 interface/storage reviews were read after independent current-page/source inspection to compare coverage.

| Scope | Current evidence and result |
|---|---|
| Normal ingress, body and execution | `e2e/normal.md:7–38`: pool candidate selection→retained body→authenticated CandidateBlock→completed unsealed effects→irrevocable range→Storage prepare/apply→durable ACK; local commit and certification separate |
| Body missing/invalid/custody | `e2e/block-body.md:37–85`: missing/wrong-peer bytes stay pending; expected invalid payload alone gets false; local storage failure never becomes custody; header/body join can await Reporter independently |
| Native finality and dense delivery | `e2e/native-consensus.md:9–52`, `e2e/canonical.md:7–36`: native DA/proposal/finality work is independent; sparse facts require exact policy/history interpretation; included emits, authenticated empty skips, unresolved stops; missing body is not empty |
| Leader report window and freeze | `e2e/leader.md:7–79`: closure first 4f+1 or deadline, fixed snapshot, no direction reply quorum; actual-context recheck and pre-adoption base fallback; fixed proposal does not mutate after late planning/report/pool changes; preservation/adoption/continuation remain open |
| Non-leader branch execution | `e2e/reschedule.md:9–36`: authenticated current direction→required inputs→execution parent→completed result; missing base/body adds no cut wait; canonical state cannot be rolled back |
| Root preparation and canonical apply | `e2e/canonical.md:40–79`: unsealed effects or explicit rootless adapter→selected prepare/merkleize→native finalize(batch)→Barrier+metadata linkage; Storage owns physical reclamation, Executor logical promotion/pruning; failed flush has no successful receipt |
| Result certification | `e2e/results.md:9–42`: root and complete result/output binding before sign; retained own direct provenance; full stable subject, eligible distinct f+1, exact order/base check; no raw collector-count shortcut or Baton gate |
| Active-validator sync | `e2e/state-sync.md:9–49`: pending order evidence→verified certificate→material validation→safe fence→same Storage writer→durable import; unavailable certificate/material preserves local work; imported range gets no own direct signature; next directly executed range may sign |
| Startup and lost ACK recovery | `e2e/recovery.md:7–85`: body custody supports native replay independently of execution-state recovery; application readiness separate; recover state/output/cursor/provenance; exact idempotent redelivery identity, not root equality |
| Parent/rootless boundaries | `execution/qmdb.md:80–121,123–171`: native/release recipes separate; no unsealed-parent fork claimed; optional overlay identified as additional adapter; prefix extraction/reexecution and actual ancestry required; identical logical values do not imply reusable sealed ancestry |
| Shared/cloned authority and retention | `execution/qmdb.md:140–186`, `execution/README.md:26–34`: access fence spans lazy reads/stage/expand/materialization/merkleization and all aliases; stale-result generation alone is insufficient; canonical mutation not advisory-cancelable; retained references govern physical release |
| Architecture and internal QMDB maps | `overview/architecture.md:11–38`, `execution/qmdb.md:19–56`: named Storage role separates effects/root/apply, underlying engines blue; rootless adapter explicit; no full Stateful dependency or Bank semantics |

None of these source sequences imposes a root for every execution attempt, an extra direction approval quorum, compulsory peer collection before the next execution, or a particular signing granularity. The explicit root/signing/batch-boundary determinism decisions remain blank.

## Mechanical consistency checks and pending artifacts

- Exactly five proposed `pub trait` names occur in canonical application blocks and export: TxPool, Orderer, Baton, Executor, Storage. Existing callback excerpts use `rust,ignore` and do not enter the generated export.
- Export reconstruction using the checked-in exporter's exact assembly rule equals `docs/assets/interfaces/baton.rs` byte for byte. Initial naive block containment differed only because repeated Future imports are intentionally deduplicated; exact assembly comparison resolves that.
- There are 39 empty decision cells across the current Markdown pages. None were filled by this review.
- The native source pin remains 534af0ede48affd35b2111522527547b4cc9bf72. Paper/handoff retain descending 3f+1-th greatest rank; docs do not introduce a contradictory ascending rank.
- All 18 inline Mermaid sources were inspected. At snapshot time 11 mmd files differed from the current inline sources:01,02,04,05,08,09,10,11,13,14,17. This is root's acknowledged generation work. Unchanged source diagrams 03,06,07,12,15,16,18 already matched.
- No archived/toy/native tests, compilation, benchmarks or LaTeX were run to label documentation as protocol validation. No publication/readback or rendered visual QA was performed by this reviewer. The final root-owned render/export/link/build/publication checks remain required after edits settle.

## Exact reader/source snapshots

SHA-256 hashes are of reviewed current bytes. Paths are relative to the canonical repository above. SUMMARY is navigation metadata; the other31 Markdown files are reader pages.

| File | SHA-256 | Lines |
|---|---|---:|
| `docs/README.md` | `36f3b4711d09fd81a296153c3dfa2a87b6384f883cfb1c68948a3e1b80736ff4` | 35 |
| `docs/SUMMARY.md` | `48624939af1dd13321694376f1a07af2bbb978a2417f30bd6f4bc3f628b5e5a8` | 54 |
| `docs/baton/README.md` | `1abd2f46c050b8771cea3cf23788d01a20f5a9dae4e86e728e2873777b5274dd` | 30 |
| `docs/baton/direction.md` | `ffca5634f3c582147e5b9764c412c35e63a3abb9ddaf0270d8f843cc742e1eda` | 75 |
| `docs/baton/interfaces.md` | `c383302c0acc6817d136a7829a8dccc3962d94669af5223f8776bc168d31986b` | 30 |
| `docs/consensus/README.md` | `4f1044c2d71bee357ff800604565e737dfae97003a87299c93533560aa021f65` | 83 |
| `docs/consensus/block-body.md` | `0ebb7b5c4d3e027f30138f239cb45771ef7b40032b32df35f3c08016b06c87fa` | 105 |
| `docs/consensus/decisions.md` | `5cd5d25894a485829ba0fb65ded031b15589cd4312ba15931dfcb8e5577c0adf` | 16 |
| `docs/consensus/ordered-input.md` | `498987f35d50e84bac391232e5d39b3f44ab7bcdbb8687f3ba1c0d7c1842bebf` | 50 |
| `docs/e2e/block-body.md` | `dde7ec9beefed392b97a70c27fc36847858c25acd9a0e06a3fd44b4d7a5db829` | 85 |
| `docs/e2e/canonical.md` | `000c1e19afa1403a5e0717e2ebc266fe6df4febd5d31498a113b5461f1b934c8` | 79 |
| `docs/e2e/leader.md` | `2d54bce6f941631004ee2244c1a872c045a8651ae26b8a0d0686d1899096608e` | 79 |
| `docs/e2e/native-consensus.md` | `39c8acaa0b594d7ec7049b68dd28892e40b7dc710796c0a5c238a2d0e7e620ba` | 52 |
| `docs/e2e/normal.md` | `6040a0f865462b96deec8f79d2c7b3541d44769991972ef602df490556542d5d` | 82 |
| `docs/e2e/recovery.md` | `cd4312136f3179e8cf33f5438664983cc477ac4a46055ab4f51f4100c7e2767e` | 85 |
| `docs/e2e/reschedule.md` | `f1916ed2e4ed591587e14a2148bf675d6be0d3835b1becc1665b895f1822e4eb` | 36 |
| `docs/e2e/results.md` | `7e40080b7b65ec05a9a7e6cb28bbb607932f2dda47cb8850e16ace4b45c3a289` | 42 |
| `docs/e2e/state-sync.md` | `9b5dee130a7b6fe17734c4f56fde070fe408e7cd969615507333195921b6b799` | 49 |
| `docs/execution/README.md` | `3afb5cefa76bce0348e2b00ae71609cfe863bc69277391cd9f979b00c1834ae9` | 66 |
| `docs/execution/interfaces.md` | `fe1f8acd4293054c1a9db93d33ce223a794c53579db2249dc7cdbb37daec217c` | 44 |
| `docs/execution/qmdb.md` | `080a4cae4248d42e33dd81125b249fa72fd82b840c48871d313b84a9f2e6a14e` | 186 |
| `docs/execution/state-sync.md` | `ae86d60930bfd5b84576236f891bbeaffcfde223efb63ea83cb6cbc360f5b840` | 31 |
| `docs/overview/architecture.md` | `717b5467661d6c3f1e0e179f9b65708e7af9ca3e6d17f9bbf61d78f2d0043a4e` | 81 |
| `docs/overview/glossary.md` | `389591cf7463deb23e5724e7893b923e00ebc53baed2dd911ffa54bb11f339d8` | 63 |
| `docs/overview/interfaces.md` | `75186da2c22d034800d490ea83f8775b5492d1756ca12afd1c52a62340f6df5b` | 49 |
| `docs/overview/networking.md` | `de38e939deaeb1b9c025afea313f0e0f4b87bd8602ebc0139e654828cb54a741` | 19 |
| `docs/overview/rust-interfaces.md` | `8013382ce85dc94b6d85805751cbcbd3dc4304cd8cf2ac8774a5e4698b8990e8` | 346 |
| `docs/reference/integration.md` | `a6e5ae6fe29cece60e5324c44e5cf4a5ba73f7238fac52c0ee414e99433a2fd3` | 126 |
| `docs/reference/sources.md` | `716b76900efc341dc8ef49601e2c8c4e64159b22a720d66a49654d87e46d67b8` | 11 |
| `docs/reference/verification.md` | `876d2105c0ec760206e5c50f3f48f617baa5bfdf74fa1dd4f43a9cd9812b15b3` | 21 |
| `docs/tx/README.md` | `cc240484b12c8418d37e4d032e2443df00dc73e88b01f77ba9114a99a13b45b5` | 73 |
| `docs/tx/interfaces.md` | `2b8bd54d850d6fefabce36077230e3e993dfd79a7d2640cf8a4e1225025c3728` | 22 |

| Prerequisite / generated artifact | SHA-256 |
|---|---|
| `AGENTS.md` | `27b8bd42e75f3020e3dfd53302774bdb808fa579827c259bf2dc712617ad947a` |
| `README.md` | `861d73faee57e85a98d1eecfa0c278ccde66801c37b856d09a1d088505bad0b9` |
| `BATON_HANDOFF.md` | `66a405bcd1a5630ea34b898cd938cc8c0b18429b186187f5f51742b899efcaf6` |
| `baton-paper.md` | `f756eeb76c14159f314258aa16b02a23d9c8aa1d45260a0c06cdeeb6c5fb039d` |
| `docs/assets/interfaces/baton.rs` | `66e0f67b815b8c23dc636fc42ff01385cf1b3c2f789aa5249b9ff9f0b548fdab` |

| Source diagram at audit time | SHA-256 |
|---|---|
| `docs/assets/diagrams/diagram-01.mmd` | `d8b6226b5fe22de3ae3d73c10dd204ad5975cfc1b491df9d20e5e90a7cf91c22` |
| `docs/assets/diagrams/diagram-02.mmd` | `cdfff83d9fe3e87c4ea35a6241fdb0873b03f0c473b9672639a3b5330c56dce2` |
| `docs/assets/diagrams/diagram-03.mmd` | `bcc458524e8aeb32bf0f60563a870fe25942431fd2b6f04f8631085017350b80` |
| `docs/assets/diagrams/diagram-04.mmd` | `15c760b97810131950f0993e7c567c6a50ff84372f5e42c476a58cb709dbba4b` |
| `docs/assets/diagrams/diagram-05.mmd` | `d478f16234110c9c6d14346a44e2eef99115da98afc83b9183befae258ac42c6` |
| `docs/assets/diagrams/diagram-06.mmd` | `88de04405687c27bae88585a3e73acb3b7b1c87b507fdfaf23ef4994fd2421e2` |
| `docs/assets/diagrams/diagram-07.mmd` | `1197ec8338219eccd6e583cd6c3f1e4c93d91108eca4c5d73aa292ccdace45b5` |
| `docs/assets/diagrams/diagram-08.mmd` | `f7354347d1f69783efdfc916ce7fe75413881d18f1a9d7b7a5d391b1292599c5` |
| `docs/assets/diagrams/diagram-09.mmd` | `c14c042b91c614fc8a088d51d0e20563dfe1b45020401f498df0a52076bcb00e` |
| `docs/assets/diagrams/diagram-10.mmd` | `40bf5beeb270e15b932f8c38833e8d8812f2e97fcc62e33ab88f8151021c317b` |
| `docs/assets/diagrams/diagram-11.mmd` | `5dbd97dc0d3063c0cb6c64104311c5801bc3efd4fb0ac988bf3015afbb6fc3cc` |
| `docs/assets/diagrams/diagram-12.mmd` | `f1f3fc970bc1d1164b4357946814d8d08dac24dd24c1539bc5c82525859ba13e` |
| `docs/assets/diagrams/diagram-13.mmd` | `ab99f65c93cbc9721e0c2ddd9d1d9aaa964c013cee35aeae77ac21bdff4db11a` |
| `docs/assets/diagrams/diagram-14.mmd` | `73bdee7d2adccedb1b3263a391a5a1feabdf634f11135d62780a3c29041fb02a` |
| `docs/assets/diagrams/diagram-15.mmd` | `71c81d894487b251e3dd191d177364291761151ac5f0fa2d8f7ca3ad31e64ac0` |
| `docs/assets/diagrams/diagram-16.mmd` | `8f43cb4ef3587b81658ff35807ef118346bee4e78f94d1e11398efccfa3fcd93` |
| `docs/assets/diagrams/diagram-17.mmd` | `777621dc0d2354831c5aa51bec5cf69df301817df286c0dcc9b371cbc2435adc` |
| `docs/assets/diagrams/diagram-18.mmd` | `3589b4c68dc0c3ad260c8c4479bfb3c1f5245dbe1be3a25798b91e3db681652d` |
