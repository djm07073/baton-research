# Sources and document status

**Current requirements and pinned source determine this design.** Research drafts and earlier snapshots supply provenance. Their historical claims do not override the latest user decisions or current documentation.

## Sources and document status

The explanation follows [Tempo Technical Overview](https://app.notion.com/p/2dfc1352439b801db5b6cf6fe21fc315?pvs=204): **overall architecture → component responsibilities/interfaces → propose/verify/finalize sequences**. [Tempo DeepWiki](https://deepwiki.com/tempoxyz/tempo/2-architecture-overview) provides a useful presentation of layers, source-file mapping, actors, P2P channels, and communication. These are structural references; technical claims and reuse feasibility are grounded in pinned Commonware code. Tempo's Simplex, Reth/REVM, and Engine API implementation are not adopted. Baton uses native Multimmit, generic execution, and QMDB.

The [Baton research draft](https://docs.google.com/document/d/1PtUpMGMNMkyo1UEY2bNciJD3oIiGLRf407PW_T3Er5I/edit) records algorithm provenance and conditional arguments. The earlier [Google implementation specification](https://docs.google.com/document/d/10x4RvqG8e07Tai0s20e-wpCfz8COgH0JGR5daKE1xO8/edit) is a historical detailed-contract reference, without automatic synchronization with this architecture.

Diagrams and application interfaces are design plans. Reviewing pinned source and attachment boundaries does not establish completed native correctness, performance, or QMDB crash-recovery tests. Fill open decisions only after review in each layer's decision table.
