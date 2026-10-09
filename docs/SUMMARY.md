# Summary

* [Start here](README.md)

## Overview

* [Architecture](overview/architecture.md)
* [Roles and terminology](overview/glossary.md)
* [Rust interfaces](overview/rust-interfaces.md)
* [P2P and message paths](overview/networking.md)
* [Reading the interfaces](overview/interfaces.md)

## App transactions

* [Transaction admission and selection](tx/interfaces.md)
* [Pool backend survey](tx/README.md)

## Multimmit and Marshal

* [Consensus: native structure](consensus/README.md)
* [Block construction and body exchange](consensus/block-body.md)
* [Finalized ordered input](consensus/ordered-input.md)
* [Consensus open decisions](consensus/decisions.md)

## App scheduling

* [App and Multimmit](baton/README.md)
* [Pre-cut and Baton scheduling](baton/direction.md)
* [App callback behavior](baton/interfaces.md)

## App execution and storage

* [Execution: responsibilities](execution/README.md)
* [App execution and certification](execution/interfaces.md)
* [QMDB branches and canonical application](execution/qmdb.md)
* [State sync from certified results](execution/state-sync.md)

## E2E cases

* [Normal flow: transaction to state](e2e/normal.md)
* [Block body exchange](e2e/block-body.md)
* [Native proposal, DA, and finality](e2e/native-consensus.md)
* [Leader reports and proposal races](e2e/leader.md)
* [Direction receipt and branch execution](e2e/reschedule.md)
* [Finalized order and canonical application](e2e/canonical.md)
* [Startup, restart, and recovery](e2e/recovery.md)
* [App certification and queries](e2e/results.md)
* [State sync from certified results](e2e/state-sync.md)

## Benchmark baselines

* [Pre-cut execution without Baton](baselines/precut.md)

## Development and references

* [Commonware integration and development order](reference/integration.md)
* [Cases to verify](reference/verification.md)
* [Sources and document status](reference/sources.md)
