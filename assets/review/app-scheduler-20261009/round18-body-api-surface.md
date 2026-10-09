# Round 18: concrete body and public API surface

Native source `6233438985d8249d2b2bc1204191d5d405652288`, 2026-10-09. Checked the Rust reference, body guide and App callback pseudocode against exported source. Existing API excerpts and helper names are valid. No native edits or runtime tests; the only reader change makes the concrete codec implementation requirements explicit in consensus/block-body.md.

## What App actually implements

- `multimmit::types::Body<H>` is `Codec + Digestible<Digest = H::Digest>` and has a blanket implementation (`types/block.rs:265–267`). Do not manually introduce another body or block marker. `Digestible` requires `Clone + Sized + Send + Sync + 'static` (`cryptography/src/lib.rs:233`). The digest must correctly commit to the chosen canonical body representation; the marker does not check application transaction signatures, static policy or VM validity.
- Concretely, existing `Write`, `Read` and `EncodeSize` implementations supply `Encode`, `Decode` and `Codec` through blankets. `FixedSize` can supply `EncodeSize` for a genuinely fixed-size type (`codec/src/codec.rs:89,113,197,305,341–349`). `Read::Cfg` requires `Clone + Send + Sync + 'static`; its decoder receives `commonware_codec::Buf`. The public `Config::body_codec_config: B::Cfg` supplies that application's decoding bounds (`marshal/config.rs:339–371`). Native protocol `CodecConfig` is a separate field and does not replace body bounds.
- `Debug`, `PartialEq` and `Eq` on the body are only needed for the corresponding optional `TransactionBlock` formatting/comparison implementations (`types/block.rs:341–370`). They are not base `Body`, Marshal or shared consensus `Block` requirements. The example derives them for convenience, not as another application contract.
- `TransactionBlock<H,B>` already implements `Codec`, `Digestible`, shared `Block`, `Heightable` and `Epochable` (`types/block.rs:373–457`). App supplies body behavior plus the existing `Automaton` and typed `Reporter` handles; it does not need to implement a generic replacement `Block`/`Executor` trait.

## Exact construction and identity

| Existing operation | Source and meaning |
|---|---|
| `TransactionBlock::<H,B>::from_context(context, body)` | `types/block.rs:284`: infallible, accepts `Into<Arc<B>>`, computes the body digest and constructs its contextual header. |
| `TransactionBlock::<H,B>::new(header, body)` | `types/block.rs:296`: returns `Result<Self, types::Error>`, compares `header.body_digest()` with `body.digest()`, rejects mismatch with `Commitment`. It does not authenticate a producer signature or validate VM semantics. |
| Decoding a complete block | `types/block.rs:389–400`: `Read::Cfg = B::Cfg`; decodes header and body and invokes `new`. Full `Decode` also rejects trailing bytes (`codec/src/codec.rs:318–341`). |
| `context.header(body_digest)` | `types/block.rs:70`: reconstructs the exact expected header. Context's fields are private; `chain()`/`parent()` are inherent methods, while `epoch()`/`height()` use the shared `Epochable`/`Heightable` traits. |
| `header.block_ref::<H>()` | `types/block.rs:186`: hashes the entire header using the configured hasher, then returns producer chain, height and that header digest. A digest type alone does not identify the hasher. |
| `block.reference()` / `block.digest()` | `types/block.rs:325,425`: both use header identity; `reference()` includes chain and height. Neither is the body digest returned by Automaton. |
| `BlockRef::new(chain, height, digest)` | `types/primitives.rs:227–284`: public, infallible value constructor with public getters. Its digest must be the header digest. Epoch is bound by that digest, not an independent BlockRef field. |

Core pseudocode's `expected_header.block_ref() using App's configured hasher` is explicitly pseudocode and has the correct meaning; real Rust spells the generic hasher as above. There is no nonexistent helper to replace. The seven Rust API blocks already state that surrounding generic bounds/imports are omitted and they are not standalone compilation targets.

## Public lookup and custody contracts

The public `marshal::Mailbox<H,V,B>` requires `H: Hasher`, `V: Variant`, `B: Body<H>` (`marshal/mailbox.rs:247–261`). Clones share the actor handles, subscription bound and staged cache. All block methods below take `&self` and return an async result:

| Method | Actual input and output |
|---|---|
| `stage_block` | `impl Into<Arc<TransactionBlock<H,B>>>` → `Result<Custody, marshal::Error>` (`mailbox.rs:337`) |
| `put_block` | same input → `Result<(), marshal::Error>`; stage followed by custody wait (`mailbox.rs:354`) |
| `get_block` | `BlockRef<H::Digest>` → `Result<Option<Arc<TransactionBlock<H,B>>>, marshal::Error>` (`mailbox.rs:396`) |
| `fetch_block` | same reference → `Result<Arc<TransactionBlock<H,B>>, marshal::Error>` (`mailbox.rs:409`) |
| `subscribe_block` | same reference → `Result<Arc<TransactionBlock<H,B>>, marshal::Error>` (`mailbox.rs:431`) |

`Custody = Completion<marshal::Error>` (`marshal/types.rs:318`); `wait(self).await` consumes the token and yields `Result<(), Error>` (`actors/util/completion.rs:24–27`). It is not a block-returning future or a cloneable ACK. An unresolved sender closure maps to the configured error. Already accepted work survives dropping its receipt. Current prose distinguishes staged acceptance, buffered get/fetch availability and completed durable custody correctly; the round16 explicit-fetch/put fallback remains necessary for the stronger App progress design.

## Accessibility and configuration

`multimmit::types` is public; `types/mod.rs:56,63` reexports the block and primitive types, including Context, Body, TransactionBlockHeader, TransactionBlock and BlockRef. `multimmit::marshal` publicly reexports Mailbox, Completion, Custody, Config, Service, ServiceHandle and `open` (`marshal/mod.rs:81–95`). Its internal service module is not the external call path. Marshal is exposed on native targets, not wasm32.

Public `marshal::open` accepts the configured body codec and `buffered::Mailbox<P, TransactionBlock<H,B>>`, with `H: Hasher<Digest = B::Digest>`, `B: Codec + Digestible` and the stated `B::Cfg` bounds (`marshal/service/mod.rs:96–108`). The stronger Sync bound already comes from `Read::Cfg`. `with_max_block_bytes` sizes bounds for the complete encoded producer block, including its header, not just raw transaction bytes (`marshal/config.rs:381–394`). Current integration refers to the concrete example assembly rather than inventing an uncallable convenience constructor.

Resolution: added one paragraph to consensus/block-body.md describing concrete codec traits, digest bounds, body decoder configuration and the wrapper's existing Block implementation. Root was advised that the Rust overview can link this paragraph without expanding its already accurate excerpts. No extra public trait, service or API is required for these operations.
