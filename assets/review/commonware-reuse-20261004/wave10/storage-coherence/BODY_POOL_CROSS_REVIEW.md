# Independent body / pool / introductory coherence review

Reviewer `/root/reuse_storage_types_v3`; documentation/source-only. **Scoped source fit: pass.** No canonical edits, implementation, tests, builds, dependency changes or policy selection.

Bound final report SHA-256:

- `pool-coherence/REPORT.md`: `337849808bdb3f305ef423a4c4e52a159bb6c4c55989b17d4c585d3155aab028`
- `body-coherence/REPORT.md`: `9106d87b81e5af78b8b792ef13e72c8d198db7a83a48bcf8ba25c0177caf4c53`
- `intro-coherence/REPORT.md`: `51da6051bdaa62de48b70c8c414d7952b60f9e96528a87c9ececc33018c5037f`

## Fresh decisive checks

`body-pool-cross-review/` records **13 independently fetched primary files** in four freshly fetched complete nontruncated Git trees, every raw Git blob matched. Native534af, explicit released476, Nunchieea35c and Tempo61c979 remain separate source/dependency identities. This is a narrow recheck of the actual proposed no-API prose deltas and key body boundaries, not fresh verification of every historic pool/chain citation.

- Nunchi public MempoolHandle::pending(limit) uses a mailbox oneshot snapshot; private pool selection clones gap-free eligible nonce candidates. Public finalized uses try_send with no processed reply; its private owner's finalize updates nonces/status/height then runs TTL even for an empty digest list. Its pool module is private; exported handle is the connection seam. This independently establishes that the paragraph after Reth in tx/interfaces belongs specifically to Nunchi source adaptation. Replacing its vague antecedent explicitly names that conditional candidate without choosing it or adding a second lifecycle owner. Fresh actor.rs L177–218, pool.rs L160–283, lib.rs private/export boundary checked.
- Body send recipe is real existing composition: release standard Relay forwards/proposes retained full blocks to Marshal; core dispatch buffer.send invokes the standard variant's buffered Mailbox broadcast_shared. Tempo constructs buffered Engine with its mailbox and starts it in the retained service task group. Existing prose does not rebrand this Simplex Marshal as unchanged native Multimmit. Fresh release relay.rs L21, core/actor.rs L649, variant.rs L115, Tempo consensus/engine.rs L207/L526 checked.
- Native receive recipe uses public buffered subscribe/get with Arc messages. Its insertion notifies waiters before cache eligibility; receiving a message therefore does not prove residency/durable custody. Generic resolver delivers responses to its Consumer, not automatic buffer insertion. Fresh buffered ingress/engine and resolver response delivery support current qualified receive prose.
- Native Marshal explicitly documents Simplex-only limitation. Inline's Automaton uses Simplex Context; specialized resolver Receiver has pub(crate) recv/try_recv. Existing public buffer/generic-resolver/archive callbacks remain reusable without adding a generic body service. Those source boundaries do not demand a new framework or ACK/readiness quorum.
- Intro-coherence report agrees with current proposed Rust contracts and the independently reviewed three owner fixes: Executor computes transaction effects/logical paths/certification/sync, Storage selected roots/canonical apply/durability/physical retention, Executor delivery ACK after complete receipt. It adds no upstream capability or URL.

The pool report's Reth/Constantinople comparisons remain unchanged from previously pinned audits; this narrow pass does not claim fresh compile or all-source revalidation of those unrelated APIs. Their cited boundary wording is consistent with current conditional backend choices and the one changed Nunchi antecedent.

## Adoption verdict

Adopt only the three introductory ownership clarifications and the Nunchi antecedent. Body no-delta verdict is supported: current interfaces/diagrams already reuse actual Commonware primitives with native/body/custody integration explicit. No public body trait, another pool/dispatcher, custom generic storage/tree/simulator, selected backend/policy/limits, quorum, per-attempt root or new native cut/ACK barrier is established. All transaction/body/execution/native custody/adoption/recovery implementation obligations remain open. This review is source/documentation fit, not a compiled assembly, rendered diagram proof or executed E2E result.
