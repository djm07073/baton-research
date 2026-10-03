# Wave-2 flow findings resolution

Independent reviewer: `/root/reuse_flow_review_v2`. Canonical repository: `/Users/leojin/Documents/Codex/2026-09-30/task/overpass-research`. Resolution snapshot: 2026-10-03T20:14:03.411008+00:00.

This supplements [REPORT.md](REPORT.md), whose historical snapshots remain unchanged. Only this RESOLUTION.md was written. The five requested correction pages were independently re-read in full, and the latest inline Mermaid sources plus storage/public-return boundaries were checked. Reader documentation, interfaces/export, protocol code, renders and GitBook were not edited by this reviewer.

## Resolution verdict

All three reported wording findings and the diagram signature precision point are resolved in the current bytes. No remaining contradiction was found in the corrected scope. The proposed `Storage::apply` public successful result consistently means recoverably durable CommitResult. Upstream native `DatabaseSet::finalize` still returns a durability Barrier rather than an application durable receipt; the adapter obligation remains explicit.

| Original issue | Current location and independent resolution |
|---|---|
| F1: Executor direction selection | `docs/e2e/leader.md:3` now says “uses Baton::plan”. Both inline leader sequences retain Baton planning and independent no-wait native cut/proposal freeze. No Executor plan method is implied. |
| F2: wrong canonical mutation owner | `docs/overview/interfaces.md:35` assigns shared canonical mutation to Storage and Executor::commit to orchestration. `docs/baton/README.md:7,9` explicitly names Storage roots/apply/durability and shared single writer while Executor orchestrates. The noncancelable canonical mutation rule is preserved. |
| F3: removed body helper interface remnants | `docs/consensus/block-body.md:32–41` now uses Digestible and existing Automaton/Relay/Reporter callbacks directly. commitment/build/publish/on_retire helpers are removed. Definite propose decline versus temporary pending, expected permanent invalidity, storage failure and native Retire/archive-release distinctions remain. No duplicate body trait was restored. |
| broadcast_shared signature depiction | `docs/e2e/block-body.md:25` now has `Mailbox::broadcast_shared(recipients, retained Arc)`, matching the two arguments in native `broadcast/src/buffered/ingress.rs:127–132`. No recipient policy or peer acknowledgement was adopted. |

## Durable public-return and flow consistency

- `docs/overview/rust-interfaces.md:318–326`: Storage::apply checks authorized canonical input, ancestry and single-writer access; it observes successful durability plus recoverable metadata linkage before returning CommitResult. State, outputs, cursor and direct/imported provenance recover together. Failed flush is not success, and canonical mutation is not canceled with advisory workers.
- `docs/overview/rust-interfaces.md:241–248,346`: Executor::commit delegates exact preparation/application, returns only after Storage's durable completion and remains distinct from result certification. The public interface does not expose a readable-only success as CommitResult.
- `docs/execution/interfaces.md:15,23`: the detailed method descriptions agree with these completion conditions. No second public return lifecycle bypasses Storage durability.
- `docs/e2e/canonical.md:60–75`: Storage awaits native finalize(batch), then Barrier::durable plus metadata/provenance linkage. Success produces Durable CommitResult before delivery ACK. Flush/shutdown/incomplete linkage produces no successful receipt or ACK. Physical reclamation remains separately reference/retention-gated.
- `docs/e2e/normal.md:28–34` and `docs/e2e/state-sync.md:29–39`: direct and imported application both use Storage's same durable result before delivery/outcome handoff. Import preserves original certificate and imported provenance; certificate alone does not stop execution. Baton receives only optional progress.
- `docs/execution/qmdb.md:162–186`: readonly visibility, successful barriers, crash linkage, canceled DB mutation, closure/abort and fatal flush failure remain distinct. Native finalize(batch) and indexed-release apply(batch)/finalize() recipes remain separated.
- `docs/e2e/results.md:15–33`: selected root preparation precedes own direct-result signing. Full-subject f+1 collection establishes certified state finalization while local application durability remains separate. Roots are not compulsory for every speculative attempt.

