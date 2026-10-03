# Baton: 역할과 report 경로

Baton은 사전 실행·재실행과 intended-order report·direction을 조율한다. State finalization과 state sync의 승인자나 중계자가 아니다.

## 역할과 책임

Consensus에서 받은 후보 block을 execution에 넘겨 사전 실행을 예약한다. Local known inputs에서 intended order를 만들고 peer report를 교환한다. Leader는 이를 받아 direction을 선택·전파하며, non-leader는 direction을 받아 실행 계획을 바꾼다. 확정 순서의 전달·canonical 적용·state finalization·state sync는 Orderer / Executor가 직접 처리한다. Baton은 이 경로의 승인자나 대기 조건이 아니다.

**Baton**이 scheduling과 재실행 요청을 맡고, **Executor**가 speculative branch 관리와 canonical state 적용을 맡는다. **Runtime**은 tx 계산만 수행한다. Executor 내부에서도 canonical 적용은 single writer로 직렬화한다. Native signing·vote·finality authority는 consensus에 남는다.

## Report connection

Commonware P2P 위에서 authenticated window context, intended-order reports, advisory directions를 전달한다. 각 메시지는 epoch/view/history/actual parent/rule/window/frontier를 식별한다. Leader-local timer만으로 remote node가 window를 안다고 가정하지 않는다.

Report는 **실행 의도**이며 execution progress·state root·완료 증명이나 direction vote가 아니다. 같은 window에서 identity당 유효 원본 report 하나만 계수한다. Worker의 검증 완료와 leader owner의 snapshot admission은 다른 사건이다. 닫힌 snapshot에 늦은 report를 삽입하지 않는다.
