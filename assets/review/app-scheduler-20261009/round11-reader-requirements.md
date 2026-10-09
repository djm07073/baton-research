# Round 11: original reader requirements

Reviewer: `/root/docs_alignment`. This pass starts from the user's original questions and requested rewrite, rather than adding another architecture. It reads current `docs/baton/` with the overview, E2E and transaction companion pages. The floor-generation correction underway with root is outside this pass. This is documentation/source evidence, not App runtime validation.

## One confirmed companion mismatch, fixed

`docs/e2e/block-body.md:82` previously said a full speculative queue must never lose the only eligibility record. Read literally, this imposed unconditional retention even though the canonical handler at `docs/baton/interfaces.md:61` permits bounded deferral **or forgoing a speculative opportunity**. It could encourage an unbounded candidate store or pressure-dependent custody verdict.

Replaced only that sentence with: “Retain/coalesce deferred eligibility within the chosen bound, or explicitly forgo that speculative opportunity. A dropped optional notification or full speculative queue must not turn a valid body into `false` or lose canonical input.”

The required ancestry/authentication, current-owner late-verify check, exact-parent dispatch and canonical retention obligations remain intact. This introduces no notification, queue, type or public interface. No diagram source was changed; no rerender is needed for this prose correction.

## Original requirements and exact reading paths

| User need | Current answer and evidence | Acceptance |
|---|---|---|
| Put the transaction pool inside App | `docs/baton/README.md:15,19` names App ownership and directly links the pool contract. `docs/tx/interfaces.md:7–17` gives ingress/admit, bounded stable selection and durable outcome maintenance, including local pool membership not being a peer/canonical payload validity prerequisite. `:19–29` connects selection to existing `Automaton::propose`, Marshal staging and the canonical callback pages. | A reader can implement concrete pool functions without designing a public TxPool trait or treating selection/proposal as canonical retirement. Backend/policy remain explicit choices. |
| Implement concrete Pre-cut and Baton modes | `docs/baton/README.md:21` permits two concrete implementations or a local mode enum. `docs/baton/direction.md:7–16` compares the same candidate, checkpoint, worker and Update inputs. `:20–37` defines fixed started prefix plus pending-only ordering with both A→B→C and A→C→B cases. `docs/e2e/reschedule.md:7–11` illustrates dispatch from completed parents. | Pre-cut has no Baton instance, report traffic or native policy changes. App execution/storage is shared; mode selection does not imply two simultaneous canonical writers or duplicated body services. |
| Explain `verify + other conditions` as another-lane candidate availability | `docs/baton/README.md:38–48` identifies remote, local pre-sign and recovery origins, no origin flag, optional local producer lane, nonproducing validators and Observer. `docs/overview/glossary.md:21` traces role/local-lane values to actual Engine/scheme/epoch mapping. `docs/baton/interfaces.md:33–51` reconstructs the exact header/BlockRef and separates custody/admission from later dispatch. `:61–63` handles pending ancestry, bounded optional speculation, duplicates and current lifecycle/applied state. | Successful verification can supply usable foreign-lane candidate facts under role/lane/live/identity conditions. Calling verify is neither a packet-receive event nor proof of executable ancestry. Execution, result roots and reports do not gate true. |
| Explain App and scheduler behavior on Marshal Update | `docs/baton/interfaces.md:87–114` identifies the synchronous Reporter boundary, retains full Update/Exact, takes continuous indices, checks replay, reconciles exact canonical predecessor and selects completed work, repair or verified import. `docs/baton/direction.md:39–43` links that worker and explains canonical-base advancement, applied pending removal and conflict fencing. `docs/e2e/canonical.md:41–45` allows first-seen Update without earlier verify/candidate metadata. | Existing Marshal is the canonical input authority. App does not re-sort Updates or require another Automaton call, report approval, pool membership or scheduler certificate. |
| Explain ACK versus execution/native progress | `docs/baton/README.md:52–56` states reuse/repair followed by durable application; matching completed speculation may leave mainly remaining storage work. `docs/baton/interfaces.md:118–129` puts the normal milestone table and active-window behavior before crash/floor exceptions. `docs/e2e/canonical.md:49–55` distinguishes in-memory ACK, App durability and later Marshal cursor persistence, and warns that the example immediate ACK is not the transaction consumer. | ACK is after honest local durable application; it does not inherently rerun execution. Unfinished execution still must be completed or replaced with verified applicable material. Only App delivery capacity waits when its ordinary window fills; native voting/finality does not wait for this ACK. |
| Reuse native machinery and remove redundant layers | `docs/baton/README.md:11–19,32–34` assigns existing Engine/Marshal work and concrete App internals. `docs/overview/networking.md:25–39` gives existing Relay, buffer, resolver bridge, mailbox and typed Reporter connections. `docs/overview/interfaces.md:19,32` explains ordinary handles, associated Activity types and why mutable callback handles do not serialize workers/storage. `docs/overview/rust-interfaces.md` supplies current signature excerpts rather than new traits. | No mandatory BlockService, Orderer, Executor, Storage or generic scheduler framework remains in the live contract. Additional App messages use existing logical channels and primitives. |

