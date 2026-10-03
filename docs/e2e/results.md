# Executor result certification and queries

**ResultService establishes that eligible validators signed the same execution result.** It operates inside Executor, which exchanges signatures directly with peer Executors. A verified f+1 certificate establishes a certified result; local durability is a separate milestone.

## Result endpoint: direct execution and f+1 certification

Signing and collection are **internal Executor responsibilities** implemented through ResultService. The sequence shows direct signature exchange and collection between validator Executors. Certificates and change sets use the same execution-peer boundary without Baton relay. See [result certification interfaces](../execution/interfaces.md#result-certification-trait).

```mermaid
sequenceDiagram
    participant E as Validator Executor
    participant S as Internal ResultService
    participant P as Peer Validator Executor
    participant R as Certified result consumer
    E->>S: Completed direct execution with exact context
    S->>S: Verify own execution and irrevocable order / input-state chain
    S->>S: Persist own statement / signature obligation
    S-->>E: Own signed ExecutionStatement
    E-->>P: Execution signature
    P-->>E: Matching execution signatures or result certificate
    E->>S: Verify distinct epoch identities and exact statement match
    alt f+1 matching eligible signatures verified
        S-->>E: Verified result certificate
        Note over E: State-finalization endpoint verified, local durability is separate
        E-->>P: Result certificate, state material on peer request
        E-->>R: Result certificate + exact input identity
        R->>R: Verify certificate, irrevocable order and input-state chain
    else Insufficient signatures
        E->>E: Retain / reprovide signatures and continue local execution
    end
    Note over E,P: Direct Executor exchange, separate from Baton reports / directions
```

[Open full-size diagram](../assets/diagrams/diagram-11.svg)

Do not aggregate signatures merely because their state root values match. The statement must bind the same exact input range, canonical predecessor, runtime, and full result. An imported certificate or synced result cannot become the receiver's own direct-execution signature. Common signing boundary and wire schema remain undecided. Compare full statements bound to the same [root kind/version and operation/batch-boundary interpretation](../execution/qmdb.md#qmdb-state-and-reuse-boundaries).

Reuse Commonware cryptographic primitives for signing and signature verification. The common single-signature entry points are [`Signer::sign(namespace, msg)`](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/cryptography/src/lib.rs#L93) and [`Verifier::verify(namespace, msg, sig)`](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/cryptography/src/lib.rs#L130).

Executor's internal ResultService constructs ExecutionStatement, checks eligible epoch identities, and verifies that distinct identities signed the same full statement. Native [message signing](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/scheme/bls12381_threshold.rs#L1143) and [verification](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/consensus/src/multimmit/scheme/bls12381_threshold.rs#L1189) are examples of primitive calls. Scheme, keys, domain, codec, and aggregation remain undecided; the example BLS scheme is not adopted as the default.
