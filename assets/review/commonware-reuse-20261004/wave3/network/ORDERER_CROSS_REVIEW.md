# Independent Orderer review of network/body findings

Review date: 2026-10-04. Reviewed REPORT.md source hash `c0686d641f3bb0682b3fd79f685df776bd89c89bd263796d2b20b998e6dbc0b7`. Recomputed Git blob SHA-1 and SHA-256 for all 50 verified source receipts; all match both manifest and their respective immutable Git tree. No protocol compilation, implementation, canonical edit, dependency change or publication occurred. Only this cross-review file was written.

## Verdict

**Pass.** N1 and N2 are source-grounded small documentation corrections. Oracle/Provider, transport recipients, cache residency and native signer eligibility are correctly kept separate. Optional codec wrappers are real public APIs, with the reported loss/blocking/lifetime limits. No extra transport engine, mandatory actor or adopted policy value is justified.

## N1: native example register arity

Independently verified the complete resolution path:

- `examples/log-multimmit/src/main.rs` constructs `discovery::Network::new` and calls four three-argument `network.register(..., quota, 256)` methods at L366–369.
- The same pin's discovery/mod.rs L255 reexports its local `network::Network`; that concrete type has `register(&mut self, Channel, Quota)` at network.rs L169. No alternative overloaded inherent register signature exists in that file.
- Example Cargo uses `commonware-p2p.workspace=true`; root Cargo L133 maps it to local path `p2p`, despite the workspace package's 2026.7.0 version spelling. This is not the 2026.9.0 release type being substituted into an older example.
- `start(self)` consumes the registered network; add channels before start. Start binds each sender before spawning actors; prebinding sends may be accepted and dropped.

Safe correction: “Use the selected native pin's `network.register(channel, quota)` and register all planes before start. The pinned log-multimmit example remains a wiring reference; its three-argument calls are stale relative to this same pin's primitive signature.” Do not claim a recorded compiler failure, repair the external checkout, choose `256`, or change the source pin.

## N2: exact payload/envelope size

The response formula is correct **for the pinned generic resolver**, independently read from resolver wire.rs L16/109 and codec bytes.rs L23:

- Broadcast payload: encoded Body itself.
- Fetch request: 8-byte u64 + 1-byte tag + encoded Key.
- Fetch response: 8-byte u64 + 1-byte tag + Bytes length prefix + body bytes.
- Fetch error: 8-byte u64 + 1-byte tag.

Bytes' prefix follows the existing usize codec; it is variable length and not an assumed constant 4/8-byte prefix. Network channels pass `cfg.max_message_size` as the application payload bound; discovery adds transport/channel/encryption framing internally. The native channel's UnlimitedSender asserts encoded payload length, so oversized local resolver output can panic if submitted, rather than become a Consumer Invalid outcome. Use checked budget arithmetic and public encoded-size operations; private resolver wire types are not new public construction APIs.

Safe correction: require the **entire allowed resolver response** and request key envelope to fit the network application maximum, as well as the raw body. No numeric limit, fragmentation, compression or outbound size-wrapper choice is adopted. Consumer still needs its bounded application decode/context/digest checks. The transport byte bound does not establish transaction count, nested allocations or validation-work limits.

Alto's configured maximum includes its block data prefix/base allowance; Tempo's outgoing `SizeLimited` is crate-private adapter code. Both are accurate assembly references, not evidence of a public universal size-limiter primitive.

## Oracle, Provider and recipients

The 50-file report receipts did not include tracker/ingress.rs, so I additionally fetched that one immutable native file directly **in memory**, without writing another snapshot. Its calculated Git blob `8098e41cdce94291ffc302bb56be1014c8f05b05` matches native-tree.json. [`Oracle<C>`](https://github.com/commonwarexyz/monorepo/blob/534af0ede48affd35b2111522527547b4cc9bf72/p2p/src/authenticated/discovery/actors/tracker/ingress.rs#L270) is Clone and implements existing Provider (L305), Manager (L327), Blocker (L338). Thus cloning the oracle is a concrete supported reuse choice when its tracked peer sets express the desired serving policy, not an inferred adapter.

- Provider returns tracked sets. `latest.primary` is not the connected-peer snapshot or a cryptographic consensus committee proof.
- Native rate-limited `Recipients::All` expands its connected-peer subscription snapshot, subject to local quota. It does not mean all current signing validators received a message or satisfy a custody quorum.
- Buffer stores references only for latest primary peers, but resolves existing waiters before cache eligibility. It sends after attempted local insertion even if insertion is ineligible. `broadcast_shared` Feedback reports mailbox admission; downstream attempted recipients are ignored by buffer and not returned as a publication completion.
- Generic resolver chooses outbound peers from latest primary; inbound requests can be served for connected nonprimary peers. Required old-epoch serving material therefore needs deliberate coverage, without redefining native committee authority.
- Transport relay identity need not equal producer authorship. Validate the original header/body subject and signer role separately. Tempo's BLS/Ed25519 concepts are source context, not an adopted Baton key mapping.

Safe correction: add a compact wiring table naming Network → registered Sender/Receiver → buffer or generic resolver, with cloned oracle Provider/Blocker only under the stated peer-set condition. Label membership/recipient/key binding policies as still open. Root can optionally add tracker/ingress.rs to the source receipts for the oracle claim; the public signature has already been independently checked here.

## Optional codec wrappers

`utils::codec::wrap(config,pool,sender,receiver)` and WrappedSender/Receiver are public typed helpers. These produce typed send/receive interfaces, not raw Sender/Receiver implementations automatically suitable to pass ahead of body engines. The engines already wrap their channels internally.

WrappedBackgroundReceiver supplies bounded strategy-parallel decode, a bounded lossy output mailbox, automatic peer blocking on Codec errors and a Handle whose drop aborts its task. It returns a typed BackgroundReceiver; no raw Receiver implementation was found for that receiver. It is conditional reuse for application tx/report/result paths needing that behavior. Pure stale context/local storage errors should remain application verdicts rather than be encoded as hostile decode failures.

Safe correction: mention the existing wrappers in the network reuse table without requiring another module or inserting them before buffer/resolver. Preserve no-wait cut, native authority, Executor/Storage ownership and all open policy cells.

## Publication disposition

The prior published revision remains unchanged by this review. Root can apply the four proposed small edits after the normal source/comment/interface consistency review. These findings validate APIs and documentation wording, not a compiled Baton integration or completed dense-delivery proof.
