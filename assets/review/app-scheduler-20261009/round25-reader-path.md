# Round 25: new-reader callback and body path

Read-only reader-path audit of current `docs/baton/README.md` → `docs/baton/interfaces.md`, the actual body reference, visual body sequence, App scheduler and pool entry pages. This reviewer edited only this report. Root subsequently applied the two narrow reader edits below; no policy selection, rendering or external action was part of this review.

There is no `multimmit-body-availability.md` in the research or parent repository file inventory. The actual reference is **`docs/consensus/block-body.md`**, linked by `docs/baton/README.md:38` as “Body flow”; visual sequences are in **`docs/e2e/block-body.md`**. No alias file or new availability layer is needed.

## Findings and minimal proposals

| Priority | Exact evidence | Reader impact | Smallest proposed edit |
|---|---|---|---|
| Low, worthwhile title cleanup | `docs/consensus/block-body.md:24` says “Reuse the same body components as Tempo”; `:26` actually instructs using directly compatible current `log-multimmit` assembly and treats other chains as historical references | The heading leads a new reader toward a third-party chain dependency when the table directly below is entirely supplied Multimmit Marshal APIs | Rename H2 to **Use Marshal's existing body APIs**, keeping `<a id="reuse-the-same-body-components-as-tempo"></a>` for existing links. Keep current native composition and source evidence; no implementation/policy change |
| Low, useful focused deduplication and navigation | The final two sentences of `docs/baton/interfaces.md:59` describe fetched bytes arriving while an earlier subscription is pending, establishing custody with put/stage and retiring the old wait. `docs/consensus/block-body.md:37–39` already owns the complete API distinction and race recipe. The callback page has no direct internal link to that body reference | After the high-level README, the callback reader encounters a specialized storage/subscription race inline, then must return to the README or find the body page through the sidebar for its full API table | Replace **only those two final sentences** with a direct link to the body page's preserved anchor, e.g. “See [active retrieval and subscription races](../consensus/block-body.md#reuse-the-same-body-components-as-tempo) for the body-fetch path.” Retain the receiver/sender, false-versus-pending, subscribe durability and get/fetch-before-durability sentences |

The evidence positions in the findings table refer to the pre-edit text. These are simplification/navigation changes, not correctness failures. **Root applied both proposals.** Fresh readback confirms `consensus/block-body.md:24` preserves the old explicit anchor, `:26` is “Use Marshal's existing body APIs,” and `baton/interfaces.md:59` now links directly to the new section anchor. False/pending, successful-subscription custody and get/fetch-before-durability rules remain in the callback paragraph; the full fetch-first race recipe remains at body reference `:39–41`. Root reported its docs check passing 32 pages / 253 links / 19 diagrams / 38 open cells; this reviewer did not rerun that global check. No larger rewrite is justified by this pass.

## What the new reader can already determine

