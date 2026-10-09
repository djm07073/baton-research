# Round 14: diagram arrows and completion boundaries

Reviewer: `/root/docs_alignment`. Read the current embedded Mermaid, corresponding `.mmd` sources and adjacent explanations after the Round 13 prose cuts, against `docs/baton/interfaces.md`. This is an independent documentation-flow audit, not a protocol execution trace.

The current mapping is: 02 normal transaction flow, 07 advisory scheduling, 08 canonical Update, 09 execution/QMDB lifecycle, 10 restart/redelivery, 11 result certification, 13 startup, and 14 import. The requested conceptual paths were checked under those actual names, rather than relying on an older number-to-topic mapping.

## Confirmed fixes

### Diagram 02: separate publication, admission and asynchronous dispatch

The prior native self-step said “Sign producer header, native DA / ordering” before the Relay request. That compressed later DA/order progress into an earlier step before body publication. The later optional candidate region also required the exact execution parent before “pending admission and dispatch,” conflating inexpensive admission with execution readiness; its “Execute transactions speculatively” label could be read as completing CPU work before the next native Activity/Update.

Root approved these minimal replacements in both `docs/e2e/normal.md` and `docs/assets/diagrams/diagram-02.mmd`:

```text
N->>N: Sign producer header
...
opt Eligible live candidate
    A->>Q: Admit or update pending candidate
    Q->>Q: Start asynchronous work when exact parent and worker capacity are ready
end
```

The unchanged adjacent text still says speculation may finish before **or after** Update. Candidate registration does not wait for a completed execution parent, and starting asynchronous work does not add a speculative completion gate to native Activity, finality or canonical delivery. The detailed native DA/view progression remains in diagram 15 and its native source map.

### Diagram 13: schedule only on successful readiness and valid App state

The diagram explicitly returned “Ok(()) or Stopped error” from readiness, then showed an unconditional scheduling-resume step. Root approved replacing the App self-step with:

```text
A->>A: On ready success and valid App base, re-evaluate candidates and schedule
```

Applied to `docs/e2e/recovery.md` and `docs/assets/diagrams/diagram-13.mmd`. This preserves the two readiness conditions and retained-candidate wakeup without a new lifecycle actor, callback flag or failure protocol. Existing prose distinguishes open-time recovered-verification failure, stopped readiness and owned service teardown.

No other diagram source changed in this round. Root rendered only 02 and 13; post-render inspection is recorded below.

## Arrow-to-contract matrix

| Diagram / arrows | Meaning checked against the canonical flow | Result |
|---|---|---|
| 02 proposal → stage → Custody token → body digest | Propose constructs exact contextual bytes; stage response means accepted storage work, not a disk flush. The later local verify is the durable custody fence before signing. | Consistent. Accepted token and later verdict remain distinct labels. |
| 02 / 04 / 05 verify request and receiver resolution | These are logical request/verdict events. The existing Automaton future first returns a oneshot receiver; bounded async App request work later sends the result. No transaction-completion return is implied by true. | Consistent with the explicit callback handoff paragraph and “receiver resolves” wording. Immediate receiver-handle return is intentionally not another diagram participant. |
| 02 sign → Relay and separate complete-block publication | Signing precedes the staged full-block broadcast request. Native DA/view/order are not grouped into that signing step. Relay Feedback is local; the body page retains its no-op/remote-custody caveat. | Corrected as above. |
| 02 pending admission → asynchronous work | Eligible metadata can be retained while the exact execution parent or worker capacity is unavailable. The selected scheduler dispatches later from the ready parent. | Corrected as above; no native wait for speculative CPU completion. |
| 07 direction → pending policy → worker result | Direction is authenticated advice, not a new canonical input. Body or execution-parent absence leaves work pending. Worker result means effects for the exact path, not canonical apply or certification. | Consistent. Adjacent paragraph requires current-attempt/ancestry acceptance and actual database-access fences. |
| 08 native Activity → Marshal history/body work | Activity is a native observation into the supplied Marshal, not an App execution request or public finality proof constructed by App. Marshal can hold ordered delivery at a gap. | Consistent with the source-owned native activity and canonical input contracts. |
| 08 Update → retained inbox → Feedback → worker wakeup | The synchronous report hands off full Update and token promptly. The worker consumes exact continuous indices independently, including without previous verify or candidate metadata. | Consistent. Feedback does not promise execution or durability; no extra approval actor appears. |
| 08 exact replay / new input branches | Replay checks exact durable identity without duplicate effects. New input reuses matching work, validates an import or finishes/repairs from the canonical predecessor. | Consistent. Scheduler priority cannot reorder the Update stream. |
| 08 storage completion → App advancement → Exact ACK → Marshal cursor | Storage completion includes state/output/applied identity/provenance. App advances once and schedules pool maintenance before ACK. Marshal cursor persistence is a later distinct operation. | Consistent with core worker and E2E timing prose. The diagram does not require pool maintenance or peer result signatures to finish before ACK. |
| 09 worker CPU result → selected preparation | Completed effects are bound to input/parent/runtime; roots may be deferred until selected. A completed CPU result is neither a durable applied record nor a certificate. | Consistent. The callback page owns current-attempt acceptance and canonical writer rechecks inside these abstract steps. |
| 09 canonical writer → persistence → success/failure | Only a successful durable record supports promotion; failed completion leads to recovery rather than a claimed ACK. Actual apply may already have advanced before later durability failure. Retention/reference obligations control reclamation. | Consistent with Round 10 corrected labels and QMDB failure contract. The App execution owner, workers and storage are internal responsibilities, not mandated services. |
| 10 recovered App state + Marshal cursor → replay | Recovered durable applied identity may be ahead of Marshal's durable ACK cursor. Same exact input ACKs without effects; next input applies from recovered canonical base; identity/gap error stops advancement. | Consistent. No new finality or execution ACK protocol is introduced. |
| 11 direct result → selected commitment → signature → peer certificate | The result-signing path requires exact irrevocable input/base and retained direct-execution provenance. f+1 matching eligible signatures create the result endpoint, while local durability remains separate. | Consistent. This is a certification scenario, not a requirement to rerun already matching direct speculative work or block canonical apply on peer signatures. |
| 13 services/handles → Engine open → recovered verify → start/ready | App custody and retained delivery ingress exist before native recovery requests; speculative scheduling does not need to run to answer custody. Readiness is an initial milestone, not ongoing App health/durability evidence. | Consistent after the explicit success/App-base scheduling condition above. |
| 14 certificate → material validation → canonical writer | Certificate receipt alone does not stop unfinished execution. Verify exact subject and applicable material, then use the same canonical writer/access fencing as direct work. | Consistent. Adjacent text keeps target/base and floor/App-state authority distinct. |
| 14 durable import → matching retained Updates → ACK | Only exact durable imported coverage can satisfy ordered retained deliveries. Imported provenance remains imported; no new own direct-execution signature is emitted. | Consistent. Pool maintenance is scheduled, not an ACK approval condition. |

