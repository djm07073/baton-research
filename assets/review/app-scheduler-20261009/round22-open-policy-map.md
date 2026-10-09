# Round 22: all baseline open decisions mapped

Fresh extraction and semantic comparison use baseline `08cfe68b8b565fff4a0f8119cb36ec9b22062a31` and current working-tree documents. This audit compares every original label and its surrounding contract, not only counts or the four highlighted unadopted proposals.

The baseline has **39 blank Decision cells**: Baton 11, consensus 8, execution 10, tx 10. It also has **five blank Channel ID cells** outside Decision tables. Current documents have **38 blank Decision cells**: Baton 11, consensus 8, execution 9, tx 10. Networking now has three explicit `Undecided` App-plane rows plus supplied Marshal example channels. These scopes must not be conflated.

Result: no missing open semantic question was confirmed. No reader edit or replacement policy is needed. The execution row reduction merges replay/checkpoint/state-sync questions into their current owners; the consensus table keeps eight rows but changes their ownership and grouping substantially. Existing source implementations resolve several former mechanism questions without selecting production tuning, App state policy or the missing Baton native extension.

## Baton: all 11 labels retained

Baseline source: `docs/baton/direction.md:89–99`. Current source: `docs/baton/direction.md:103–113`.

| ID | Original label, verbatim | Current location | Semantic disposition |
|---|---|---|---|
| B01 | Window announcement / report / direction message codec | `direction.md:103` | Unchanged; window announcement remains an actual step at `docs/e2e/leader.md:16–20`, not inferred from a local timer |
| B02 | Report / direction logical channels and quotas | `direction.md:104` | Unchanged; no numerical channel/quota choice made |
| B03 | Concrete global comparator / deterministic tie-break / rule identity | `direction.md:105` | Unchanged; pending-only G is adopted, concrete comparator/encoding is not |
| B04 | Candidate set / horizon / finite work budget | `direction.md:106` | Unchanged; bounded completed evaluation does not pick a universe, horizon or budget |
| B05 | Conflicting reports within one window | `direction.md:107` | Unchanged; one identity once is required, equivocation handling policy remains open |
| B06 | Tail selection / hysteresis for the same supported prefix | `direction.md:108` | Unchanged; longest supported prefix is fixed, incumbent-first/tie policy is not |
| B07 | Concrete deadline and cycle-restart settings | `direction.md:109` | Unchanged; fixed deadline/first processed close rule does not choose timer values or restart settings |
| B08 | Wire direction version / freshness / update ordering | `direction.md:110` | Unchanged; complete context validation does not choose wire version or update ordering |
| B09 | Producer / validator dissemination targets | `direction.md:111` | Unchanged; roles are distinguished but no target set/overlap assumption selected |
| B10 | Native proposal adoption and policy-binding implementation | `direction.md:112` | Unchanged; also made explicit at `docs/consensus/decisions.md:25,27,29` |
| B11 | Execution signing scope / common boundary | `direction.md:113` | Unchanged; execution contract `docs/execution/interfaces.md:64–66` leaves per-block/chunk policy open and forbids slice/ACK-window shortcuts |

## Consensus: all eight original questions decomposed

Baseline source: `docs/consensus/decisions.md:23–30`. Current consensus rows: `docs/consensus/decisions.md:23–30`. Relative references in the table below are under `docs/`.

| ID | Original label, verbatim | Current location / remaining question | What changed and why |
|---|---|---|---|
| C01 | Body format / size limit / archive layout | `consensus/decisions.md:23` keeps App body format/hash/domain/transaction-byte bounds/validity open; `reference/integration.md:117` leaves archive/cache tuning to assembly | Body format/limits remain open. A new App archive layout is superseded by supplied Marshal `Config`/`ArchiveConfig`, not silently chosen from the old proposal. Native partition/retention/size settings still need configuration |
| C02 | Body transport adapter / fetch protocol | `overview/networking.md:27–35`; `consensus/block-body.md:26–39`; `reference/integration.md:117` | Existing buffered full-block transport, Marshal Relay and resolver bridge now supply the mechanism. Latest ownership requires reusing those; no new body-fetch wire protocol is required. App body codec and deployment timing/limits remain open |
| C03 | Targeted retry / fallback / pending want, subscriber, and byte budgets | `reference/integration.md:50,117`; `overview/networking.md:41`; `consensus/block-body.md:66` | Retry/fetch registry/subscriber mechanisms move to supplied resolver/Marshal. Numerical budgets, peer provider, resolver timing and App lifecycle handling remain explicit configuration work. Removing a bespoke pending-want/fallback framework does not mean capacities or production values were decided |
| C04 | Evidence export schema / retention handoff | `baton/interfaces.md:93`; `consensus/decisions.md:25,29–30`; `consensus/ordered-input.md:39–52` | Local ordinary native evidence transfer is now Marshal's authoritative Update/recovery path, so no new App order-evidence schema is needed there. Portable external evidence export is explicitly a separate **open** contract at `baton/interfaces.md:93`. Policy-specific frozen evidence/interpretation and App/floor retention remain open; Update is not declared a portable proof |
| C05 | Ordering policy codec / availability | `consensus/decisions.md:26`, with `:9` | Unchanged question; inline bytes versus retrievable commitment remains open |
| C06 | Protected-prefix adoption conditions | `consensus/decisions.md:27`, with `:14` | Unchanged question; no particular positive-adoption construction chosen |
| C07 | Exact continuation / extension / view recovery integration | `consensus/decisions.md:28–29`, with `:12–13` | Original question retained verbatim, with matching Marshal interpretation/persistence now explicit. Current ordinary order implementation does not settle Baton-specific continuation |
| C08 | Backfill / checkpoint / GC | `consensus/decisions.md:30`; `consensus/block-body.md:68–70`; `execution/README.md:44,47–49`; `execution/state-sync.md:39–43` | Ordinary native backfill/checkpoint/prune mechanism is supplied by Marshal. App checkpoint/import/floor coordination, independent execution/material retention, budgets and crash sequencing remain open. A second native backfill/GC service is superseded, not an App recovery requirement |

