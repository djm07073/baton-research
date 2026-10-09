# App execution and result certification

**The existing consensus callbacks enter one app; execution and storage calls stay concrete and internal.** The app chooses PreCut or Baton scheduling, validates exact parents, computes transaction effects, reconciles canonical Updates and owns durable state. No separate Executor, Storage, Runtime or ResultService trait is required.

## Interface overview

Use the [canonical callback contract](../baton/interfaces.md) for proposal, custody, scheduler admission and ordered delivery; the [Rust interface reference](../overview/rust-interfaces.md) contains the existing signatures and typed-handle wiring.

Execution jobs carry the exact input block plus the execution checkpoint selected by the scheduler. A producer's `Context.parent` identifies that lane's previous header. It cannot identify the predecessor in the merged execution sequence. The same body after different prefixes needs different execution identity. Bind completed work to canonical base, application/runtime/rule version and exact prior inputs; the concrete encoding remains open.

Candidate metadata identifies the exact block; an execution attempt also identifies its chosen path and parent. A duplicate candidate notification does not launch another copy of an active attempt. Repair on a different exact parent remains distinct work.

Preserve completed/current `F` and sort only pending eligible inputs. A state-dependent child starts when the valid predecessor checkpoint is ready. Missing/unfinished parents leave work pending. A new arrival does not cancel or relabel started work; a new canonical Update may require exact-parent repair. [Scheduling rule](../baton/direction.md#global-rule-for-local-execution-and-reports).

## Internal execution and apply flow

```text
on eligible candidate:
    on App owner, refresh facts for the exact header/context
    exclude already applied work; do not re-enqueue a claimed attempt
    admit eligible pending work once
    dispatch separately when the exact predecessor is ready

on execution completion:
    on App owner, accept the still-current execution attempt only once
    reject canceled, retired, duplicate, stale-context or invalid-ancestry completion
    retain completed effects, outputs and direct-execution provenance
    advance the valid speculative path

on ordered Update:
    retain index, complete block and ACK in canonical intake
    if durable applied metadata already covers this exact index and identity:
        acknowledge this redelivery; return
    when the preceding canonical input is applied:
        select valid exact-parent effects / complete or repair work /
            use verified applicable imported material
        prepare any required deterministic commitment
        recheck current predecessor and writer authority before mutation
        apply through the single canonical writer
        establish recoverable state + outputs + applied identity + provenance
        on App owner, reconcile durable completion with current applied identity
        advance the canonical base once or recognize the already covered input
        signal ACK for this exact durable Update
```

These are local handler steps, not proposed public APIs. Actual database calls use the chosen QMDB/DB handles. Root preparation consumes some unsealed drafts; retain exact effects before consuming the only representation if another branch or later prefix still needs them. A readable applied DB is insufficient for ACK until covering durability and the app's recovery linkage are established. [QMDB](qmdb.md#commit-a-branch-to-canonical-state).

Durable application and Marshal's ACK cursor are distinct stores. The app ACKs matching durable application; Marshal later syncs its cursor. Crash redelivery must validate exact index/block and avoid duplicate effects. A scheduler notification, pool cleanup completion or direction reply adds no approval gate. Pool maintenance can replay from durable outcomes under its backend contract.

<a id="result-certification-trait"></a>

<a id="result-certification-inside-executor"></a>

## Result certification inside App

App result-message handlers use existing authenticated P2P and crypto directly. Baton report/direction handling does not relay or gate execution certificates, state sync or apply.

A direct signer requires its own completed execution/validation evidence, a prepared full result commitment, irrevocable exact input and the correct canonical input state. Bind epoch, range, exact ordered inputs, canonical base, runtime/rule and selected result/output/material commitments. Local worker generations and writer permits are not stable shared signature fields. Advisory speculative order alone does not satisfy the signing condition.

Collect signatures only after validating the full subject, eligible epoch identity and signature. Count each identity once. State finalization requires `f+1` distinct matching signatures plus verified irrevocable order and canonical input-state linkage. Eligible result signers need not belong to the particular ordering QC. Fewer signatures are an incomplete certificate, not a reason to pause native consensus or subsequent valid direct work. A root alone or transport response count is insufficient.

An imported verified result retains imported provenance. The app may relay/serve the original certificate; it cannot issue its own direct-execution signature for work merely imported. It can directly execute and sign a subsequent range from the imported canonical checkpoint. Certification, material availability and local durable/read readiness remain separate milestones. [State sync](state-sync.md#state-sync-from-certified-execution-results).

Per-block/per-chunk boundaries, statement codec/domain, result-root scheme, keys, serving/retention and result-switch policy remain open. A longer-range certificate cannot be sliced into a shorter-range certificate.

Choose durability/batch boundaries that permit progress within Marshal's `max_pending_acks` window. If the App withholds every ACK until more Updates than that window can hold arrive, delivery waits forever. A signing range may be larger when valid durable application and ACK progress independently; this does not require per-block signing.

## Reuse certificate building blocks

| Existing mechanism | Reuse | App check still required |
|---|---|---|
| `p2p::utils::codec` typed wrappers | Encode/decode existing authenticated sender/receiver traffic | Bounded codec, full statement, original eligible signer identities |
| Crypto `Subject`, `Attestation`, `Scheme`, `Signers` | Domain/message definition, signing, signature verification and packaging | Exact input/base/runtime/result interpretation and distinct eligible `f+1` |
| Optional buffered broadcast | Share/cache an identified certificate or material object | Cache key identifies the object; different attestations cannot all overwrite one statement digest |
| Optional collector | Solicit request-bound peer responses | Its count is transport responses before app validation, not valid signer count |

Current source: [certificate APIs](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/cryptography/src/certificate.rs), [typed transport](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/p2p/src/utils/codec.rs), [collector response handling](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/collector/src/p2p/engine.rs#L190).

`Scheme::assemble` packages supplied attestations; it does not replace signature verification. Validate and deduplicate roster indices before constructing signer sets. Decode peer certificates with the selected epoch verifier's bounded `certificate_codec_config`, not its unbounded trusted-storage configuration. Keep a bounded execution-statement envelope because primitive attestation/certificate data does not supply our exact execution context. Scheme-specific proof-of-possession and original-signature provenance requirements still apply.

`N5f1::quorum(n)` computes `n-f`, or `4f+1` for `n=5f+1`; this is not the execution-result threshold. Multimmit also has distinct DA and nullification threshold sharings, not an existing `f+1` result-signing role. Select compatible certificate/key material and quorum handling, or use lower-level signature/bitmap primitives while enforcing `f+1` in app assembly and verification. A quorum adapter cannot lower an existing BLS sharing's polynomial threshold. No new native quorum or result-signing format is adopted. [Current fault model](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/utils/src/faults.rs), [native key roles](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/consensus/src/multimmit/scheme/bls12381_threshold/mod.rs#L3), [BLS threshold compatibility](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/cryptography/src/bls12381/certificate/threshold/mod.rs#L92).
