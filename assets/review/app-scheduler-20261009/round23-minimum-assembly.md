# Round 23: minimum App assembly

## Finding and disposition

The integration recipe made the optional App consumer of native `Activity` look mandatory: it always constructed `Reporters::from((marshal, app_activity))`. Nearby prose in the Rust reference and consensus entry page also unconditionally called for two typed App handles. The native reporter supplied by Marshal already satisfies Engine's required interface.

Applied by the owning agents:

- `docs/reference/integration.md`: App custody/output processing receives `marshal.clone()`, and the minimal Engine configuration uses `reporter: marshal`. A following conditional paragraph shows `Reporters::from((marshal, app_activity))` only when App also consumes native Activity.
- `docs/consensus/README.md`: pass the Marshal mailbox directly; the second App handle and existing fanout are conditional.
- `docs/overview/rust-interfaces.md`: use Marshal's mailbox for native reporting; use a distinct typed App Activity handle only if App consumes those observations. Required retained Update handoff remains explicit.

I read the resulting three pages after both owners confirmed their edits. No extra actor, adapter trait, public event, or callback is introduced. No diagram changes are needed.

## Source basis and ownership

| Source | What it establishes |
|---|---|
| `consensus/src/lib.rs:258` | `Reporter` is `Clone + Send + 'static`, has one associated Activity type, and a synchronous `report` method. |
| `consensus/src/multimmit/engine/mod.rs:320`, `:411` | Engine accepts a generic `Reporter<Activity = Activity<V, H::Digest>>`; it does not require `Reporters` or an App Activity consumer. |
| `consensus/src/multimmit/marshal/mailbox.rs:263` | Cloning the supplied mailbox shares its existing service handles and subscription slots. It does not start another service. |
| `consensus/src/multimmit/marshal/mailbox.rs:492` | The mailbox implements native Activity reporting directly, including the certificate-release path and advisory router path. |
| `consensus/src/reporter.rs:21` | Existing `Reporters` optionally fans out the same associated Activity type. It does not combine native Activity and Marshal Update into a single associated type. |
| `examples/log-multimmit/src/node.rs:297`, `:318` | The example gives App a Marshal clone before moving the mailbox into optional native-Activity fanout. The revised minimal recipe preserves that ownership order. |

These are local source inspections at the current pinned native revision, not a new compiled integration or protocol test.

## Other optional facilities

- `docs/baton/interfaces.md#native-activities-and-optional-local-notifications` already routes native Activity directly to Marshal and makes App observation optional; missing hints may reduce speculation but cannot stall canonical delivery.
- `docs/overview/interfaces.md` already makes separate typed App handles conditional on both Activity types entering App.
- `docs/e2e/recovery.md` creates the required Automaton and canonical-output handles, keeps App custody processing available during native open, and retains startup/recovery ownership. It does not require a native Activity observer.
- The collector/direction protocol remains Baton-specific, while PreCut and Original comparisons do not require it. Native policy integration remains an explicit implementation gap.
- Concrete pool backend reuse remains conditional. Resolver, full-body custody, retained canonical Updates, application durability, and service lifetime ownership are required connections and were preserved.

No further minimum-assembly correction is warranted. No tests, global render, or external action was needed for this prose/pseudocode correction.