Source checks supporting these owner changes:

- `consensus/src/multimmit/marshal/config.rs:198–240` exposes catalog/resolver mailboxes, pending storage segmentation, ACK window and backfill concurrency. `:263–306` exposes encoded block/response, hot/materialized body, backfill and checkpoint byte limits. `:339–355` exposes startup, partition prefix, capacities/limits, retention, body codec and archive configuration.
- `examples/log-multimmit/src/marshal.rs:126–176` composes the existing buffer, Marshal and resolver, including provider/blocker, timeout/retry and priority settings. These example values are not selected production values (`docs/reference/integration.md:117`).
- `consensus/src/multimmit/marshal/actors/backfill/actor.rs:689–724` submits exact-key/subscriber work to the resolver. A new App fetch protocol is not needed to preserve the old question's required retrieval function.
- `AGENTS.md:13–19` / `BATON_HANDOFF.md:7–11` explicitly supersede the old absent-Marshal finding and old ordinary delivery/custody ownership.

Reverse check of the changed current consensus rows, so a new row is not mistaken for preservation of the same-numbered old row:

| Current blank row | Source of the still-open question |
|---|---|
| `:23` Application body format, hash/domain, transaction/byte bounds and validity | C01 plus existing App validity/codec obligations |
| `:24` App scheduling bounds, candidate retention and global-rule comparator/tie-break | B03/B04 and E06/E08 below, restated at integration boundary |
| `:25` Baton actual-leader-context / prepared-policy native hook | B10 and the baseline native-policy TODO construction/recheck steps; not a new adopted hook |
| `:26` Ordering policy codec / availability | C05 |
| `:27` Protected-prefix adoption conditions | C06 |
| `:28` Exact continuation / extension / view recovery integration | C07 |
| `:29` Policy-specific Marshal interpretation, persistence and recovery | C04/C07/C08 after ordinary Marshal reuse; future policy interpretation is still missing |
| `:30` App state-sync/floor coordination and application retention | C08 and E07/E08/E09; native floor alone cannot install App state |

## Execution: ten old rows mapped to nine current rows

Baseline source: `docs/execution/README.md:40–49`. Current blank table: `docs/execution/README.md:41–49`.

| ID | Original label, verbatim | Current blank row(s) and supporting contract | Semantic disposition |
|---|---|---|---|
| E01 | Application transaction semantics | `README.md:41` | Unchanged; no Bank/VM semantics selected |
| E02 | QMDB database variant / state encoding / root type | `README.md:42` QMDB variant / state encoding / result root | Renamed, same choice. `qmdb.md:9,57,83` distinguishes ops, Current and application result commitments without selecting one |
| E03 | Canonical operations / batch-boundary derivation / logical-root integration | `README.md:42–43` result root and deterministic canonical operation/batch boundaries | Split between result-root scheme and deterministic materialization. `qmdb.md:57,83` keeps logical values versus storage history/root distinction and explicitly leaves root/normalization/boundaries open |
| E04 | Root-deferred read/effects view / checkpoint sealing policy | `README.md:44` Root-deferred effects/read representation and checkpoint policy | Renamed, same choices. `qmdb.md:73–83` retains existing-draft replay versus overlay versus useful sealed checkpoints as alternatives |
| E05 | Block / parent-hash encoding and binding / checkpoint granularity | `README.md:45` Execution identity / parent binding / checkpoint granularity | Renamed to avoid confusing producer-header ancestry with execution identity. `interfaces.md:9` explicitly leaves concrete encoding open |
| E06 | Execution scheduling / cancellation / worker-fencing contract | `README.md:46` Worker placement / cancellation / access-fencing contract; `baton/direction.md:105–106` | Scheduling policy is with the App scheduler, worker/access contract with shared execution. Existing pending-only rule and progress requirements do not choose quotas, placement, advisory precedence or concrete cancellation/fence implementation |
| E07 | Atomic commit of state / outputs / cursor | `README.md:47` Recoverable linkage of state / outputs / applied position / provenance | Reframed to the actual consistency requirement. `qmdb.md:55,127–129` explicitly says neither DatabaseSet nor Metadata supplies cross-store atomic linkage; implementation remains open. Marshal owns its separate cursor, so a new all-stores transaction framework is not presumed |
| E08 | Branch pruning / memory / disk budget | `README.md:48` Branch retention / memory / disk budgets | Renamed, same questions. `qmdb.md:109` distinguishes logical retirement from safe physical deletion under live/reference retention |
| E09 | Replay / checkpoint / state sync | `README.md:44,47,49`, plus `consensus/decisions.md:30` | **Merged, not lost.** Checkpoint representation is E04; recovery/replay linkage is E07 (`qmdb.md:127–129` explicitly leaves matching multi-store checkpoint selection to App); certified material/switch protocol is `README.md:49` and `state-sync.md:15,31,43`. Marshal handles its own native replay, not App state recovery |
| E10 | Query interface / certified-result integration | `README.md:49` Query / result material / certified state-sync protocol | Renamed/merged with E09's sync portion. `qmdb.md:131–133` leaves query/historical scope open; `interfaces.md:64` leaves result format, keys, serving/retention and switch policy open |

