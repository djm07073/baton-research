# Round 10: E2E diagram completion semantics

Reviewer: `/root/docs_alignment`, with source findings from `/root/native_audit` and storage findings from `/root/simplification`. Scope is the existing E2E diagrams and adjacent explanatory text; no protocol, renderer configuration or public interface was added.

## Applied semantic corrections

| Diagram / source page | Correction | Why it is required |
|---|---|---|
| 04 / `docs/e2e/block-body.md` | Common subscribe-or-retained-token result is now “Durable custody established.” | `subscribe_block` returns the block, while `Custody::wait` returns successful completion rather than another block. App already owns its constructed block. Source: `marshal/mailbox.rs:354–358,431–445`, `marshal/types.rs:316–318`. |
| 05 / `docs/e2e/block-body.md` | Optional explicit retrieval is labeled concurrent; the durable return explicitly names `subscribe_block`. Adjacent prose says fetch may expose buffered bytes before storage sync. | A reader must not interpret the preceding fetch response as proof of durable custody, nor await an unfulfilled subscription before starting required active retrieval. Source: `marshal/mailbox.rs:409–445`; existing native body-flow contract. |
| 09 / `docs/e2e/canonical.md` | Failed storage completion says “No ACK or durable completion, stop using failed storage and recover.” Reclamation requires retention and reference obligations to permit it. | Apply may already have advanced state before final persistence fails. Recovery/retention obligations extend beyond current live references and serving. Source evidence is recorded in `round9-durable-boundaries.md`; the parent requested these exact minimal labels. |
| 14 / `docs/e2e/state-sync.md` | After durable import, advance the canonical base and **schedule** pool maintenance. | Pool maintenance completion is not an extra ACK approval step. Exact durable imported coverage and retained ordered Update identities remain required. This resolves the diagram finding recorded in `round8-role-walkthrough.md`. |
| 15 / `docs/e2e/native-consensus.md` | Native DA and Native view/finality are separate siblings in the existing parallel region; ordinary votes broadcast to peers, including the drawn native owner. Adjacent prose states view work may already run during producer validation and finality is processed locally by each native view owner. | The old sequential branch visually implied DA certificate completion preceded leader-view progress, contradicting its note. Source: `machine/durability/effect.rs:470–491` distinguishes producer-directed DA votes from ordinary broadcast; `machine/reducer/step.rs:573–603` drains locally computed finality without a leader-only ownership condition. Native eligibility gates remain explicit. |

The body-publication paragraph also links existing Relay completion semantics: local `Ok` can mean no matching staged block was found and does not prove remote receipt/custody. No new cache, retry service or publication acknowledgement was introduced.

All embedded Mermaid edits were duplicated exactly in their existing `.mmd` sources. Root regenerated the five targeted PNG/SVG pairs and manifest. `git diff --check` passed after the edits.

## Pixel inspection of final generated artifacts

I opened the **actual** `docs/assets/diagrams/diagram-{04,05,09,14}.png` after root reported the targeted render complete. Result: pass for each, with no additional cosmetic change.

- **04:** Stage acceptance, local custody result, true verdict and signing remain vertically distinct. New common custody label fits without covering adjacent arrows. Separate native-header and body-channel arrows plus the arrival-order note remain readable.
- **05:** Concurrent-fetch optional region, pending-body branch and explicit subscription completion are readable. Invalid/valid branches are separated; the later optional scheduler admission remains visually independent of execution completion. No label overlaps another label or branch boundary.
- **09:** The durability-success/failure branches remain separated. Retention wording wraps within the reclamation region without clipping; the failure note is fully visible. It no longer describes failure to establish durability as proof that apply never succeeded.
- **14:** The new “advance canonical base and schedule pool maintenance” step is legible before the exact covered-Update optional ACK region. Imported provenance and failure/no-ACK paths remain visible. No text is clipped or hidden by the nested regions.

Root independently opened final **15** and reported readable parallel branches and labels. This report does not claim a second pixel review of 15 by this reviewer.

## Reviewed source and PNG fingerprints

| Diagram | SHA-256 `.mmd` | SHA-256 `.png` |
|---|---|---|
| 04 | `0fae09f31d912ca1aa24c581383214f052e6a2db0bde7164a8bd0384d8efba4d` | `fc4fb6aabc203c626f23043e57f378efafbd6c43d67e6fd6e6eaefb5768edf90` |
| 05 | `297c61704f531aa140dde30d20cac052ed96a4cf993b22892f8b5c3fa8394fe4` | `9884cd5157e3a894c049ea949bd980d2af8ea92b0a30d18276bae8c138d2e360` |
| 09 | `99e1fb9e2251097de4d27bcfb2a06359781e538829735e589c7490df76e07236` | `f6f685ccfb62bccd65c1432af2fe260736e7d072355f4b0c5ea1f65c59d3316a` |
| 14 | `0c68a0d001b0da32157f2eba0a7b3a13e37196a06a2eafd4341571d8ca0d61a8` | `79581a02671e9a1f18f557fc5f8f098a483b10fb45aca88620c92d7e2e51c756` |
| 15 | `03d10ce5be6d7e35b6b8e798d8a8c1d15dd4e4280b31a614bd0446db5d83074d` | `9a0f0caee64ad8e7571a068be38f1aa465c88d59d1777cb57f3f9a79c775b3e2` |

These are documentation and visual checks. They establish neither runtime correctness nor a completed App executor, atomic state import or native Baton policy implementation.
