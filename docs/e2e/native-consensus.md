# Block proposal, DA, and cut finality

**Multimmit owns native signing, voting and finality.** The App provides payloads and validity/custody verdicts. Marshal consumes native activity to retain and deliver the ordinary finalized total order.

<a id="normal-native-consensus-producer-da--leader-proposal--finality"></a>

## Native producer, DA and view/finality paths

This diagram highlights the App connections. Native protocol details remain in the [consensus source map](../consensus/README.md).

```mermaid
sequenceDiagram
    participant P as Producer native owner
    participant A as Producer App
    participant V as Validator native owner
    participant B as Validator App
    participant L as Native leader / view owner
    participant M as Multimmit Marshal
    P->>A: Automaton::propose(Context)
    A-->>P: Body digest through proposal receiver
    P->>A: Automaton::verify(Context, body digest)
    A-->>P: Valid durable custody through true verdict
    P->>P: Sign producer header
    P-->>V: Signed header on native data plane
    V->>V: Native authentication and eligibility checks
    V->>B: Automaton::verify(Context, body digest)
    B-->>V: Valid durable custody through true verdict
    par Application speculation
        B->>B: Eligible candidate enters App scheduler
    and Native DA
        V->>V: Continue DA path and native durability gates
        V-->>P: DA vote
        P-->>V: DA certificate when native threshold is met
    and Native view / finality
        Note over P,L: DA certificate assembly and leader proposal progress are independent, native eligibility still applies
        L-->>V: Native leader proposal and required parent evidence
        V-->>L: Broadcast native votes to peers (L included)
        L->>L: Native finality / extension processing
        L-->>M: Reporter::report(Activity)
        M->>M: Existing history interpretation and ordered body delivery
    end
```

[Open full-size diagram](../assets/diagrams/diagram-15.svg)

The App's speculative execution is independent of the native DA path after successful validity/custody verification. Neither speculative worker completion nor application delivery ACK is a native vote/cut prerequisite. Native availability, ancestry and durability gates still apply; the body validity callback is not permission to bypass them.

Native view work can already be running during producer validation. The leader/view-owner lifeline represents one native owner; each view owner processes finality locally.

The native data message carries the signed producer header. Marshal separately broadcasts the full `TransactionBlock` containing header and body. A receiver can therefore have a header while still waiting for its body. Verification begins when native eligibility chooses the request, not for every packet arrival. [Body flow](block-body.md)

Native activity is also useful for App observations through a composed `Reporters` value. It is distinct from Marshal `Update`: the former reports native activity, while the latter supplies an indexed finalized complete block and application ACK token. The [current assembly](https://github.com/0xEyrie/monorepo/blob/6233438985d8249d2b2bc1204191d5d405652288/examples/log-multimmit/src/node.rs#L306) passes native activities to Marshal and an App handle.

For Baton to change the agreed execution order, a separate native proposal-policy extension must preserve selected leading prefixes through validation, extension and recovery. Current App scheduling callbacks alone do not implement that extension. [Open native decisions](../consensus/decisions.md)
