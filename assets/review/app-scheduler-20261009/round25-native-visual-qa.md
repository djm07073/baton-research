# Round 25: fresh native/body PNG visual review

2026-10-09 09:22 UTC. Opened and visually inspected the actual current PNGs in `docs/assets/diagrams` with the image-viewing tool, all four in this round. Read their current Mermaid sources and adjacent reader prose; checked embedded Mermaid equals the corresponding `.mmd` source after trimming. Re-read relevant native custody, dispatch, publication, Relay and Marshal ownership paths at `6233438985d8249d2b2bc1204191d5d405652288`. This is visual/document/source review, not a renderer-only dimension check or runtime test.

## Exact inspected artifacts

| PNG | Pixels | SHA-256 |
|---|---|---|
| diagram-04.png | 1318 × 1284 | `fc4fb6aabc203c626f23043e57f378efafbd6c43d67e6fd6e6eaefb5768edf90` |
| diagram-05.png | 936 × 1722 | `9884cd5157e3a894c049ea949bd980d2af8ea92b0a30d18276bae8c138d2e360` |
| diagram-15.png | 1359 × 1644 | `9a0f0caee64ad8e7571a068be38f1aa465c88d59d1777cb57f3f9a79c775b3e2` |
| diagram-16.png | 1136 × 634 | `8b2de46afb7397732a24ce98b6843b40ca5f05b80bc34de6876f623739763193` |

These are the reader assets under `docs/assets/diagrams`, not the different legacy copies under top-level `assets/diagrams`. No legacy image was used as evidence of the current rendering.

## Visual and semantic disposition

| Diagram | Actual visual observations | Native/prose comparison |
|---|---|---|
| 04, local propose/custody/dissemination | All six participant headings, long custody/Relay labels, both transfer arrows and bottom note are fully visible. No clipping or conflicting text overlap. | Stage acceptance returns a token before proposal response; local verify establishes durable custody before header signing. Body digest response differs from Relay header-digest lookup. Complete header/body broadcast and separate signed-header data-plane transfer are distinct; the note explicitly permits either arrival order. Source: mailbox.rs:337–358; actor/app.rs:94–158; machine/producer.rs:430–478; actor/publish.rs:124–136; marshal/relay.rs:101–112. Adjacent prose correctly limits Relay Ok, including missing cache entry. |
| 05, body availability and validation | The optional fetch frame, unavailable/available alternatives and invalid/valid alternatives fit inside the canvas. Notes and the final execution-independence note remain readable. | Subscribe and concurrent explicit fetch are separate. The illustrated success response is specifically a durable subscription result, not merely fetched bytes. The adjoining paragraph preserves get/fetch buffered-before-sync and wrong-peer-response distinctions. Valid candidate facts are retained independently of execution completion; optional scheduling needs authentication/ancestry and an exact parent. The prose links the fuller lifecycle/deferred-capacity/fetched-bytes fallback handler. Source: mailbox.rs:409–443; chain_plane.rs:522–550. |
| 15, native producer/DA/view flow | All six headings, three parallel sections, wide independence note and final Marshal history/delivery box are readable. The section boundaries do not obscure message labels. | Local verify precedes producer signing; remote native authentication/eligibility precedes App verify. Speculation, DA and view/finality appear in parallel branches, with no execution or application ACK edge into native voting. Votes are described as broadcast to peers, including the shown leader/view owner. Adjacent prose explicitly says view work may already run during producer validation and each owner processes finality locally, preventing the linear illustration from implying a global phase barrier. Native eligibility/durability still applies. Source: chain task ownership in actor/chains.rs:1–99, app.rs:125–158, chain_plane.rs:522–550, machine/producer.rs:430–478 and ProposalPolicy semantics in config/mod.rs:32–45. |
| 16, owner map | All nodes and labels are visible. Curved transport/Update/custody arrows are traceable; no label collision or clipped edge endpoint. Colors consistently distinguish existing native/Marshal owners from App. | App contains pool/scheduler/execution/state; native shell owns protocol-machine/journal/proof links; Marshal owns body channels and ordered Update. ACK goes from App to Marshal, not to the native machine. The App→machine Baton policy edge is dashed and explicitly future. This is an ownership map; adjacent source map identifies separate remote chain-plane and recovery callback paths rather than asserting every verify is driven by local AppExecutor. Marshal ownership matches marshal/mod.rs:8–37; native shell/machine ownership matches machine/mod.rs:1–64. |

No arrow or adjacent paragraph makes speculative execution completion or App delivery ACK a native vote/cut prerequisite. No extra BlockService/Orderer is depicted. The diagrams intentionally show relevant success/dispatch paths; current surrounding prose supplies cancellation, backpressure, transient failure and recovery limits without claiming a complete protocol proof.

## Source binding

Current `.mmd` SHA-256 values:

- 04: `0fae09f31d912ca1aa24c581383214f052e6a2db0bde7164a8bd0384d8efba4d`
- 05: `297c61704f531aa140dde30d20cac052ed96a4cf993b22892f8b5c3fa8394fe4`
- 15: `03d10ce5be6d7e35b6b8e798d8a8c1d15dd4e4280b31a614bd0446db5d83074d`
- 16: `da4880835c43dfae4ee8abaa27ba9ee5ce9f0848825c7121d468a1c262284d14`

The inspected surrounding pages were e2e/block-body.md (`d88e71e79fa2f09967f27de07907a81d1cf306eaa76281cd4cb14d8bfe2b4032`), e2e/native-consensus.md (`81588b9a3d7949601d904fc6418841689ae574896a2011534edd738f76063446`) and consensus/README.md (`94d5b0e0a1f5cec6d0d492261018d426d7411d1f820d8e8a6bdc09a0c8337fa0`). All four embedded-source comparisons passed. No reader, diagram source or rendered artifact was edited; no native tests were run.
