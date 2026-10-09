# Round 12 — Adversarial App event traces

These are analytical event traces against the current design and inspected source, not executable tests or proof of implemented behavior. Unless noted otherwise, each trace applies equally to PreCut and Baton. `A`, `B`, `C` denote exact block/context identities; `AB` denotes the execution checkpoint after that exact input prefix, not a producer-header parent. No new public trait or actor is introduced below.

## 1. Verify and canonical Update become ready together

```text
t0: canonical App base is A; verify(B) is waiting for custody completion
t1: Marshal reports Update(42, B, token); App retains it synchronously
t2a: verify completion is processed first
     -> owner admits B once; dispatch claims attempt (A, B, runtime, attempt-id)
     -> canonical worker finds that exact attempt and finishes/reuses it
t2b: canonical execution is processed first
     -> it performs required App checks and owns work for exact A -> B
     -> late verify refreshes facts, without re-enqueuing that claimed work
t3: selected exact AB is durably applied and linked; owner advances once; ACK token
```

**Required result:** no missing canonical work because an earlier verify was absent; no duplicate dispatch of an already claimed exact attempt; no ACK at callback receipt. Canonical execution/repair shares the App execution tree/current-attempt ownership with speculative work. It does not need a candidate entry to exist first. A different speculative parent would be distinct work and cannot substitute for A→B.

**Existing owner/mechanism:** App owner serializes candidate/current-attempt changes; the same execution backend serves canonical and speculative work; Marshal supplies the actual indexed Update/token. `baton/interfaces.md:63,67-83,96-114` and `execution/interfaces.md:16-50` cover these rules. Current `delivery/actor.rs:315-327` calls the synchronous reporter and then retains its waiter.

**Open choices:** concrete App event storage/serialization and job representation. These do not require a second canonical-execution registry, a new callback or a public scheduler/executor interface.

**Assessment:** pass as designed; eventual implementation must use the same exact-attempt ownership for canonical execution, not treat “canonical worker” as a separate unsynchronized execution namespace.

## 2. Custody completes after the block was already applied

```text
t0: verify(B) begins; its asynchronous completion is delayed
t1: App durably applies Update(42, B) through the canonical path
t2: verification completion arrives with the original body/context
t3: owner rechecks current applied position and lifecycle
     -> no new speculative B entry or worker
     -> still-required valid custody request receives true
```

**Required result:** applied input is not resurrected as pending work. Already applied does not make the payload invalid. If native canceled the original request, cleanup of that obsolete response cannot turn into a new eligibility grant for retired/stale work. A remaining useful candidate must satisfy current identity/lifecycle/eligibility, independently of the old response.

**Existing owner/mechanism:** `baton/interfaces.md:45-63` performs the check after the await; native response cancellation already exists. The example `application/actor.rs:59-118` races `response.closed()` against `subscribe_block`. Marshal's `service/subscriptions.rs:3-6,91-104` coalesces callers and keeps begun durable settlement independent of caller cancellation. No second App body-custody store is needed.

**Open choices:** bounded metadata retention and admission horizon; native/body retention and application-execution retention are different obligations.

**Assessment:** pass. Cancellation/late completion is not permanent invalidity, and custody completion is not scheduler dispatch.

## 3. A shared-parent branch is replaced while a worker is running

```text
t0: AB is completed; worker C is running from AB with a live QMDB-backed draft
t1: eligible D arrives
     -> ordinary arrival preserves the started ABC path; D stays pending
t2: canonical Updates instead require ABD
     -> reuse AB only if exact execution and concrete storage ancestry match
     -> revoke adoption of C and fence its incompatible live DB accesses
t3: canonical writer applies/persists D from AB
t4: old C computation may still finish; reject its retired completion
     -> release its retained resources only when actual work/other obligations permit
```

**Required result:** late arrival alone does not rewrite `F`. Confirmed order can require repair/replacement. A local generation check at t4 is insufficient: after t3, C must not lazily read D's sibling-applied state as if it were AB. If the chosen implementation cannot safely fence those reads, it must wait for safe access ownership before that mutation. This is a local writer/access constraint, not a consensus ACK gate.

