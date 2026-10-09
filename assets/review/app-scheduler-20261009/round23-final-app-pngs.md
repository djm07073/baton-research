# Round 23: final App diagram PNG readback

Directly opened and visually inspected the current on-disk PNGs for diagrams **08, 09, 17, 18 and 19** with `view_image`. This is an actual raster readback, not only Mermaid/source or manifest validation. Compared each with its current `.mmd`, embedded Mermaid block and adjacent prose. Diagram 01 belongs to root's separate inspection; no other PNG is covered by this receipt.

All five pass this review. No source, image or render-manifest change was made, and no rerender is requested. The checks establish presentation/semantic consistency of these design diagrams, not runnable App behavior, native proof or storage crash-test results.

## Visual and semantic findings

| Diagram / actual PNG size | Visual inspection | Meaning checked against current page |
|---|---|---|
| 08 / 1115×1885 | All participants, nested alternatives, labels and bottom ACK-independence note are visible. Inner exact-applied branch fits its frame. No clipped/overlapping text or ambiguous arrow endpoint | `docs/e2e/canonical.md:3–57`: unresolved order holds delivery; Update/Exact is retained before synchronous Feedback; expected index/block/predecessor is checked; exact durable replay avoids a second apply; new input uses exact work/import/repair and fencing; durable state/output/applied identity/provenance precede ACK; pool maintenance is scheduled, not awaited as another approval; Marshal cursor persistence is separate. Native consensus never waits for application ACK |
| 09 / 711×1657 | Long vertical sequence remains legible. Root-deferral note, success/failure alternative and conditional-retention box are fully inside the canvas, without text collision | `docs/e2e/canonical.md:59–91`: exact completed execution parent precedes dispatch; completed effects are distinct from selected root preparation; one authorized writer applies; logical promotion occurs on durable success; physical reclaim is conditional on references/retention; failed storage has no successful ACK/durable completion and requires recovery. Adjacent paragraph explicitly makes workers/storage internal App responsibilities and disclaims automatic cross-store atomicity |
| 17 / 1200×1036 | Application title, scheduler, optional effects path, writer, DB boxes and durable record all fit. Some edges cross in the right half, but labels have clear backgrounds, endpoints remain traceable and no text is clipped or obscured | `docs/execution/qmdb.md:3–11,38–57,65–83,113–135`: Marshal ordered input reaches the execution tree; PreCut/Baton only selects work; effects may be retained without roots; existing unmerkleized/sealed batches feed the same canonical writer; current API order is apply then finalize; covering durability joins the App's durable applied record before the ACK edge. The application subgraph is not a mandatory actor graph or extra public Storage/Executor layer |
| 18 / 934×280 | Compact branch tree is clear; all six non-root nodes and both AB descendants are separated, with arrows entering the intended boxes | `docs/execution/qmdb.md:85–109`: AB is the common execution prefix for C/D; A after X is a different execution identity from A after S0. The figure does not claim either branch is canonically adopted or that roots are optional at every fork; adjacent prose supplies exact context, actual ancestry and retention conditions |
| 19 / 1599×908 | The shortened PreCut title is visible above the callback box and is not crossed through its text. All boxes/labels fit. Bottom routes converge on Marshal and some lines cross, but stage/fetch, ordered Update and post-durability ACK labels and arrowheads remain distinguishable | `docs/baselines/precut.md:3–5,33–52,81–112`: independent PreCut App has pool/callback/scheduler/shared execution/storage, with no Baton report/direction instance or policy service. Native Activity goes directly to existing Marshal; eligible custody drives pending-only speculation separately from exact canonical input; both feed shared execution. Durable outcomes feed pool maintenance, ACK goes to Marshal after durable apply, and execution certificates/material use peer App traffic without a scheduler approval hop |

Diagram 08 condenses cursor advancement/sync into one displayed Marshal step; the page's line 55 explicitly says contiguous ACKs free window capacity before separate cursor I/O. Diagram 17 is a responsibility/dataflow graph, so the writer-to-durable-record edge is not an alternate durability bypass: the covering-DB-durability edge and lines 51/55/119–129 supply that prerequisite. Neither diagram introduces a peer `f+1` wait before valid direct application/ACK.

## Actual file identity

SHA-256 values below hash the **raw file bytes**, including the `.mmd` trailing newline. The render manifest hashes normalized source with trailing whitespace removed; those normalized hashes were separately checked and match for all five. Each `.mmd` also matches exactly one current embedded Mermaid block after surrounding whitespace normalization.

| Diagram | Actual PNG SHA-256 | Actual `.mmd` SHA-256 |
|---|---|---|
| 08 | `13da4387ecb069ac8dbd8d7c405da7ef3b7158c9d3f318f11549a717f11d1ebe` | `aba2229f425862e24f7de6ce3659098628c2decc12274d88048b77d7a4b64d12` |
| 09 | `f6f685ccfb62bccd65c1432af2fe260736e7d072355f4b0c5ea1f65c59d3316a` | `99e1fb9e2251097de4d27bcfb2a06359781e538829735e589c7490df76e07236` |
| 17 | `a87b01a7e02e28ebdcb17bed630ba495130aaa19b2521430f496fe9ff2df7f31` | `9ac290c7ec5ea996a6e1488dbb4554d03f54265d0344ad334c649f64b0fde824` |
| 18 | `f047081e01f263cf2c426145a4ca77d709db00409ae28aa5b30b8d45dd70a0d2` | `15954e740735be9f3e06d983850113bea479db19f6ed172f4c1dbffa05748973` |
| 19 | `37b5d94d671656e04d62dd17e4662063851f23a431770f25a3dc1a33e383f2c6` | `4654f571dc2fc99f19bd4e19aa93ab2eebce7c83e36e182e6c2eff831171bb20` |

Current compared page SHA-256:

- `docs/e2e/canonical.md`: `42d3bceeba8cfaf7d602c0ea3704ac73ad8ab2a084283895a661bf0c3282120e`
- `docs/execution/qmdb.md`: `ed8eaf8444a2e2c6013118586984824f6b4222c6f2b3992c55a776a57748ccda`
- `docs/baselines/precut.md`: `6ca66de11a463c8b5e78c2793c0ff53665b45b2df0cddf90db72da865043e600`

Scope limit: these are whole-image visual inspections plus current source/prose comparison. No browser zoom/responsive layout claim, unviewed SVG-pixel claim, other-diagram visual claim, or runtime validation is implied.