All 18 latest inline Mermaid sources were re-inspected. The corrections preserve completed unsealed effects, explicit rootless adapter limits, actual parent linkage, clone-wide fence obligations, no certificate-only execution stop, exact dense delivery across unresolved slots, no Baton certification/apply gate, no extra direction quorum and independent no-wait cut behavior. No new blocking semantics issue was found.

The diagrams represent integration design rather than verified protocol execution. The generic Storage branch-view/material-import seams remain incomplete/open as previously labelled; this resolution does not claim a built adapter or proof.

## Mechanical snapshot checks

Exactly five proposed application traits remain: TxPool, Orderer, Baton, Executor, Storage. Existing callbacks remain `rust,ignore`, excluded from the standalone export. Blank decision cells: **39**. Exact export reproduction from canonical Rust blocks: **True**. No Bank semantics or defaults were added.

Render regeneration is root-owned concurrent work. At this snapshot, **11** stored `.mmd` files differ from current inline sources. This remains a generation/publication task, not an unresolved source-flow finding. No SVG/PNG visual QA or GitBook readback was performed here.

## Current byte hashes

| Re-read corrected page | SHA-256 | Lines |
|---|---|---:|
| `docs/e2e/leader.md` | `2d54bce6f941631004ee2244c1a872c045a8651ae26b8a0d0686d1899096608e` | 79 |
| `docs/overview/interfaces.md` | `75186da2c22d034800d490ea83f8775b5492d1756ca12afd1c52a62340f6df5b` | 49 |
| `docs/baton/README.md` | `1abd2f46c050b8771cea3cf23788d01a20f5a9dae4e86e728e2873777b5274dd` | 30 |
| `docs/consensus/block-body.md` | `0ebb7b5c4d3e027f30138f239cb45771ef7b40032b32df35f3c08016b06c87fa` | 105 |
| `docs/e2e/block-body.md` | `dde7ec9beefed392b97a70c27fc36847858c25acd9a0e06a3fd44b4d7a5db829` | 85 |

| Additional checked contract/flow artifact | SHA-256 |
|---|---|
| `docs/overview/rust-interfaces.md` | `8013382ce85dc94b6d85805751cbcbd3dc4304cd8cf2ac8774a5e4698b8990e8` |
| `docs/execution/interfaces.md` | `fe1f8acd4293054c1a9db93d33ce223a794c53579db2249dc7cdbb37daec217c` |
| `docs/execution/README.md` | `3afb5cefa76bce0348e2b00ae71609cfe863bc69277391cd9f979b00c1834ae9` |
| `docs/execution/qmdb.md` | `080a4cae4248d42e33dd81125b249fa72fd82b840c48871d313b84a9f2e6a14e` |
| `docs/e2e/canonical.md` | `000c1e19afa1403a5e0717e2ebc266fe6df4febd5d31498a113b5461f1b934c8` |
| `docs/e2e/normal.md` | `6040a0f865462b96deec8f79d2c7b3541d44769991972ef602df490556542d5d` |
| `docs/e2e/results.md` | `7e40080b7b65ec05a9a7e6cb28bbb607932f2dda47cb8850e16ace4b45c3a289` |
| `docs/e2e/state-sync.md` | `9b5dee130a7b6fe17734c4f56fde070fe408e7cd969615507333195921b6b799` |
| `docs/e2e/recovery.md` | `cd4312136f3179e8cf33f5438664983cc477ac4a46055ab4f51f4100c7e2767e` |
| `docs/e2e/reschedule.md` | `f1916ed2e4ed591587e14a2148bf675d6be0d3835b1becc1665b895f1822e4eb` |
| `docs/overview/architecture.md` | `717b5467661d6c3f1e0e179f9b65708e7af9ca3e6d17f9bbf61d78f2d0043a4e` |
| `docs/consensus/README.md` | `4f1044c2d71bee357ff800604565e737dfae97003a87299c93533560aa021f65` |
| `docs/e2e/native-consensus.md` | `39c8acaa0b594d7ec7049b68dd28892e40b7dc710796c0a5c238a2d0e7e620ba` |
| `docs/assets/interfaces/baton.rs` | `66e0f67b815b8c23dc636fc42ff01385cf1b3c2f789aa5249b9ff9f0b548fdab` |

