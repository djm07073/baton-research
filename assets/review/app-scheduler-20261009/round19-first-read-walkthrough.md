# Round 19: first implementation read

Reviewer: `/root/docs_alignment`. Started at the current `docs/baton/README.md` after the Round 18 role-table reflow, then followed callback, scheduling, transaction and E2E references as a new implementer would. The review concerns navigation and explanation, not another protocol or callback-owner audit.

## Result and applied navigation improvement

The required path is complete: App composition → existing handles/assembly → local pool/proposal → other-lane verification and independent scheduling → ordered Update → local durable apply/ACK. No step requires understanding the old public layer names or following a circular link to recover an unstated contract. The role table makes the user's central other-lane question easier to locate without weakening the common lifecycle/identity filters.

One small navigation improvement was recommended and applied by root, not a missing-behavior defect. The first direct callback link in the main entry guide previously landed in the verify subsection, below startup and propose. A reader looking specifically for assembly could reach it through Architecture or scroll up in the callback page; the new direct connection link at “What App implements” makes that route explicit.

Immediately after `## What App implements`, root added this single sentence:

```markdown
Follow the [assembly and callback handlers](interfaces.md#assemble-before-opening-the-engine) for the connection sequence.
```

The destination already contains startup order and the exact integration link. This adds no duplicate recipe, new page, requirement or diagram. Root also retained the role table's actual `context.chain()` accessor spelling.

## Practical implementer walkthrough

| Implementer's next question | Read this existing path | Concrete answer available without old trait knowledge |
|---|---|---|
| What do I build and what do I reuse? | `baton/README.md:11–40` | Build one App's pool, selected scheduler, transaction runtime/checkpoints and state linkage. Reuse Engine, Multimmit Marshal, its Relay/body exchange and ordinary ordered delivery. Existing Automaton and typed Reporter handles form the boundary. No public TxPool/Executor/Storage/BlockService/Orderer implementation is required. |
| Which handles exist before Engine opens? | `baton/interfaces.md#assemble-before-opening-the-engine` → `reference/integration.md#body-assembly-to-implement` | Create App custody/output ingress, network/buffer/Marshal/resolver and concrete callback handles. App genesis/recovery binding exists and can service custody while Engine::open verifies retained work. Start native planes, await ready plus valid App base, then re-evaluate retained candidate state. Existing node ownership handles failed startup and shutdown. The source example and assembly pseudocode are local on the integration page. |
| What are the real Rust signatures? | Callback page's introductory `overview/rust-interfaces.md` link | Existing Automaton/Reporter/Relay/Update signatures and typed handle constraints. Propose/verify futures return receiver handles; the verdict arrives later. Reporter is synchronous. The excerpts are explicitly reference material, not a complete compiled transaction App. |
| How does client input become my local block? | README's App-pool row → `tx/interfaces.md:7–31`; callback page's propose section; `e2e/block-body.md#block-lifecycle-mempool--propose--body-dissemination` | Admit bounded valid txs under local selected/unselected policy; retain stable selected bytes; build TransactionBlock from native producer Context; stage it and return body digest through the receiver. Native local verify establishes durable custody before signing, then supplied Relay uses header digest. Selection, staging and verify are not canonical pool retirement. |
| Can successful verify mean another lane's usable block? | README `:46–64` → `baton/interfaces.md#automatonverify-validity-custody-and-scheduling`; body E2E | Only after successful live verification and role/lane, lifecycle and exact identity checks. Producer validators can compare context.chain() with their local lane; nonproducers have none to exclude; Observers normally use Update. Calls also occur locally and in recovery. Obtain exact full bytes/custody, update eligible pending metadata and resolve true without waiting for transaction execution. Duplicates and already-applied candidates do not become fresh speculative work. |
| When does that pending block actually execute? | The immediately following README admission/dispatch paragraph → callback dispatch subsection → `baton/direction.md#global-rule-for-local-execution-and-reports` | Pending admission can precede execution-parent readiness. Preserve started/completed F, sort eligible pending work only, and dispatch on the exact completed parent when capacity exists. The A/C/B example distinguishes arrival before versus after C starts. A producer-header parent is not the cross-lane execution checkpoint. |
| How do the two scheduler modes differ? | `baton/direction.md:5–16,47–99`; linked PreCut baseline through docs navigation | PreCut is ordinary early scheduling without reports/direction/native policy changes. Baton adds bounded authenticated intentions and advisory selection. Both use the same execution/canonical writer and Marshal Updates. Full protected-prefix canonical order still needs native authenticated adoption/continuation/recovery; no local Update sort pretends to implement it. |
| Who owns Update and what does report return? | README `:68–74` → `baton/interfaces.md#marshal-reportupdate-canonical-input-and-ack` | App synchronously retains the entire Update and Exact token, returns local Feedback, and runs an independent canonical worker. An earlier verify or scheduler entry is not required. Consume exact continuous indices, reuse/repair or import valid material and use the shared canonical writer. |
| What exactly permits ACK? | Same canonical callback subsection; `e2e/canonical.md#what-the-ack-waits-for` | Exact state/outputs/applied-position/block/provenance are recoverably durable. App advances once and schedules internal pool maintenance, then ACKs. Matching speculation can reduce remaining work to preparation/I/O; unfinished work must finish or be validly imported. Native voting/finality does not wait for App ACK, though the ordinary delivery window can fill. Marshal cursor I/O is later, so exact replay is idempotent. |
| What is the complete successful sequence? | `e2e/normal.md`; `overview/interfaces.md#finding-calls-in-e2e-cases` | The normal diagram joins local proposal, custody, asynchronous speculation, native Activity, Update, durable application and ACK. The body, native consensus, scheduling, canonical and recovery pages expand individual scenarios rather than redefine a second contract. |

