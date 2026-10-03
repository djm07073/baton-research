# Proposed small addition: existing body page only

Place after the current body Digestible/callback explanation; retain existing headings and tables. No new body trait, actor or chosen format is proposed.

**Implement the body's existing codec and digest interfaces directly.** Native Multimmit requires Automaton/Relay commitments; it does not require a Simplex Block or Application body type. Existing native Header construction, codec and digest/block_ref APIs already supply producer-header identity.

| Body need | Existing Commonware interface |
|---|---|
| Selected field/transaction encoding | Write + EncodeSize; Encode is supplied automatically |
| Bounded parsing and complete-frame check | Read::read_cfg; Decode/Codec are supplied automatically |
| Ordered transactions / retained bytes | Vec<T> uses (RangeCfg<usize>, T::Cfg); Bytes uses RangeCfg<usize> |
| Stable body commitment | Digestible plus the selected existing Hasher; recompute/check untrusted content |

Buffered broadcast and Archive accept the body's read configuration; the resolver's unit outer wire config does not require a unit body decoder. Count, inner transaction bounds and complete encoded bytes are separate constraints. Share the stable body through existing Arc/Bytes handles, and keep cached bytes/digest coherent with the committed representation. A body commitment is separate from the native header hash and its parent header reference; preserve the authenticated header/body join and required durable parent custody already specified below. Body format, hash/domain, limits and encoding remain open.

Suggested source anchors: native codec.rs#L202 / #L305; types/vec.rs#L65; broadcast/buffered/engine.rs#L111; multimmit/types/block.rs#L175; multimmit/engine.rs#L602. Actual Tempo/Alto formats remain examples, not adopted schemas.
