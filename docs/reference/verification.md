# 검증할 케이스

정상·누락·stale·취소·crash·recovery 경계를 확인할 계획이다. 이 페이지의 케이스는 실행한 테스트 결과가 아니다.

## 컴포넌트별 검증 케이스

| 컴포넌트 | 설계에서 확인할 케이스 | 실행 상태 |
|---|---|---|
| Tx / pool | 신규·중복·구조 invalid, proposal 취소, canonical outcome 전 cleanup 금지 | 미실행 |
| Builder / custody | Expected digest mismatch, body / parent 누락, durable storage 실패, late build completion | 미실행 |
| Native / delivery | Unresolved gap, authenticated empty, extension, history 누락, recovery 후 emitted prefix 보존 | 미실행 |
| Leader Baton | Threshold / deadline 경합, distinct report 중복, stale context, planner incomplete, cut 먼저 ready | 미실행 |
| Non-leader Baton | Missed / late direction, missing body, order 변경, producer와 executor 역할 분리 | 미실행 |
| Execution | Prefix reuse / input-state mismatch / runtime mismatch, cancel된 job 완료, partial-prefix commit | 미실행 |
| QMDB recovery | Commit 중 crash, ACK 유실, 같은 range 재전달, pruning 후 필요한 checkpoint 복구 | 미실행 |

Leader/view/context 교체는 [proposal freeze](../e2e/leader.md#planner-completion과-proposal-freeze의-경합)와 [native recovery owner](../consensus/README.md#실제-native-actor와-파일-구조)에서 읽는다. Old reports/advisory를 새 context에 재사용하지 않고, 이미 인증된 해석과 emitted canonical prefix를 보존해야 한다. Native adoption·continuation·recovery bridge는 여전히 개발·증명할 부분이다.

Missed direction은 [non-leader 경로](../e2e/reschedule.md#baton-lifecycle-non-leader의-direction재실행-요청)로 돌아가 local intended work와 canonical Commit을 진행한다. Late build는 [native 요청 correlation](../consensus/block-body.md#mempool에서-가져와-블록-생성), late execution은 [generation과 access fencing](../execution/qmdb.md#실행-요청을-받으면-분기-tree-정리)으로 구분한다. Direction 수신이나 취소된 worker의 완료를 새 cut barrier로 두지 않는다.