With the applied assembly shortcut, the implementation route from the user's chosen `docs/baton/` entry is two purposeful clicks: README → callback startup → current-source assembly. The existing `docs/README.md` route already puts the callback page before scheduling, after the concise pool contract. The optional backend survey remains optional, so selecting a third-party pool is not a prerequisite for understanding the connection.

## Circularity and repetition checks

- The main guide introduces the contract and links to the handler. The handler defines the sequence directly and links back only for role context, or onward for concrete source/storage detail. It does not defer the same missing operation back to the main guide.
- `tx/interfaces.md` defines admission/selection/readiness and stable-byte maintenance locally; it links verify/Update for their behavior. Those callbacks select from and maintain the concrete pool rather than pointing back for an undefined consensus hook. This is normal topic ownership, not a circular implementation obligation.
- `baton/direction.md` owns the pending rule and report algorithm. It links one canonical Update worker rather than another delivery implementation. That worker is fully stated on the linked page and does not need a Baton report to proceed.
- E2E body and canonical pages retain scenario-specific timing explanations, then point to the canonical callback for exhaustive races, capacity and recovery. The approved paragraph cuts remain helpful; no second copy needs restoring.
- The short callback table in the entry guide and the callback page's full pseudocode serve overview and implementation purposes. The concise return/completion milestones are worth repeating locally; deleting them would make the user consult another page merely to understand whether a callback waits for execution.
- Existing links to QMDB, execution result certification and state sync terminate in concrete supplied mechanisms plus explicitly open App choices. They do not invent public layers to disguise missing work.

No further paragraph cut is recommended in this pass. In particular, keep the adjacent role conditions and admission-versus-dispatch paragraph: the first explains whether a callback represents eligible speculative input; the second explains why valid input need not start immediately.

## Scope and disposition

No companion page or diagram needed modification. Root applied the one-sentence navigation change. The role-table rendering uses normal Markdown, not a new generated asset. The documentation checker was run for the newly added link; no unchanged render/protocol suite was rerun. This report records a current-file reading walkthrough, not evidence that the proposed App implementation exists.
