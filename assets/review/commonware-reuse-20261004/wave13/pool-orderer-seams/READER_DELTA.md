# Exact minimal reader delta

In `docs/tx/README.md`, under “Nunchi whole-actor connection”, replace only:

> **Nunchi supplies the queue/selection actor; TxPool connects its payload and canonical lifecycle to Baton.**

with:

> **Nunchi supplies the queue/selection actor; TxPool adds payload hooks and connects durable Executor outcomes to that actor.**

This names the already documented direct Executor→TxPool→selected backend outcome path and preserves Baton scheduling independence. No new upstream API/actor/default or selected completion contract is implied. Keep the rest of the paragraph, all citations/headings, Rust contracts/export and diagrams unchanged. No other reader delta is recommended.