**Existing owner/mechanism:** App owner/current attempts plus one canonical writer and concrete batch handles. `execution/qmdb.md:65-69,107-109` explicitly separates stale-result rejection from access fencing and retention. `glue/src/stateful/db/any.rs:106-117` reacquires current DB state for batch reads; `db/mod.rs:148-167` warns about nested writer-preferring read-lock acquisition. Runtime completion handles may only stop waiting (`runtime/src/utils/handle.rs:27-31`).

**Open choices:** the concrete access-fencing/cancellation protocol and resource policy. If AB is rootless, replay/overlay materialization from a valid anchor is App work; no unsealed-parent QMDB fork is assumed. For Baton, replacing a started path solely because an advisory direction disagrees remains explicitly undecided; t2 above is canonical input, not an adopted advisory-override policy.

**Assessment:** pass. No extra branch manager service is required, but the access fence cannot be omitted from implementation.

## 4. The same current attempt reports completion twice

```text
t0: owner claims attempt j for A -> B, reserves resources and records j before launch
t1: completion(j, AB, runtime) is accepted; effects/output/provenance retained once
t2: duplicate completion with the same generation and identity is delivered
     -> current-attempt acceptance is already consumed; ignore as duplicate
t3: repair later starts attempt k on A -> X -> B
     -> another late completion(j) cannot satisfy k, even though block B matches
```

**Required result:** one completion cannot advance `F`, release capacity, publish results or schedule successors twice. Block equality or generation equality is insufficient; exact current attempt and parent/runtime matter. Failed launch can release an unstarted claim only if work never began and resources are actually releasable.

**Existing owner/mechanism:** owner-serialized claim/attempt state and acceptance-once (`baton/interfaces.md:67-83`, `execution/interfaces.md:18,31-35`). Existing runtime task/result handles are transport for this work, not automatic proof of semantic deduplication. Existing in-memory collections suffice; no new generic job-state protocol is required.

**Open choices:** attempt ID representation and resource accounting. Accepting once is an adopted invariant, not an open policy.

**Assessment:** pass; later code must make duplicate rejection include one-time resource/accounting effects.

## 5. Verified import arrives during direct durable I/O

```text
t0: direct canonical A -> B owns the writer; apply/finalize is in progress
t1: peer supplies a valid certificate and material originally applicable from A
t2: App verifies/prepares candidate material using safe separate storage ownership
     -> it cannot abort/drop the direct by-value mutation to seize its database
t3: direct operation settles; B's exact durability/linkage outcome is known
t4: import rechecks current predecessor and writer authority
     -> if already covered: retain useful certificate/material, do not apply twice
     -> if the old A-based delta is no longer applicable: do not apply it to B
     -> adopt a further target only through a newly valid material/handoff check
```

**Required result:** no simultaneous direct/import canonical mutation; no delta silently rebased onto partially executed or newly advanced state; no ACK after failed durability. If mutable storage fails, stop using that instance and recover authoritative state. A successful import retains imported provenance and never creates an own direct-execution signature for merely imported work.

**Existing owner/mechanism:** the same canonical writer, predecessor recheck and existing QMDB mutation ownership. `execution/state-sync.md:5-15,31-35`, `execution/qmdb.md:55,125-133` cover the handoff. `ManagedDb` explicitly loses the instance on error/cancellation (`glue/src/stateful/db/mod.rs:334-336`); `apply_shared` holds an empty WriteSlot until restoration (`1850-1857`); tuple apply/finalize do not make independent App metadata atomic (`1041-1065`). A second handle to the same sync partitions is not isolated candidate storage (`storage/src/qmdb/sync/journal.rs:22-28`).

**Open choices:** compatible-target selection, checkpoint switch, pending import budget, and exact cross-store recovery. A finalize method may already have returned a pending durability barrier; the chosen schedule may exploit permitted pipelining, but cannot misattribute that barrier to later work or discard it as if it canceled I/O. No blanket per-block signing/durability policy is selected here.

