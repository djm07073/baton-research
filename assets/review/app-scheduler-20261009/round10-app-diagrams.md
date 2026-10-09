# Round 10 — App execution diagram semantics

Reviewed the current source and adjacent prose for diagrams 09, 11, 14, 17, 18 and 19. This is a documentation/source consistency review, not an execution, crash-recovery or protocol proof. No runtime tests or benchmarks were run.

## Confirmed corrections

Two diagram 09 wording problems were sent to the root and have been corrected in both `docs/e2e/canonical.md:79-83` and `docs/assets/diagrams/diagram-09.mmd:20-24`:

1. The old failure note, “No ACK or successful apply,” excluded the real case where apply succeeds but a later durability operation fails. It now says “No ACK or durable completion, stop using failed storage and recover.” This agrees with `docs/execution/qmdb.md:125-129`: readable/applied state is not observed durable completion, failure is not proof of zero disk writes, and restart must choose a coherent App checkpoint.
2. Reclamation previously required only the absence of live references or serving obligations. The new condition, “Retention and reference obligations permit reclamation,” also covers recovery, sync and durable-history retention. Logical pruning alone never authorizes physical deletion (`docs/execution/qmdb.md:109`).

Alignment independently corrected diagram 14's pool-maintenance step to “Advance canonical base and schedule pool maintenance” (`docs/e2e/state-sync.md:33`, diagram source line 24). ACK therefore does not wait for a pool cleanup round trip. This matches the existing internal contract at `docs/execution/interfaces.md:55` and the independent durable-outcome/ACK arrows in diagram 19.

No additional execution/baseline edit was justified by this pass.

## Scenario checks

| Diagram and adjacent text | Trace checked | Result |
|---|---|---|
| 09; `e2e/canonical.md:57-89` | Speculation produces effects on exact completed parent; canonical input selects/reconciles them; selected commitment and one writer precede durability; owner promotes the path afterward | Pass. Root preparation is not equated with transaction execution or durable apply. The corrected failure branch leaves ACK unavailable even if an earlier mutation already succeeded. |
| 09; `execution/qmdb.md:109-129` | ABD becomes canonical while C is retired, but a worker/query/recovery/material-serving obligation still uses its material | Pass after retention wording correction. Logical pruning can happen first; physical reclamation remains conditional. No early-free dependency was added to ACK. |
| 11; `e2e/results.md:15-40`, `execution/interfaces.md:63-73` | Local direct execution and selected result commitment finish while fewer than f+1 matching signatures exist | Pass. More certification work remains, but there is no arrow blocking direct durable application or ACK. Diagram explicitly separates result certification and local durable application. Signing-range choices must independently permit ACK progress. |
| 11; same text | Two roots match but the range/base/runtime differs, or a result was imported | Pass. Full-subject verification precedes counting signers; imported results do not create own direct-execution provenance. Material retention is explicit before sending a statement. |
| 14; `e2e/state-sync.md:15-50` | A certificate is valid but material is missing/invalid or its predecessor is unresolved | Pass. Continue valid local work; the certificate alone does not trigger canonical mutation or cancel useful execution. Verified applicability precedes fencing and the shared writer. |
| 14; same text | Verified import becomes durable with pending matching Updates and asynchronous pool cleanup | Pass with alignment's maintenance-label correction. Preserve imported provenance, update local canonical ownership, schedule maintenance, and ACK only retained tokens covered by the exact durable prefix. It never fabricates tokens or waits for cleanup completion. |
| 17; `execution/qmdb.md:3-83` | App keeps a rootless AB prefix and later prepares a selected commitment | Pass. Retained effects/overlay is explicitly optional App work. The concrete branch-access section explains existing sealed-parent forks and replay/materialization at a valid anchor; the diagram does not invent an unsealed-parent QMDB fork. |
| 17; `execution/qmdb.md:44-55,113-129` | `apply` succeeds; `finalize` begins; covering barrier or App output linkage is incomplete | Pass. The flow's durable node depends on the App writer/linkage and covering QMDB durability. Adjacent API table requires `Barrier::durable() == true` plus App linkage before ACK; a writer-to-durable-node arrow is not an alternate bypass of that requirement. |
| 18; `execution/qmdb.md:85-109,123` | Reuse AB for ABD; attempt to reuse A-after-S0 as A-after-X; only ABC sealed material exists when AB is confirmed | Pass. The picture is an execution-prefix tree, not a guarantee that every pictured node is already a sealed QMDB batch. Same block on a different prefix differs. The text requires valid actual ancestry and exact-prefix material; it rejects hiding C after applying ABC. |
| 19; `baselines/precut.md:3-52,54-112` | Verify finishes valid custody before speculative execution; canonical Update arrives without earlier speculative admission | Pass. Candidate intake and exact-parent scheduling are separate, and canonical index/block reaches execution directly. The page covers local/recovery verify and Observer's missing live validation planes. No Baton instance or result-approval hop appears. |
| 19; same text | Durable execution produces pool outcomes and ACK while peer certification is incomplete | Pass. Durability feeds pool maintenance and Marshal separately; there is no pool-to-ACK or certificate-to-ACK dependency. Peer result/import capability remains shared with Baton, including imported provenance rules. |

## Existing mechanisms versus design status

`docs/README.md:36-38` labels the transaction App and modified Baton integration as proposed work connected to inspected native code. `docs/execution/README.md:67` and `docs/baselines/precut.md:5,126-134` repeat the missing implementation/runtime verification status. Existing callbacks, native Activity, Marshal Update and QMDB handles are distinguished from App-internal execution and scheduling responsibilities. Diagram 17's text explicitly says its App subgraph is not a required actor graph (`execution/qmdb.md:38`); none of these diagrams requires an extra public trait/service.

## Visual evidence and final render handoff

Actually viewed PNGs 09, 11, 14, 17, 18 and 19 during this round. The first 09/14 images showed the old wording that motivated/overlapped the corrections above. Root subsequently rendered and copied the corrected 09/14 assets; alignment owns their final visual readback together with 04/05. Those production images are no longer considered stale. The final sources were independently read back here; final 09/14 pixel validation is attributed to alignment, not claimed by this review.

PNG 11, 17, 18 and 19 had legible labels and intact arrowheads at actual rendered size. Diagram 17's Update ends at the execution node, diagram 18 separates A-after-X clearly, and diagram 19's shortened PreCut title is legible. No clipping or routing problem changed the reviewed meaning. Cosmetic rewrites were avoided.

Final source SHA-256 prefixes observed after root's render notification:

| Diagram | `.mmd` | `.png` |
|---|---|---|
| 09 | `99e1fb9e2251097d` | `f6f685ccfb62bccd` |
| 11 | `95097fdb320bbca5` | `04769dca2c40f512` |
| 14 | `0c68a0d001b0da32` | `79581a02671e9a1f` |
| 17 | `9ac290c7ec5ea996` | `a87b01a7e02e28eb` |
| 18 | `15954e740735be9f` | `f047081e01f263cf` |
| 19 | `4654f571dc2fc99f` | `37b5d94d671656e0` |

The hashes identify reviewed source/current production files; a hash does not itself prove rendered semantics or runtime behavior.
