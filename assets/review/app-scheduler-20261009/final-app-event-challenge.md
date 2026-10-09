# Final App event challenge

Reviewed 2026-10-09, 09:44 UTC. This is an analytical trace of the current design text, not an implementation test, liveness proof or claim that the App integration exists. Reader documentation was not edited.

**Finding: no unresolved contradiction in these four traces.** Existing callbacks, App ownership and the existing Marshal/QMDB mechanisms can express the required transitions without another public trait, execution service or approval protocol. Concrete capacity, result-switch and multi-store recovery policies remain implementation work.

## 1. One delivery slot: `max_pending_acks = 1`

1. Marshal reports `Update(j)`; App retains its complete identity, block and Exact token and returns promptly. The occupied slot prevents delivery of `j+1`, while native consensus continues.
2. App obtains the exact predecessor, finishes valid direct work, prepares the selected root and completes covering durability plus recoverable state/output/applied-identity/provenance linkage. Optional speculation, report crypto or planning cannot monopolize the resources required for these steps.
3. The App owner accepts that durable completion once, schedules pool maintenance and ACKs `j`. Marshal can release this contiguous acknowledged slot and deliver `j+1`; its cursor durability is a separate boundary.
4. Neither a certificate covering future Updates nor pool maintenance completion is a prerequisite. A batch policy that withholds this ACK until `j+1` arrives is explicitly forbidden. Larger signing ranges remain possible when durable application and ACK progress independently. A worker that yields no reusable output must settle its attempt and release resources only once it never started or safely terminated; retained canonical input remains available for the selected repair/recovery path.

Evidence: `docs/baton/interfaces.md:87, 96–120, 124–135`; `docs/execution/interfaces.md:48, 60–66`; `docs/consensus/ordered-input.md:27–31`; `docs/tx/interfaces.md:29`. The resource-progress requirement specifies no new quota or service. Ordinary valid transaction reverts remain execution outcomes under `docs/baton/interfaces.md:63`.

## 2. Observer encounters a block first through canonical delivery

1. An Observer has no live per-chain validation plane. Marshal's trusted local `Update(j)` is its first encounter with the block; no earlier `verify`, pending candidate, activity hint or local pool entry is assumed.
2. App retains the Update, performs the application checks needed for execution and obtains the exact canonical predecessor. Transactions are checked under agreed payload rules even when they were never selected or admitted to this node's pool.
3. App executes directly, durably applies through its canonical writer and ACKs using the same boundary as trace 1. Missing speculative work is a performance condition, not a missing authority or callback.

Evidence: `docs/baton/README.md:46–64`; `docs/baton/interfaces.md:93, 100–120`; `docs/tx/interfaces.md:17`. Observer application does not imply eligibility to issue validator result signatures; signer eligibility remains the separate contract at `docs/execution/interfaces.md:58–62`.

## 3. Earlier verification finishes after durable application

1. On a live validator, a verification request is awaiting asynchronous custody/completion handling. A canonical Update independently supplies the same block, and App durably applies its exact index and identity.
2. The earlier verify completion re-enters the App owner. It checks current lifecycle and exact epoch/context/block identity rather than using the pre-await view of pending work.
3. If its custody verdict is still required, it returns an honest verdict from validity and durable custody. Already-applied state prevents speculative re-admission or a new execution attempt; being already applied is not a reason to return `false`.
4. Concurrent/repeated verification can refresh facts but cannot reset an existing attempt to pending. A late worker completion separately needs current-attempt identity and one-time acceptance. These are ordinary owner checks, not a new native callback or an execution wait in `verify`.

Evidence: `docs/baton/README.md:60, 64`; `docs/baton/interfaces.md:59–67, 72–87, 112–118`. This trace uses a validator deliberately; it does not invent live verification for an Observer.

## 4. Certified import arrives while the direct writer is mutating

1. The direct canonical writer already owns the exact transition and has a by-value mutation or covering flush in progress. A peer result arrives concurrently. App validates the full certificate and applicable material, but neither possession nor validation transfers writer authority.
2. The import path respects the same writer and access fences. It cannot cancel the mutation by dropping a waiter, reuse a partially applied DB as a different delta's base, or treat readability as durable completion.
3. After successful direct durability and recovery linkage, App accepts the durable completion and can ACK the covered Update. The prepared import must recheck current predecessor/applied identity. If the target is already covered, it does not apply effects again or replace direct provenance merely because a certificate arrived. A later applicable import can use the shared writer under the still-open switching policy.
4. If certified import instead acquires authority before direct mutation begins, it fences incompatible direct work, durably links imported provenance and ACKs only covered exact input. Merely importing does not authorize an own direct-execution signature. If mutation/barrier fails, the affected instance is not reused; recovery establishes authoritative state before any success ACK.

Evidence: `docs/execution/state-sync.md:3–15`; `docs/execution/README.md:29`; `docs/execution/qmdb.md:123–135`; `docs/baton/interfaces.md:102–115`; `docs/execution/interfaces.md:58–66`. The two legal authority orders do not choose a winner-selection policy. Matching multi-store checkpoint selection remains explicit App integration work, not a guarantee supplied by QMDB or Marshal alone.

## Reviewed file fingerprints

Raw SHA-256 at the review snapshot (paths relative to `baton-research/`):

| File | SHA-256 |
|---|---|
| `docs/baton/README.md` | `bfd48640fe6b7b2d0599e9c8780eac38046804253b221617db5c8265632dfd82` |
| `docs/baton/interfaces.md` | `6749e395b567dfecaf98f367271cd6d5a8df76e29fc6536e0279d516d2fb4755` |
| `docs/execution/README.md` | `7ed0be32734248b825e50e4de88f9185937aaf56cf369de0e90c535200fc4be6` |
| `docs/execution/interfaces.md` | `733f5460b1facb14ebcba05e2f28d5840c5fdb0d97dbf7e1d3097b61c9a75538` |
| `docs/execution/qmdb.md` | `ed8eaf8444a2e2c6013118586984824f6b4222c6f2b3992c55a776a57748ccda` |
| `docs/execution/state-sync.md` | `7e5dac91af51a829e8b04bac1bd411844f82c821f007bb8ae511e5832d1aad21` |
| `docs/tx/interfaces.md` | `000d26910db81d098c24bb15bde475a83561c0474e462718a2226767a728a7c2` |
| `docs/consensus/ordered-input.md` | `8fb5fb111c1da587c2968e82c61c0f0ceb6214e1f6f641e7b85613f20ae7ef04` |
