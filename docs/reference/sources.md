# Sources and document status

**Current user decisions and the inspected parent checkout define this implementation design.** Earlier papers, linked documents and review receipts retain their historical meaning.

## Sources and document status

| Source | Role in these docs |
|---|---|
| [Current native checkout 6233438985d8249d2b2bc1204191d5d405652288](https://github.com/0xEyrie/monorepo/tree/6233438985d8249d2b2bc1204191d5d405652288) | Current Multimmit Engine, Marshal, existing callbacks and `log-multimmit` assembly |
| [Historical native pin 534af0ede48affd35b2111522527547b4cc9bf72](https://github.com/commonwarexyz/monorepo/tree/534af0ede48affd35b2111522527547b4cc9bf72) | Earlier research and reusable primitive investigation; its absent-Marshal limitation is superseded |
| [Baton paper](../../baton-paper.md) | Algorithm motivation, conditional arguments and evaluation plan |
| [App/scheduler review](../../assets/review/app-scheduler-20261009/native-audit.md) | Current callback/custody/delivery source audit and failure-boundary findings |
| [Earlier reuse review](../../assets/review/commonware-reuse-20261004/README.md) | Source-pinned historical ecosystem pool/storage/API research |

The [Google research draft](https://docs.google.com/document/d/1PtUpMGMNMkyo1UEY2bNciJD3oIiGLRf407PW_T3Er5I/edit) and [earlier Google implementation specification](https://docs.google.com/document/d/10x4RvqG8e07Tai0s20e-wpCfz8COgH0JGR5daKE1xO8/edit) are provenance references without automatic synchronization. Repository Markdown is canonical. No GitBook/Google Docs publication is implied by local edits.

Existing Engine/Marshal behavior is source-grounded. App-owned pool, PreCut/Baton schedulers and application execution are proposed integration work. The authenticated Baton policy extension remains unimplemented/unproved. Documentation checks do not establish protocol correctness, E2E execution, crash recovery of an App implementation or performance benefits. [Verification plan](verification.md).
