# Proposed reader delta (not a canonical edit)

## execution/interfaces: result exchange

Executor can receive result signatures and certificates through `p2p::utils::codec::wrap`, which turns the existing raw Sender/Receiver pair into a typed sender/receiver. Reuse the existing Executor owner for validation and collection. Transport peer identity is separate from the original eligible epoch signer; accepted sends and collector response counts are not f+1 verified signatures.

| Existing component | Connection | Limit |
|---|---|---|
| Typed P2P wrapper | Incoming full statements/signatures/certificates → Executor collect/verify | Selected bounded codec and full application verification remain required |
| Buffered broadcast mailbox | Share/cache an identified artifact; get/subscribe by known digest | One object per digest; distinct signer responses cannot all use only their shared statement digest as the artifact key |
| Conditional collector | Request-bound solicitation via Handler/Monitor and two raw channel pairs | Requested transport peers counted before application validation; explicit cancel; no resolver retry loop |

The buffered cache is transient. It is not an unsolicited result stream, durable certificate store or signer accumulator. Keep exact full execution subject and original signer collection inside Executor. Existing generic certificate and f+1 application checks remain as already specified.

## execution/state-sync: material transport

For compatible QMDB operation proofs, reuse `glue::stateful::db::p2p::Actor` and its cloneable Source mailbox directly. It already owns generic resolver serving/retries; no extra fetch actor is needed. Storage supplies a compatible shared DB, and Executor authorizes the certificate-bound target. The upstream operation Request contains numeric size/start/count, not the trusted root or execution statement, so concurrent sessions must retain compatible authenticated history and verify the chosen target separately. Output/certificate bundles need their own application binding to the same target.

`attach_database` enqueues a serving DB replacement; its returned ready Future does not confirm processing, retention, durable apply or writer handoff. Local Source proof feedback ends at the proof check; it must not wait for f+1 collection or canonical apply. Keep direct execution running until certificate and applicable material verification succeeds. Existing canonical writer fencing and direct/imported recovery provenance remain required.

## Scope preserved

These are conditional existing-handle recipes. They select no codec, signing scheme, archive/schema, service topology, quota, retry/switch policy or new public trait, and establish no native protocol/custody proof.
