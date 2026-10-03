# State sync: 인증된 실행 결과로 상태 동기

Validator Executor끼리 인증서와 change set을 교환한다. 적용 가능한 인증 결과가 먼저 준비되면 남은 실행을 줄일 수 있으며, 구체 전환·저장 계약은 미결정이다.

## State sync: 인증된 실행 결과로 상태 동기

**Validator Executor끼리 인증된 실행 결과로 상태를 동기화하는 기능을 정상 경로의 선택지로 둔다.** 재시작·뒤처진 노드에만 한정하지 않는다. 직접 실행 중에도 인증된 결과와 적용 가능한 change set이 먼저 준비되면 남은 실행을 줄일 수 있다. 책임·peer 통신 경로는 정한 요구사항이며, 전환 정책·자료 형식·검증·저장 구현과 안전성 / 진행성 검증은 아직 남아 있다. 직접 실행을 반드시 대체하거나 인증서를 기다리도록 정한 것이 아니다. State sync의 적용·복구도 [§6.5의 Executor와 durability 계약](qmdb.md#commit-요청을-받으면-branch를-canonical로-만들기)을 따른다. Certificate와 material의 별도 검증은 아래 표에 정리한다. QMDB sync target 검증은 native order와 execution certificate의 출처까지 자동 검증하는 API가 아니다.

| 단계 | 검증할 연결 | 다음 단계에 주는 것 |
|---|---|---|
| Certificate 확인 | Distinct eligible epoch validators의 동일 statement `f+1`, exact native range / input state / runtime / result | 검증한 target statement |
| Material 검증 | Exact local base와 delta / checkpoint / outputs가 target commitment에 대응 | Import 가능한 state material |
| 적용·복구 연결 | State / outputs / cursor의 선택한 durable commit 계약 | Imported verified canonical checkpoint |
| 이후 실행 | Imported checkpoint에서 다음 exact range를 직접 실행 / 검증 | 다음 range의 direct execution 결과와 서명 후보 |

ImportedVerified provenance와 canonical checkpoint의 recovery 연결도 import commit 계약에 포함한다. Recovery 때 direct execution 근거를 복원하지 못하면 해당 range에 own signature를 만들지 않는다. Imported material을 검증·적용한 행위를 해당 range의 own `DirectExecuted` signature로 바꾸지 않는다. Receiver는 원래 signers의 certificate를 전파하거나 인증 조회에 쓸 수 있고, 채택한 canonical base에서 **다음 range**를 직접 실행한 경우 그 다음 statement에 서명할 수 있다. Correctness certificate는 material의 보관·전파·조회 availability를 보장하지 않으므로 serve / retention 조건은 따로 정해야 한다. Delta / checkpoint format, root 종류, signer boundary, import codec과 crash recovery 방식은 §6.6의 빈칸에 남긴다.
