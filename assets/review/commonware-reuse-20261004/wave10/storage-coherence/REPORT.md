# Executor / Storage documentation coherence

Reviewer `/root/reuse_storage_types_v3`. Documentation/contract-source audit against canonical baseline `01cf73b41dedd81614237977e4edf150c7d19a81`; no native build, test, benchmark, protocol implementation, dependency change or canonical edit by this agent. **Detailed contracts and diagram ownership are coherent. Three introductory sentences needed clarification; root has adopted those clarifications.**

## Findings and smallest correction

| Location at baseline | Reader ambiguity | Final adopted wording |
|---|---|---|
| `docs/overview/architecture.md` lead | Executor “turns agreed inputs into durable state” hides the Storage boundary already explicit below | Executor computes transaction changes; Storage prepares roots and durably applies canonical state |
| `docs/e2e/normal.md` lead | Executor “applies the result” can imply it owns physical database mutation | Executor computes changes; Storage applies and persists them; BlockService uses existing body primitives |
| `docs/e2e/canonical.md` lead | “It acknowledges delivery” can grammatically refer to preceding Storage | Executor acknowledges only after Storage makes state, outputs, cursor and provenance recoverably durable |

These are role clarifications of existing adopted requirements, not new API or ownership choices. Root made the edits; this agent independently verified final file hashes and exact diffs. No additional vocabulary/page/trait/method/framework is needed.

## Consistency checked across existing pages

- **Executor** resolves execution parents, computes/reuses completed transaction effects, selects/logically promotes/prunes exact paths, retains worker authority, signs directly executed prepared results, verifies/collects full eligible f+1 subjects, orchestrates normal-path peer sync, and sends delivery ACK/outcomes. Direction planning remains Baton::plan.
- **Storage** supplies authorized concrete branch access; turns selected completed effects into material and root; checks compatible base/ancestry and canonical writer access; applies/flushes canonical QMDB state; connects outputs/cursor/provenance recovery; serves retained state/material and controls physical reclamation. This is a thin application boundary, not compulsory actor or another database algorithm.
- ExecutionResult remains completed **unsealed effects/batches and outputs**, not mandatory root after every attempt. PreparedResult is a retained sealed/material handle for selected signing/application; direct-result signing still requires irrevocable exact order/base/runtime and own direct evidence. Speculative finished work, prepared roots, certification and durable application remain distinct.
- Public/proposed Rust contracts are labeled as design boundaries. Associated types do not automatically connect modules, choose codecs/schema/roots, establish a single writer, or implement sync. Storage::read is not a pending-parent/historical snapshot shortcut. Executor receives actual internal batch/read handles through the Storage attachment; no extra public storage-view trait or glue Application/full actor is required.
- Existing QMDB reuse is correctly scoped: applied-base drafts and sealed-parent forks, concrete keyed methods, one-shot unsealed/staged drafts, per-DB selected merkleize and sealed batch ownership. Rootless branching remains conditional retained exact-effect replay/materialization or a compatible overlay/access integration, rather than an asserted public unsealed-parent fork. No generic custom tree/storage engine becomes mandatory. Own prior pinned storage reviews remain the API evidence; this coherence pass introduces **no new upstream API claim** or source inventory.
- The direct path asks Storage to prepare/apply; the import path requires verified full certificate and applicable exact-base/target/output material before fencing/stopping unfinished computation. Both share canonical writer/access/durability/recovery contracts. No Baton relay, direction ACK, result collection before cut, second writer, imported-own-signature, automatic multi-store atomicity or per-attempt Merkle policy appears.
- Canonical/QMDB diagrams put selected root creation, finalize/flush, metadata linkage and physical GC in Storage. Executor's logical promotion and delivery ACK follow durable CommitResult. Result diagram places preparation before own direct signing; state-sync diagram separates certificate verification, Storage applicability, safe switching and durable import. Recovery reconstructs Storage bases and Executor paths before exact idempotent redelivery.

The short generic-adapter language is consistent with the detailed concrete recipe; no wholesale rewrite or signature change is warranted. Five traits remain TxPool, Orderer, Baton, Executor, Storage. Schema/root/sealing/pruning/runtime/switch choices remain open. Bank semantics and protocol validation remain outside this pass.

## Bound document and diagram evidence

`baseline-document-receipt.json` binds **19 reviewed Markdown pages plus generated Rust export** by SHA-256 to baseline01cf73b. All **18 existing .mmd diagram sources** match embedded canonical Mermaid text; baseline .mmd/.svg bytes are recorded and remain unchanged. `svg-role-label-receipt.json` checks ownership labels in eight relevant rendered SVG source files (01,02,08,09,10,11,14,17); this is label/source inspection, **not rendered visual QA**. No diagram regeneration is needed for lead-only edits.

Final adopted pages:

- `docs/e2e/normal.md`: `da22c9d489975d03e96ca58ac9ede56c97e1391041182d7f8f67c4cfc2bf4e8c`
- `docs/e2e/canonical.md`: `fc5ca24ed8010cd3aa9f873ead571a85da423b39132e53de3f827fb738f351e0`
- `docs/overview/architecture.md`: `e21a290167bcf338ed6649fe444f7c84e9a450c0c9a1c68795739677a309531a`

`final-prose-diffs.json` shows only the three introductory prose lines changed. All other reviewed-page hashes, Rust declarations/export and diagram bytes are unchanged. No new API claim means no new raw upstream source receipt is required for these editorial changes; existing source-pinned QMDB/state-sync/retention reviews and current adopted ownership remain the grounds.

**Verdict:** adopt the three small lead clarifications. Remaining detailed interface/storage/sync/diagram prose needs no ownership change from this audit. This is documentation coherence, not compiled actual-library assembly or integration proof.