**Assessment:** pass. “Valid import can replace unfinished direct work” is correctly constrained by the safe handoff, not an instruction to preempt active mutation.

## 6. Crash after apply, before observed durable completion

```text
t0: A is the coherent durable App checkpoint; Marshal cursor covers A
t1: QMDB apply(B) returns; DB is readable at B
t2: some persistence may occur; before App observes complete durability/linkage, crash
t3: restart finds one or more DBs at B, but output/provenance/applied metadata may lag
     -> do not infer coherent B from latest DB state or Marshal cursor alone
t4: recovery selects a matching App checkpoint and matching per-DB targets
     -> reopen with init(expected); later state is durably discarded as needed
t5: process Marshal replay against that recovered exact identity
     -> if matching B durability/linkage is established: ACK B without duplicate effects
     -> otherwise reexecute/import B from the valid recovered predecessor
```

**Required result:** unobserved durability does not imply B is absent after restart; a partial multi-store B is not an applied App checkpoint. Output and provenance recovery must agree with chosen DB targets, and the normal durable-application requirement still precedes ACK. Merely reopening readable B is insufficient. Retention must leave enough material to execute the recovery rule. A failed initialization or inconsistent target is not an ordinary successful resume.

**Existing owner/mechanism:** App recovery linkage plus existing `ManagedDb::init(expected)` / `DatabaseSet::init(..., Some(targets))`, journal/metadata/barrier mechanisms; Marshal separately redelivers. `execution/qmdb.md:125-129` states these limits. `db/mod.rs:334-366` allows nondurable state to be recovered or lost and requires durable truncation beyond selected target. Exact tokens are local completion signals, not durable transactions (`utils/src/acknowledgement.rs:38-101`).

**Open choices:** how the implementation chooses a coherent multi-store App checkpoint. This is necessary App recovery logic, but the docs neither invent a new WAL/commit service nor claim that QMDB automatically supplies that linkage.

**Assessment:** pass as a specified obligation; the unimplemented selection/linkage remains an explicit risk to resolve in implementation.

## 7. Local selection disagrees with a foreign/canonical block

```text
t0: local payload policy retains tx U as valid but unselected; tx V was never admitted
t1: local propose selects T and freezes its encoded bytes; pool later replaces T's entry
t2: valid peer block B contains U/V and may overlap T
     -> agreed payload rules validate B, not local selection/membership
t3: speculative execution computes state-dependent outcomes on its exact parent
t4: canonical input applies B; durable outcomes update/reconcile local pool readiness
t5: delayed pool cleanup does not withhold ACK, but stale readiness is not trusted
```

**Required result:** selection controls this node's proposal construction, not global payload validity. Unknown/unselected transactions are not automatically invalid; balance/nonce effects are resolved under agreed semantics and actual execution state. Proposal cancellation/replacement cannot change already committed body bytes or canonically retire selected transactions prematurely.

**Existing owner/mechanism:** one concrete App pool and stable body bytes; native complete body/Update is independent of local pool membership. `docs/tx/interfaces.md:13-31` states all these distinctions, including missed-maintenance reconciliation. The chosen backend's existing admission/selection/canonical maintenance is the reuse point. No public TxPool trait or required cleanup ACK is needed.

**Open choices:** transaction semantics, duplicates, static classification, backend and readiness/retention policy. External backend behavior was not freshly queried or reverified in this round; this trace checks the current local design contract, not compatibility of an adopted backend.

**Assessment:** pass. Both schedulers consume the same valid body and later canonical outcomes; neither obtains validity authority from local pool readiness.

## Cross-scenario conclusion

No confirmed new contradiction or materially missing execution paragraph emerged. The necessary state is ordinary App-owned identity, current attempts, retained tokens/material, writer/access ownership and recovered applied linkage. Those responsibilities are essential, but do not imply extra public actors or traits. Baton adds report/planning state only; none of these failure paths requires PreCut to instantiate Baton or wait for a direction.

No execution documentation, protocol source or runtime tests changed during this round. Source inspection and analytical traces establish consistency of stated obligations, not successful behavior of an implemented App. Final site/build verification remains owned by the root.
