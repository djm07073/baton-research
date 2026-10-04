# Wave 13 exact reader delta

In `docs/overview/interfaces.md`, insert this paragraph immediately after the associated-type connection table and before the paragraph beginning `` `Executor::Block` is assembled ``:

```text
`CommitResult` is passed by value: use concrete cloneable receipt handles or recover copies of the same immutable receipt for multiple consumers; type equality and `Send` do not duplicate an owned value.
```

This clarifies concrete assembly ownership for the existing by-value callbacks. It changes no public trait bound, method/signature/type, Rust export, actor, framework, receipt schema, policy/backend choice or diagram. Exact durable result identity, per-receiver validation/processing/recovery and optional Baton exclusion from ACK remain intact. No other reader change is proposed.
