# Round 2: minimal app ownership and preserved semantics

Reviewer: `/root/simplification`. Read completed 2026-10-09T07:13:36+00:00. Source `6233438985d8249d2b2bc1204191d5d405652288`. Design/source review only; no execution tests or proof closure.

## Finding and smallest correction

1. **Bounded Update intake must include floor transitions.** Root `docs/baton/interfaces.md`, Update inbox paragraph, recommends a bound compatible with `max_pending_acks`. Current `consensus/src/multimmit/marshal/actors/delivery/actor.rs:423-451` resets the pending window when a floor is installed. Previously emitted Updates can remain in App while a fresh window opens, so repeated resets are not covered by a single-window bound. `Update` (`marshal/types.rs:130`) carries no generation field. The smallest correction is to coordinate the existing App floor/import transition with intake, reconcile old exact indices/blocks and bound any overlap. No new service, durable scheduler journal or native flag is needed. Root accepted the finding; this reviewer added the explanation/source to owned `docs/execution/state-sync.md`. Root/peer owners are updating their callback, consensus and E2E pages.

2. **Current-source naming detail.** Root README initially spelled the internal path `actors::voter::app::AppExecutor`; current source lives under `actors/voter/actor/app.rs`. Reported to root. This is navigation accuracy only.

3. **Active database-access fencing should be named in canonical pseudocode.** `docs/baton/direction.md` says to fence incompatible worker results before canonical mutation. Other root/companion pages correctly distinguish rejecting stale results from preventing live DB reads/forks against an invalidated parent. A small wording change to include both access and result adoption makes the standalone pseudocode safe to follow. Current Any wrapper explicitly reads the shared applied database (`glue/src/stateful/db/any.rs:1-5`); rejecting a completion alone does not prevent those reads.

## No extra layer is needed

| Proposed removal / concern | Review result |
|---|---|
| Public TxPool / Baton / Executor / Storage declarations | New root pages use concrete App responsibilities and existing callbacks; no replacement generic framework is introduced. |
| Body service, ordinary native proof/order/cursor ownership | Delegated to current Multimmit Marshal; peer consensus page names actual supplied owners and App-specific validity/apply obligations. |
| Typed Reporter handles | Necessary because Reporter has one associated Activity per implementation. Two small ingress handles into one App do not imply two services. |
| Execution worker and canonical writer | Necessary responsibilities, not public traits or mandatory actors. Root prose explicitly permits shared owner/concrete handles. |
| PreCut baseline | Independent mode without Baton reports/direction/native policy; shares ordinary eligibility/pending rule/backend/endpoints. |
| Rootless branching | Concrete retained effects/replay or overlay remains unresolved integration. No claim that sealed-parent QMDB forks solve an unsealed tree. |
| Native protected-prefix extension | Clearly still open; producer Automaton context cannot select a cross-lane leader cut and finalized Updates cannot be reordered. |

## Preserved contracts

- Verify is body/context validity plus required custody. Remote native eligibility, local pre-sign custody and Engine::open recovery are distinguished. Missing body/dependencies stay pending; false/closed receiver is terminal. Successful custody does not await speculative execution or queue capacity.
- Scheduler admission and dispatch are distinct. Preserve started F, sort pending only, require exact execution parent and distinguish producer-header ancestry. A/C/B examples, no hypothetical-B barrier and canonical repair remain explicit.
- Report intentions retain original context/identity, once-only first-4f+1-or-fixed-deadline closure, bounded complete candidate evaluation, 2f+1 ENTIRE-prefix priority and raw sum-LCP fallback. No direction ACK/Ready quorum; native cut never waits on planning.
- Adoption/availability/leading-order/continuation/view-recovery remain open. An adopted authenticated protected prefix cannot disappear into base fallback. Native tip extraction/extensions and extra inputs are preserved.
- Update callback retains complete block/index/Exact and returns synchronously; Backoff is not a retry protocol. Durable apply precedes ACK, and Marshal cursor sync follows separately. Crash between them redelivers idempotently by exact identity.
- Canonical effects can be reused, completed/repaired or imported under the same writer. No unconditional rerun after finality. Root preparation is separate from computation and precedes result signing.
- Result endpoint remains irrevocable exact input/base/runtime/result plus f+1 distinct eligible signatures. Direct local apply can proceed while peer signatures are collected; imported work needs certificate/material and retains imported provenance.
- PreCut/Baton use the same callback contract and state backend. Full Baton may change the authenticated canonical sequence only through the explicitly missing native extension; “same stream” should be read as shared delivery contract, not a guarantee of identical experiment orders.

## Simplicity assessment

The three Baton pages have distinct reader purposes: assembly/ownership, callback behavior, and scheduling/research policy. Some completion boundaries intentionally repeat at entry points; these repetitions do not introduce conflicting owners or an unnecessary interface. No broad restructuring is recommended in this round. Keep detailed crypto/QMDB/backend alternatives in companion pages and link them from the callback walkthrough.

## Readback fingerprints

- `docs/baton/README.md`: `0ec45406eaa1cee46232b364322c87743466a57db83bcf7e054abc574fcc1e1b`
- `docs/baton/direction.md`: `6368d5c8a5ab3f9380d3aa7eea8479145955df9b278d6bcdc349cdf990c27350`
- `docs/baton/interfaces.md`: `39993bdf15709e1ea1a6dfd1369c5bd29372ef2aca6369819936c84e6417256b`
- `docs/consensus/decisions.md`: `ae57166bbab81443de014003fb01bcfececc90eb330205647a7881cf0c5a4f56`
- `docs/consensus/ordered-input.md`: `9d9b8789c52e481e146512d457b66133b50b456a83b0d29df4f324bedc9d8a89`
- `docs/e2e/canonical.md`: `593108a1879ab9f7f84097d1dc131489c7972f04a364ad5b6415f002de41cc71`
- `docs/e2e/normal.md`: `80e34bbeeee89c22a59cbace018f91807437b2876e972575b3efd6755145beae`
- `docs/e2e/recovery.md`: `c3c935732eb66af08c1dab4976b7476ae23443107d5f0b0f35f3b754cdcdbe9a`
- `docs/e2e/state-sync.md`: `e00e99119353ac6a6ccb33fa89c482841c62441bb41e8efe10fe9105f1a5973b`
- `docs/overview/architecture.md`: `ecbd3de3bf9e4d234c8b890c6af48d450a6ce82a4cb236970a10da1bf0d0328f`
- `docs/overview/glossary.md`: `220bf5e434ebbe3e1978b9a4841d7db7281bc83d16f562a28dfa8f18234c6fe1`
- `docs/overview/interfaces.md`: `c01dceeba5f229abeb2c387116c9347fd39c5b3ab3e2e107e641991f9dd3aead`
- `docs/overview/networking.md`: `301efa5ca25405c2112de729d9664d9e5ad105519c0be34ce1d413e967031951`
- `docs/overview/rust-interfaces.md`: `9e70ef992f5408ede240e41c513307332475cb39139797b90c25b3b246be5920`
