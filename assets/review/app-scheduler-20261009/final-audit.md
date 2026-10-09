# Final requirement audit

**Completed documentation review at 2026-10-09 09:57:55 UTC.** Work began at 06:57:26 UTC and passed the requested minimum end of 09:57:26 UTC. The [final snapshot](final-checkpoint.json) binds current reader/tooling hashes, validation and elapsed time.

## Requirement-by-requirement result

The root agent reread the three core pages in full, the pool contract, all four execution/backend pages, the PreCut baseline, architecture/interface map, body API guide, ordered-input contract, normal/canonical E2E flows, assembly/development sequence and verification cases. Independent reviewers freshly reread the App/backend requirements, current native callback/startup/delivery paths, all current reader entrances and diagram semantics. Recent simplifications were read back after application. Hash-bound evidence distinguishes earlier snapshots from current bytes.

| Requested outcome | Current design and evidence | Verdict |
|---|---|---|
| App-owned tx pool | `docs/baton/README.md` and `docs/tx/interfaces.md`: admission, selected/unselected retention, stable bounded selection and durable-outcome maintenance stay inside App. Propose constructs and stages the existing TransactionBlock. | Satisfied |
| App-owned Pre-cut and Baton schedulers | `docs/baton/direction.md`: two concrete implementations or a mode choice share execution/checkpoints/canonical writer. Pre-cut has no Baton instance or report traffic. Preserve started work and sort only eligible pending work. | Satisfied |
| Automaton verify → App and scheduler | `docs/baton/interfaces.md`: exact body/context validity and durable custody precede true; owner rechecks lifecycle/applied state/identity and admits usable metadata. Dispatch separately requires exact execution parent and resources. No speculative execution/root/report/direction wait. | Satisfied |
| Verify plus conditions identifies other-lane work | Core role table and body guide distinguish remote, local pre-sign and Engine-open recovery; producing/nonproducing validators and Observer; actual Protocol producer mapping, lifecycle and exact deduplication. This is not a one-to-one network receipt event. | Satisfied |
| Marshal report(Update) → App and scheduler | Synchronous retained full Update/Exact handoff; continuous native input; reuse, finish/repair or verified applicable import; writer recheck and durable state/output/applied-identity linkage; reconcile App state, schedule pool maintenance and ACK. Canonical-first input needs no earlier verify. | Satisfied |
| Explain ACK and execution timing | App ACK follows durable application. Matching speculative work need not run again; unfinished required work must be completed or validly imported. Native consensus has no direct ACK wait; bounded App delivery and its separately durable Marshal cursor remain distinct. | Satisfied |
| Remove unnecessary layers and reuse existing APIs | No required new public TxPool/Baton/Executor/Storage/BlockService/Orderer traits. Existing Automaton, Marshal mailbox/Relay/Reporter and runtime/crypto/P2P/QMDB remain. Native AppExecutor is explicitly local callback work, not a transaction runtime. | Satisfied |
| Explain actual assembly and recovery | Current source-linked log-multimmit sequence, existing node supervision, App custody processing during Engine::open, retained Update ingress during service startup, optional native Activity fanout and startup readiness/lifecycle are explicit. | Satisfied |
| Preserve research requirements while simplifying | Exact-parent work, frozen report context/window, completed bounded selection, entire-prefix 2f+1 support, nonempty sum-LCP fallback and empty-window base remain. Result f+1, signer independence, imported/direct provenance and state-sync authority remain. Full baseline questions map to 38 open cells; no default policy was invented. | Satisfied |
| Distinguish App-only work from full Baton native work | Local speculation can attach through existing callbacks. Canonical protected-prefix adoption requires authenticated native construction/validation, continuation and Marshal interpretation/recovery. App must not reorder finalized Updates. | Satisfied, implementation/proof work explicitly open |
| Consistent readable pages and diagrams | 32 reader pages, generated existing Rust API excerpts and 19 Mermaid/SVG/PNG diagrams are aligned. Local standalone reference links were reproduced as broken, fixed and retested. Current diagram hashes bind to actual pixel review. | Satisfied |
| Three-hour iterative subagent review | Three reviewers cover native behavior, simplification/App invariants and companion reader/visual alignment; repeated cross-reviews, substantive corrections and checkpoints are retained. The minimum interval has elapsed and the final snapshot verifies current files against the latest browser/source/visual evidence. | Satisfied |

## Validation evidence and limits

- `docs:check`: 32 pages, 253 local Markdown links, 19 rendered diagram source matches, 38 blank policy cells, no failures.
- `docs:build`: generated Rust export, 32 pages, 19 diagrams, three byte-exact source Markdown downloads. No external publication.
- Browser: 32 pages, 19 decoded images, 54 unique local article HTTP targets and 24 linked HTML fragment IDs, search and mobile menu, plus three actual source downloads matching original bytes; no failures. External websites and downloaded source files' transitive links are outside this check.
- Native binding: 121 pinned references across 59 local source files and seven declarations match the actual `6233438985d8249d2b2bc1204191d5d405652288` checkout. This is local exact-byte/line/signature evidence, not remote link availability, compilation or automatic semantic proof.
- Diagram review: all 19 current Mermaid/PNG byte hashes match the named actual image-inspection receipts. Latest desktop entry/mobile callback screenshots were directly viewed by root; other screenshot captures are not automatically claimed as pixel-reviewed.
- Four isolated builder cases pass: linked-only byte-preserving copies; existing navigation/external links; rejected outside-repository paths, escaping symlinks and directory attachments.
- `git diff --check` passes. Native source, original paper, archive and historical review records remain unchanged; current guidance and review evidence are local only.

This task designs and documents the App. It does not implement or execute the transaction VM, scheduler, native Baton extension, recovery protocol or benchmark. Future App acceptance cases remain explicitly **Not run**. Concrete comparator/resource/backend/wire/root/recovery choices remain open, as requested rather than hidden behind extra abstractions.

## Evidence entry points

- [Review timeline](README.md), [run record](run.json).
- [Reader acceptance](round26-user-requirements.md), [App design audit](round24-precompletion-app-design.md), [native boundary audit](round27-three-boundaries.md).
- [All baseline open questions](round22-open-policy-map.md), [adopted-policy preservation](round21-adopted-policy-preservation.md).
- [Preview link reproduction/fix](round28-preview-link-repair.md), [latest browser receipt](browser/verification.json), [builder cases](source-attachments-latest.json).
- [Native binding receipt](native-source-targets-latest.json), [current visual bindings](visual-receipt-bindings-latest.json).

The final independent counterexample searches are [native policy hooks](final-native-policy-challenge.md) and [four App event traces](final-app-event-challenge.md). The latest desktop entry/mobile callback captures are [byte-identical to the root-viewed images](latest-browser-pixel-bindings.json). [Evidence navigation](round29-evidence-navigation.md) records the older browser-link correction without inventing missing historical receipts.