| Question a reader asks | Current answer/location | Result |
|---|---|---|
| What do I implement? | `baton/README.md:3,15–23`: one App with pool, one of two scheduler modes and transaction state; current Engine and Marshal are supplied | Clear; no required public TxPool/Baton/Executor/Storage/BlockService/Orderer |
| Are App, callback handles and workers separate services? | `baton/README.md:40`; `baton/interfaces.md:5–7`: typed handles route to the same App state. Different Reporter associated types explain the handles | Clear ordinary wiring; no mandatory extra actor/service |
| What leaves the pool? | `tx/interfaces.md:9–17,20–31`: stable selected bytes within dependencies/work/body bounds become a contextual full block; selection does not canonically retire txs | Clear; tx policy is not remote block validity, and the pool is not custody |
| Do I implement block storage/fetch/Relay? | `consensus/block-body.md:28–41`: use existing Marshal stage/put/subscribe/fetch/get/Relay and resolver bridge | Clear; App implements body codec/digest/payload validity, not another BlockService |
| Why can a node have only the header? | `baton/README.md:38`; `consensus/block-body.md:7–14,56`; `e2e/block-body.md:27–32` | Separate native signed-header and Marshal complete-block planes, with no arrival-order guarantee |
| Why are there two digests? | `baton/README.md:33,38`; `consensus/block-body.md:9–13`; `e2e/block-body.md:39` | Body digest is the Automaton result/input; contextual header digest is Relay lookup identity |
| Does stage completion mean durable storage? | `baton/interfaces.md:23–29`; body API table `:32–39` | Accepted work/token differs from successful durable wait. Local verify is before signing; there is no compulsory second flush after successful subscription |
| Does verify execute transactions or mean another-lane receipt? | `baton/README.md:46–64`; `baton/interfaces.md:36–67` | No. Remote/local-pre-sign/recovery and role/lifecycle checks qualify it. App finishes valid custody and records useful metadata; exact-parent dispatch is separate |
| Who queues and starts pre-cut work? | `baton/interfaces.md:65–87`; `baton/direction.md:20–37` | App owner deduplicates metadata and claims/reserves a current attempt; selected scheduler sorts pending only and starts after the true execution predecessor is ready |
| Must I choose a mempool now or create another actor to adapt it? | `docs/README.md:10,15`; `tx/interfaces.md:35–49`; `tx/README.md:21,47` | Pool contract comes first; survey is optional conditional reuse evidence. Existing backend actor paths are adapted if chosen, not wrapped by a required second pool |
| Does Update call the scheduler for permission? | `baton/interfaces.md:91–143` | No. Retained canonical input has independent exact-order reuse/repair/apply processing, including first encounters without verify. Scheduler/pool notifications add no approval |
| Does ACK wait for execution? | `baton/README.md:70–74`; `baton/interfaces.md:100–135` | It waits for matching durable application. Exact completed speculation avoids rerun; absent/mismatched work must finish first. Native voting/finality do not await the App ACK |
| Is body custody the same storage as canonical state? | Body API table and validity boundary `consensus/block-body.md:20,30–41` versus `baton/interfaces.md:104–115` | Distinct objects/completions are explicit: retained full block versus executed durable App state. Both use supplied mechanisms without merging their semantics |
| Can App-only Baton change finalized order? | `baton/README.md:84`; `baton/direction.md:89–97` | No. Native authenticated policy/adoption/continuation remains separate open work; no facade disguises it |

## Repetition that should remain

- README's entry-point table answers **what the callback means**; the callback page answers **how App handles it**; the body reference table answers **which existing storage/fetch API supplies each completion**. Those are different reader questions and do not duplicate owners.
- Short reminders that verify also handles local/recovery work and never waits for speculative completion protect independently visited body/E2E pages from being interpreted as “one callback equals one peer receipt.” They should not all be deleted merely to reduce word count.
- The body diagram sometimes shows `true` before optional scheduler admission while core pseudocode records pending metadata before sending `true`. Neither waits for execution, both require current-owner eligibility checks and later exact-parent dispatch; no externally observable admission ordering guarantee is adopted. A larger diagram rewrite is unnecessary.
- “App TxPool,” “App Automaton,” and execution/storage participants name internal responsibilities. The entry text explicitly rejects required new public layers; relabeling every participant would add churn without improving ownership.

Open comparators, capacities, backend choices, transaction semantics, root schemes, result formats and protected-prefix policy remain open. No policy was filled to smooth the reading path.

## Reviewed snapshot

The following hashes identify the reviewed files **after root's two edits and this reviewer's focused readback**. Later owner edits may legitimately change them.

| File | SHA-256 |
|---|---|
| `docs/baton/README.md` | `bfd48640fe6b7b2d0599e9c8780eac38046804253b221617db5c8265632dfd82` |
| `docs/baton/interfaces.md` | `6749e395b567dfecaf98f367271cd6d5a8df76e29fc6536e0279d516d2fb4755` |
| `docs/baton/direction.md` | `c2bf3f623226c3ac8936a1ca2f2f59e1053992f47c595e20b191dd8d07345e35` |
| `docs/consensus/block-body.md` | `07a300c13e0719f56dd6d44f118371ee43bbdd595007875b2ab453a42ccaad79` |
| `docs/e2e/block-body.md` | `d88e71e79fa2f09967f27de07907a81d1cf306eaa76281cd4cb14d8bfe2b4032` |
| `docs/tx/README.md` | `124ffa9fcac7060ccff9d2614ad40d871345a77e01d60e9be444beda98b8b510` |
| `docs/tx/interfaces.md` | `000d26910db81d098c24bb15bde475a83561c0474e462718a2226767a728a7c2` |
| `docs/README.md` | `f3fcb23974477d9f7a064b1b9acf1fc36372175f43524746f8c95480175fdefa` |
| `docs/SUMMARY.md` | `1651f058c94fba2b36433bc974e28880d6e9a48ca7c0d7a4da56d041841499ac` |