## Dependency spot checks

- Diagram 01 remains an ownership graph; surrounding text explicitly rejects one actor per box. Its ACK edge follows the canonical writer and durability path.
- Diagrams 04/05 retain the previously corrected custody-return and subscription-versus-fetch distinctions. Source labels need no repeat render.
- Diagram 06 keeps planning and native cut in parallel, and labels its actual-leader context path as proposed integration. Diagram 12 is explicitly future proposal-policy work, not a new current callback or synchronous planning wait.
- Diagram 15 keeps DA and native view/finality as separate parallel branches, with native eligibility still required. Its ordinary vote label indicates broadcast to peers, not a unique leader acknowledgement route.
- Diagram 17's graph separates completed effects, optional rootless representation, selected roots, canonical writer and covering database durability. The retained durable identity node joins the App linkage and covering durability obligations; no standalone Storage trait is introduced.
- Diagram 18 compares exact execution parents rather than declaring identical block identities interchangeable.
- Diagram 19 uses the same callback, Marshal, execution and durability path for Pre-cut without a Baton report/direction actor or extra orderer.

Dashed arrows are not treated as a universal method-return marker: several diagrams use them for peer messages and observations. Their explicit labels and adjacent contracts identify the actual synchronous call, asynchronous receiver result, completed effects or durability event. No additional legend or cross-cutting actor abstraction is necessary.

## Validation

`git diff --check` passed after the source edits. Existing assets were not rerendered speculatively or subjected to repeated checks solely to produce a pass. Only changed diagrams 02/13 were target-rendered; runtime correctness and the missing full Baton native policy remain unclaimed.

I opened the actual regenerated PNGs under `docs/assets/diagrams/` after root copied the source-matched render results and updated the manifest. Both passed pixel inspection:

- **02:** “Sign producer header” fits its own step. Eligible-live-candidate admission and the separately conditioned asynchronous worker start are visibly distinct. The longer worker-start label wraps within the optional region without clipping or touching the following native Activity row. Update, durable state, scheduled pool maintenance, ACK and cursor persistence remain legible.
- **13:** The new readiness/App-base condition wraps into four readable lines at the App lifeline. It does not overlap the ready result, self-arrow or custody note. Recovery verification remains visibly before actor start and readiness. No further layout edit was needed.

| Diagram | SHA-256 `.mmd` | SHA-256 `.png` |
|---|---|---|
| 02 | `10993130241a9007c7ae50679e3915a59098bac96c1349e5867c0e79c5976223` | `d0a7d1f285a24548a8295ccda37fac1d8781ffbe1a87dde8c160c43cb83f0c9e` |
| 13 | `219804c5a7590bc1a7ea9fadac1ca015dc67528b5863692622e18edac2494c1f` | `31c8f222e26ff8f8cf3074a9d1755cc0924b2ca70fafd29265ae780137d2ae04` |
