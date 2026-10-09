# Round 25: final PNG visual QA

## Inspection method and result

I opened the actual current PNG files with `view_image` for diagrams **02, 03, 07, 10, 11, 13 and 14** and inspected their pixels, including participant names, guard labels, nested branches, reply arrows, bottom notes and page bounds. All seven pass: no clipped text, unreadable overlap or arrow/label collision was found. The two tallest previews (02 and 14) were uniformly reduced by the image tool, with all labels still readable.

For **06 and 12**, this round reuses the actual PNG inspection recorded in `round21-empty-report-restoration.md`. Both current PNG hashes and complete `.mmd` byte hashes exactly equal that earlier receipt. I reread their current source and surrounding leader prose, but do **not** claim a new pixel inspection for those two unchanged images.

All nine current inline Mermaid blocks equal their corresponding `.mmd` source after trailing-newline normalization, and each normalized source hash matches the render manifest. This source check supplements the pixel review; it is not its substitute. No source edit, rerender or manifest change was warranted.

## Visual and semantic results

| Diagram | Page | Result |
|---|---|---|
| 02 | `docs/e2e/normal.md` | All six lifelines and long callback labels are readable. Local signing follows verification. Eligible candidate admission is separate from the later exact-parent/capacity start; the start is explicitly asynchronous. Canonical work reaches a durable state/output/identity/provenance reply before ACK. No native wait on execution is added. |
| 03 | `docs/e2e/normal.md` | Selected/unselected/invalid branches and retirement note fit cleanly. The pool is App-owned, selection retains candidates, and canonical durable outcomes drive later maintenance. The prose keeps logical class policies open. |
| 06 | `docs/e2e/leader.md` | Reused unchanged passing pixel receipt. The zero-report guard excludes planning on an empty snapshot; native cut work is a parallel branch with an explicit no-wait note. Proposed native integration remains labeled as such. |
| 07 | `docs/e2e/reschedule.md` | Nested context/conflict/body-parent branches fit without overlap. The permitted direction changes pending scheduling only; completed-result reply returns to App rather than becoming a direction ACK. The bottom note excludes direction approval/execution-completion rounds. |
| 10 | `docs/e2e/recovery.md` | Exact already-applied replay, next unapplied input and identity conflict/gap are legible distinct alternatives. A new input reaches durable completion before ACK; replay checks exact applied identity rather than reexecuting. Marshal cursor persistence is a separate final action. |
| 11 | `docs/e2e/results.md` | Signature exchange, full-subject validation and f+1 branch are readable. Certification and local durability are explicitly separate; imported work does not acquire own direct-execution provenance. There is no Baton/report actor or canonical ACK gate. |
| 12 | `docs/e2e/leader.md` | Reused unchanged passing pixel receipt. The first input is a frozen nonempty snapshot; proposal-freeze recheck and pre-adoption native fallback are distinct from preserving an already authenticated interpretation. The adjacent page labels the entire integration as future work. |
| 13 | `docs/e2e/recovery.md` | Startup replies and recovered-verify loop are legible. App/Marshal are available before Engine recovery callbacks; live scheduling follows both native readiness success and valid App base. The required App handles are Automaton and Update reporter, consistent with optional App native-Activity consumption. |
| 14 | `docs/e2e/state-sync.md` | All nested certificate/material/durability guards fit. Missing material continues valid direct work. ACK is conditional on retained Updates exactly covered by the durable imported prefix; pool maintenance is scheduled rather than awaited. The failure path has no ACK and imported provenance is explicit. |

## Artifact receipts

Paths are under `docs/assets/diagrams/`. These are SHA-256 hashes of the complete current file bytes; `.mmd` values include their trailing newline. Render-manifest source hashes use the equivalent inline source without that final newline.

| Diagram | PNG SHA-256 | `.mmd` SHA-256 |
|---|---|---|
| 02 | `d0a7d1f285a24548a8295ccda37fac1d8781ffbe1a87dde8c160c43cb83f0c9e` | `10993130241a9007c7ae50679e3915a59098bac96c1349e5867c0e79c5976223` |
| 03 | `219d554ce6b428a779112236bc44a0805d1327f2d72eb842dd29ebd3d98ec402` | `2ab48f96178be1f038323ab62a7eb86fe16f591aea13fae061cda1084ef85fe5` |
| 06 | `b869cad64219e42d4234fe8bd58d602b3283245cdb533fec1be70b38c876898b` | `3851356a09d3fbc31a11189b82e94ad523a591f009b41fd35cac147f89fd6b15` |
| 07 | `efb0ce1d761f287210f27c830202e6d750a05789d496e71221a5e337c693679d` | `b07a9b83cf298930af4a554ff8c37864136a87b8b88f7b377cac1104a05c8536` |
| 10 | `5ab354711f76300753f510245833d479326e6826a80f35256d075d9de9d9deda` | `ead721911946244f3eb6744768992d43f997a92b19fbe3e4f1def0cbb764c79c` |
| 11 | `04769dca2c40f512eb6176ba81b48d7a119d839ae502212e70b8dc351386b6b8` | `95097fdb320bbca5d40d49936bfa5654e002b1a44492549002a032ab6c126263` |
| 12 | `d607cf47fe4782d6678cd14615d53301895fc28d8564c4680ba830d8856c494b` | `b63f0d907f6cfebe31aa2f6a21b97d5d88c0e348c4ca05c5486f5f2c08cb221a` |
| 13 | `31c8f222e26ff8f8cf3074a9d1755cc0924b2ca70fafd29265ae780137d2ae04` | `219804c5a7590bc1a7ea9fadac1ca015dc67528b5863692622e18edac2494c1f` |
| 14 | `79581a02671e9a1f18f557fc5f8f098a483b10fb45aca88620c92d7e2e51c756` | `0c68a0d001b0da32157f2eba0a7b3a13e37196a06a2eafd4341571d8ca0d61a8` |

No change was made to the nine sources, pages, PNGs or manifest by this review. It validates these artifacts' readability and agreement with the current design prose, not implementation or protocol correctness.