| Latest inline diagram | Canonical source location | SHA-256 of inline Mermaid body | Matches current .mmd |
|---|---|---|---|
| `diagram-01` | `docs/overview/architecture.md:11` | `432d40eac8f8556c659419915e638d6ac010540cf28ffbb43f9326528a2b2446` | False |
| `diagram-02` | `docs/e2e/normal.md:7` | `4c6f189d22c32bfc4dc621abbb30d548509f25659cba59ea7538ff5e08a22ec2` | False |
| `diagram-03` | `docs/e2e/normal.md:45` | `55fd749b7dbc5c4567c0bcf3783600a71cb480d035ebf02ff94e1fe7ca451c6e` | True |
| `diagram-04` | `docs/e2e/block-body.md:7` | `7f95598b976911f947839b5942061337af2991edd660246801881a0029b9dda8` | False |
| `diagram-05` | `docs/e2e/block-body.md:37` | `fcf64a78c6ef20617a61b31ef29248b6ceb9747d423f9a06491700f45e25bf0d` | False |
| `diagram-06` | `docs/e2e/leader.md:7` | `46d3917011d291db4dfdfd769893c3fd86020e2df4728c2175b29c6d0df492bd` | True |
| `diagram-07` | `docs/e2e/reschedule.md:9` | `a5c4df363c5e4b3bdb8a4233cd3b99b4d388ccebcd231c52bbd9ebaa18e2182d` | True |
| `diagram-08` | `docs/e2e/canonical.md:7` | `4309330438cbf20f3ae2cfb41435a42b2cea0b255fd399822a6dea3d187d935b` | False |
| `diagram-09` | `docs/e2e/canonical.md:40` | `cd361561d9c5ef609114450c1819f67caf4e42dc17ca4a169b5b75ec33333cd7` | False |
| `diagram-10` | `docs/e2e/recovery.md:56` | `9569c6af7ea91d67268d0ebcf582f4e78f42db2ec83f96277e5fec61d54796eb` | False |
| `diagram-11` | `docs/e2e/results.md:9` | `9b3b280543653674c266228b23048d84fb7bf3c2e518334282928142b3476c36` | False |
| `diagram-12` | `docs/e2e/leader.md:46` | `7008971e6dd05621f815d6994ae474f6f3366ac6b0dcf8982d7542c717fc0612` | True |
| `diagram-13` | `docs/e2e/recovery.md:7` | `717987e5bc233231b68df9575b2faf9f5adf3f305cb0050825417f068d95030e` | False |
| `diagram-14` | `docs/e2e/state-sync.md:9` | `26955fef169e5e9a8b98423a82cef5706c725a4164559ad128f67588f0e1b959` | False |
| `diagram-15` | `docs/e2e/native-consensus.md:9` | `b40391445e9174c8a0399165c4c027850b783f4521566cbcae4eccb8bf4ba908` | True |
| `diagram-16` | `docs/consensus/README.md:17` | `74051c5b53ede03729f50d6183109e1170a3003bdb3c885ad6e10b0b65303062` | True |
| `diagram-17` | `docs/execution/qmdb.md:19` | `69645e1f40c0aee8ca63708abce75156c4a72c2d6cd833d53a7031d94b98f66c` | False |
| `diagram-18` | `docs/execution/qmdb.md:123` | `6aee5f77fc56c2db08868e5deac1a8c2fdfbf12e6c165e96ec9c0aa0821a93f9` | True |

Hashes identify reviewed current bytes. Concurrent later edits require comparison. No native/toy tests, compilation, benchmarks or external mutations were performed.