Thus the missing *row* is the former dedicated E09 row; none of its three semantic questions was answered or removed. Restoring a tenth blank solely to keep the count at 39 would duplicate questions already owned by checkpoint, recovery-linkage and result/sync rows.

## Transactions: all ten labels retained

Baseline source: `docs/tx/README.md:73–82`; current source: `docs/tx/README.md:77–86`.

| ID | Original label, verbatim | Current blank location | Semantic disposition |
|---|---|---|---|
| T01 | Tx format / ID / signature domain | `:77` | Unchanged; backend examples do not select a transaction schema |
| T02 | Mempool implementation to reuse | `:78` | Unchanged; Nunchi/Reth/Constantinople remain conditional choices |
| T03 | Static-analysis implementation and admission result schema | `:79` | Unchanged; schema is internal App behavior, not restoration of a public TxPool result type |
| T04 | Selection policy and configuration mechanism | `:80` | Unchanged; selected-only and dependency preservation are constraints, not a packing-policy default |
| T05 | Tx P2P wire protocol / logical channel ID | `:81` | Unchanged; deployment chooses a compatible transport/codec/channel |
| T06 | Candidate selection order / byte and count limits | `:82` | Unchanged; work and full-body limits are required, numbers/order remain open |
| T07 | Application semantics of duplicate transactions | `:83` | Unchanged; pool-local dedup and canonical replay are explicitly distinct at `:33` |
| T08 | Durability of admission responses | `:84` | Unchanged; source graceful-shutdown backup is not adopted crash/per-admission durability (`:71`) |
| T09 | Proposal cancellation / reselection / retransmission | `:85` | Unchanged; source destructive selection needs explicit integration (`:29,67`) |
| T10 | Canonical cleanup / retention / GC | `:86` | Unchanged; durable outcome mapping and backend recovery/maintenance stay internal and open (`:49,67–71`) |

## Five networking blanks outside the 39-policy count

Baseline source: `docs/overview/networking.md:13–17`. Current source: `docs/overview/networking.md:13–19,41`.

| Original plane with blank Channel ID | Current location | Disposition |
|---|---|---|
| Application tx | `:15` App transactions — `Undecided`; T05 above | Still open |
| Application body | `:13–14` Marshal resolver example `4`, broadcast example `5`; qualification `:19` | Supplied Marshal assembly replaces a proposed body plane. Example channel IDs are explicitly not protocol-mandated or adopted production IDs; register compatible handles for the chosen deployment |
| Baton report | `:16` App Baton reports / direction — `Undecided`; B02 above | Still open; combining labels in one row does not select one channel for both message kinds |
| Baton direction | `:16` App Baton reports / direction — `Undecided`; B02 above | Still open; no direction channel exists in PreCut |
| Execution result / state sync | `:17` — `Undecided`; execution result/codec/sync choices above | Still open |

## Verification and scope

All 39 original Decision labels are present in the ledger, with no omitted label or reliance on their former row positions. All current 38 Decision cells have a source in the ledger: 11 unchanged Baton, the eight reverse-mapped consensus rows, nine merged/renamed execution rows and ten unchanged tx rows. The five extra networking blanks were checked separately. Counts describe the extraction; they are not a preservation oracle or an editorial target.

The legacy `check_docs.py --migration` 39-cell assertion is scoped to the historical migration check. It was not changed or used as proof of the current semantic mapping. No reader edit, native source change, new policy/default, runtime test or external write was made this round.
