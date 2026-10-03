# Executor·Runtime·결과 인증 인터페이스

Runtime은 tx 계산을, Executor는 branch·저장·peer 통신을, 내부 ResultService는 결과 서명과 인증 검증을 맡는다.

## 인터페이스 개요

Rust 선언: [Executor](../overview/rust-interfaces.md#executor) · [Runtime](../overview/rust-interfaces.md#runtime) — 전체 원형은 「Rust 인터페이스」에서 관리한다.

`ExecuteRequest`는 exact base checkpoint·입력 order·runtime identity·generation을, `RescheduleRequest`는 새 요청과 superseded generation을 식별한다. 구체 struct layout은 미결정이다. `execute` / `reschedule`의 성공은 요청 prefix의 완료한 ExecutionResult이고, worker 취소·미완료를 성공으로 포장하지 않는다. `commit`은 exact OrderedRange·predecessor·evidence 검증과 missing-work 실행을 수행해 state/output/cursor의 recoverable durability가 끝난 뒤에만 CommitResult를 반환한다. Advisory cancellation으로 canonical mutation future를 drop하지 않으며 실패 / lost completion은 §6.5의 recovery 경계를 따른다.

`Runtime::State`는 선택할 QMDB variant에 맞춘 유효 branch-scoped state access다. Generic KV API나 immutable 과거 snapshot을 QMDB가 제공한다고 가정하지 않는다. `Runtime::Input`은 실행할 tx/body와 runtime context이고 `Output`은 application 실행 결과 / outputs다. Runtime은 branch를 canonical로 적용하거나 native 순서를 정하지 않는다. 부분 writes 뒤 실패한 branch는 Executor가 completed checkpoint로 채택하지 않는다. `read`는 실제 보관한 version과 readiness에 제한되며 결과 인증은 ResultService의 별도 경계다.

| 제안 인터페이스 | 입력 | 내부 처리 | 결과 |
|---|---|---|---|
| `Executor::execute` | Base checkpoint, exact intended input order, runtime, generation | Parent branch에서 fork → runtime 실행 → batch / outputs 생성 | ExecutionResult (checkpoint / context / outputs) |
| `Executor::reschedule` | 새 order와 context, superseded generation | 재사용 prefix 확인 → old suffix 취소 → 새 suffix 실행 | ExecutionResult (새 요청의 완료 prefix) |
| `Executor::commit` | Irrevocable ordered range, canonical predecessor, evidence | Matching completed work 확인 / 필요 시 실행 → QMDB canonical 적용 | Durable CommitResult |
| `Executor::recover` | Durable state / outputs / applied cursor | Canonical checkpoint 복원, transient branches 재구성 | Recovered execution base |
| `Executor::read` | Canonical cursor / root / query | 해당 commit의 실제 보관 state 조회 | State / output와 readiness |

`Executor::recover`는 startup/recovery 연결부가, `Executor::read`는 query caller가 요청한다. Branch handle은 context의 검증을 대신하지 않는다. 최소한 base state identity, runtime/version, exact input prefix, branch generation과 canonical cursor 연결을 확인한다.

Executor는 exact ordered input의 tx/body·runtime identity와 유효한 branch-scoped state access를 Runtime에 전달한다. Runtime은 pending mutations·outputs·실행 결과를 돌려주며, checkpoint의 context 결속과 canonical 적용 권한은 Executor가 관리한다. 이는 새 runtime 연결의 책임을 설명하는 계약이며 기존 `stateful::Application` trait와 바로 호환된다는 뜻은 아니다.

Runtime이 계산한 tx 결과와 worker가 요청 범위의 실행 시도를 끝내지 못한 사건은 구분한다. Executor는 해당 미완료 범위를 completed branch outcome으로 채택하지 않는다. Tx 실패의 state/output 의미와 미완료 시도를 Executor에서 Baton으로 알리는 계약·재시도 방식은 미결정이다.

Executor::read의 local 조회 readiness와 `f+1` 결과 인증은 별도다. Signer·collector·consumer의 연결은 [§2.10](../e2e/results.md#결과-endpoint-direct-execution과-f1-인증), Executor peer state sync는 [§6.7](state-sync.md#state-sync-인증된-실행-결과로-상태-동기)에서 설명한다.

## 결과 인증 trait

이 trait는 Executor 내부 결과 인증 역할이다. Executor가 peer 메시지를 받아 `collect` / `verify`에 전달하고, 검증 결과에 따라 state finalization을 확인하거나 §6.7의 state material 검증·적용을 진행한다. 여기의 인증 조회 성공은 material 확보·local durable 적용 완료가 아니다. Peer transport / codec / request·response와 state sync 전환 API의 구체 계약은 §6.6에 남긴다.

Rust 선언: [ResultService](../overview/rust-interfaces.md#resultservice) — 전체 원형은 「Rust 인터페이스」에서 관리한다.

`sign`은 완료한 ExecutionResult에서 own direct execution/validation provenance와 irrevocable exact range·canonical input-state·runtime 연결을 검증한 뒤 같은 full statement를 만든다. Advisory speculative order의 결과만으로 서명하지 않으며 ImportedVerified를 자신의 직접 실행으로 바꾸지 않는다. 서명된 결과의 correctness와 local apply/durability는 별도다. Per-block/chunk 등의 공통 서명 boundary는 정하지 않았다. Own statement/signature obligation은 선택한 recovery 계약으로 보관한다.

`collect`는 exact full statement와 distinct eligible epoch identities의 서명을 검증한다. `f+1` 미달은 `Ok(None)`이며 다음 실행이나 native cut의 barrier가 아니다. `verify`는 signatures뿐 아니라 irrevocable exact order와 canonical input-state chain 연결도 확인한 statement를 반환하는 application 계약이다. Primitive `Verifier::verify` 한 번이 이 전체 검증을 제공하는 것은 아니다. `certificate`의 `None`도 아직 인증 결과를 제공할 수 없다는 뜻이며 local state 부재와 구분한다. 원래 인증서의 전달·조회와 자신의 직접 실행 서명은 별도 경로다. Key/domain/codec/root 종류/common boundary/retention 선택은 §6.6의 빈칸에 남긴다.