## Earlier questions still answered

- **Where the execution machine starts:** `docs/baton/interfaces.md:7–11` links the actual node/Marshal assembly and keeps custody/output handling available before Engine recovery. `docs/baton/README.md:5` explicitly distinguishes native AppExecutor dispatch from transaction execution; `interfaces.md:65–83` shows the App-owned worker launch/claim/completion lifecycle.
- **Digest, header, body and stage completion:** entry guide `:27–32`, glossary `:25–30`, and `docs/e2e/block-body.md:37–39,78` distinguish body digest, contextual header digest, structured BlockRef, complete TransactionBlock, accepted stage token and successful durable custody. Neither body arrival nor fetch alone proves custody.
- **Can application events be added:** existing native Activity observations are optional typed handles; App candidate admission, worker completion, canonical progress and pool maintenance are ordinary private state transitions. `docs/baton/interfaces.md:136–140` does not require new `on_block`, `on_commit` or native execution callbacks.
- **Full Baton changes to canonical order:** the entry guide `:69` and direction `:87–97` explicitly preserve the unresolved authenticated proposal/adoption/preservation/continuation/recovery work. Local advisory scheduling cannot establish that result by rearranging existing Updates. The removal of extra layers has not hidden this native protocol obligation.

## Simplicity and invented-boundary check

The primary navigation in `docs/README.md:7–15` remains App composition → concise pool contract → callbacks → scheduling → normal E2E. The long backend survey is optional after the pool contract. The overview interfaces page links detailed contracts instead of restating all pseudocode. Old public names appear only in the glossary's collapsed historical mapping, negative scope statements, or existing third-party source terminology; they are not prescribed interfaces.

No extra review approval, execution-result gate on verify, pool-processing ACK, result-certificate wait for direct apply, per-box actor requirement, origin field, Update generation field or new block validation layer was found in this reader path. No additional core rewrite is justified by this pass. The sole companion correction above resolves the stricter-than-core speculation retention wording.

`git diff --check` passed. Repeated docs build/render and protocol tests were not run for this single prose edit. Backend/VM/payload policy, concrete comparator, message format, resource budget, cross-store recovery and full native Baton proof/implementation remain open exactly as documented.

## Reviewed document fingerprints

| File | SHA-256 |
|---|---|
| `docs/baton/README.md` | `4fc0f382071023391145df6db72f3f0f225abd03776386ab6371f0a5bc32a719` |
| `docs/baton/interfaces.md` | `583dd99555e3feeaaa8d05e98b4c64c5e1bc939f39ba93f2848019c75eb25623` |
| `docs/baton/direction.md` | `60f00a686c6301f5df04c96e78aa0739a6a2caeac4e06d23f6c1ffc908cf7cf3` |
| `docs/tx/interfaces.md` | `000d26910db81d098c24bb15bde475a83561c0474e462718a2226767a728a7c2` |
| `docs/e2e/block-body.md` | `1c4cd476ac70270de36c9aa0d861b25ee97e43f13dc43b0916c8948b88ed9cae` |
| `docs/e2e/canonical.md` | `b3481d8185aa6b8cf388b77ac0d78e53194c4dbab62a3e81c6bb69adc59aba66` |
| `docs/overview/glossary.md` | `ce8df8e404fa8f2562ce9a8803a4404256bb64653f24b6af0df8456211e34ddb` |
| `docs/overview/networking.md` | `9b6f40ebf53c6b7c83a8e01c63d3daab0c5d71fcdb8c8b2971af484600a7176f` |
