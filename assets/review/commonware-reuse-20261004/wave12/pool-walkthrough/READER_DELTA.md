# Exact minimal reader delta

In canonical `docs/overview/rust-interfaces.md`, immediately before `TxPool::select`, replace only:

```text
    /// Selection alone does not retire transactions from the pool.
```

with:

```text
    /// Selection alone does not establish canonical retirement.
```

No declared trait/method/type/signature, policy, actor, backend or diagram changes. Detailed cancellation/destructive ownership/canonical result requirements already exist in Tx/body/interface/E2E pages. If adopted, run `npm run docs:interfaces` to refresh the generated `docs/assets/interfaces/baton.rs` from the canonical Rust fences; do not independently edit the export. No other reader edit is proposed.
