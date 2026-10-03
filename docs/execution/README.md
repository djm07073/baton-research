# Execution: 역할과 책임

Executor가 직접 실행·state finalization·state sync·로컬 적용과 복구를 책임진다. ResultService는 Executor 내부 역할이다.

## 역할과 책임

**Executor는 validator의 실행·state finalization·state sync를 책임진다.** Baton의 execute / reschedule 요청과 Orderer의 직접 확정 입력을 받아 Runtime과 QMDB로 state·outputs를 관리한다. 다른 validator의 Executor와 직접 소통해 실행 결과를 인증하고, 인증된 결과를 받아 로컬 상태를 동기화한다. Bank 잔액·nonce 모델은 이 문서에 넣지 않는다.

| 책임 | Executor가 처리하는 것 | 경계와 완료 조건 |
|---|---|---|
| 직접 실행 | Runtime 계산, branch 관리, prefix 재사용·suffix 재실행 | 완료한 ExecutionResult; speculative 결과를 canonical로 간주하지 않음 |
| 결과 서명 | 내부 ResultService로 자신의 직접 실행 결과를 검증·서명 | 확정 exact input·올바른 input state·runtime·전체 결과에 결속; imported 결과의 own signature 금지 |
| State finalization | Peer signatures / certificate 검증과 원래 인증서 보관·전파 | 동일 full statement의 distinct eligible f+1 signatures와 irrevocable order / input-state chain 확인 |
| Executor peer 통신 | 서명·인증서·change set·outputs 송수신, 조회·재요청·serving | Executor ↔ Executor; Commonware P2P 재사용, Baton이 중계·승인하지 않음 |
| State sync 전환 | 검증된 인증서와 적용 가능한 material이 먼저 준비되면 남은 실행을 중단하고 적용 | Matching base와 safe cancellation / writer fence; 인증서만으로 실행 중단하지 않음 |
| 로컬 적용·복구 | 직접 계산하거나 검증한 state / outputs / cursor를 QMDB와 commit metadata에 저장 | Recoverable durable CommitResult; state finalization 확인과 별도 완료 조건 |
| 완료 전달 | Orderer에 durable delivery ACK, TxPool에 canonical tx 결과; Baton에는 실행 결과 / 선택적 적용 알림 | Baton의 응답·승인은 결과 인증·state sync·적용·ACK의 선행조건이 아님 |

ResultService는 Executor 내부의 서명·수집·인증 검증 책임을 나눈 trait다. Peer 통신과 state material의 검증·적용·저장·복구는 Executor가 소유한다. Baton끼리 교환하는 intended-order reports / directions와 별도 경로다. 인증서·material이 준비되지 않으면 직접 실행을 계속하며, 다른 노드의 완료를 기다린 뒤에만 실행을 시작하는 공통 barrier를 만들지 않는다. 인증서가 local ordered input보다 먼저 오면 unresolved 순서를 대신 확정하지 않고 pending으로 두거나 인증 이력을 복구한다.

Speculative state와 canonical state를 분리한다. Execute는 branch 결과를 만들며 canonical commit authority를 가지지 않는다. Commit과 state sync는 증명된 exact ordered input과 올바른 canonical predecessor에 결속된 결과만 적용하고 canonical single writer를 공유한다. 이미 진행 중인 canonical mutation을 sync 도착 때문에 drop하거나 경쟁 writer로 우회하지 않는다. 구체 전환·race·failure 계약은 §6.6의 미결정 사항이다.

## 미결정 사항

| 항목 | 결정 |
|---|---|
| Runtime / tx semantics | |
| QMDB database variant / state encoding / root 종류 | |
| Canonical operation / batch-boundary derivation / logical root 연결 | |
| Stateful actor 재사용 범위 | |
| Branch key / checkpoint granularity | |
| Execution scheduling / cancellation / worker fencing contract | |
| State / outputs / cursor atomic commit 방식 | |
| Branch pruning / memory / disk budget | |
| Replay / checkpoint / state sync | |
| Query interface / certified result 연결 | |
