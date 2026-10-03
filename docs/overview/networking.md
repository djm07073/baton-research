# P2P와 메시지 경로

Commonware P2P를 공유하면서 tx·body·합의·Baton·execution 메시지의 논리적 경로를 나눈다.

## P2P 연결과 message planes

| Plane | 누구 사이인가 | 운반하는 것 | Channel ID |
|---|---|---|---|
| Native data | Native peers | `DataMessage::Block / DaVote / DaCertificate` | 기존 example `0` |
| Native consensus | Native peers | `ConsensusMessage::Proposal / Vote / NoVote / Nullify` | 기존 example `1` |
| Native certificates | Native peers | `CertificateMessage::Nullification / Vqc / Lqc` | 기존 example `2` |
| Native resolver | Native peers | Native view proofs와 recovery 자료 | 기존 example `3` |
| Application tx | Tx peer / admission adapter / producer pool | Tx bytes / inventory의 구체 format은 미결정 | |
| Application body | Body store / resolver peers | Body bytes와 exact reference에 대한 fetch / response | |
| Baton report | Validator Baton ↔ leader Baton | Window 안내 / signed intended-order report | |
| Baton direction | Leader Baton → producer / executor Baton | Advisory direction | |
| Execution result / state sync | Validator Executor ↔ Executor; 인증 조회는 consumer → Executor | Exact statement signatures / result certificates / change sets와 조회·재요청 | |

추가 plane은 같은 Commonware network의 logical channels로 연결할 수 있다. Plane마다 새 물리 connection 또는 별도 P2P stack을 만들기로 정한 것은 아니다. 인증 transport와 message-level context 검증도 다른 책임이다. Tx / body / report의 CPU·queue·bandwidth 경쟁은 존재하므로, 논리적 no-wait를 물리적인 resource isolation 보장으로 설명하지 않는다. Runtime thread / pool 배치와 quotas는 미결정이다.
