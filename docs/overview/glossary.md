# 역할과 공통 용어

모듈 이름과 노드 역할, 입력·결과의 완료 조건을 구분한다. 새로운 이름을 늘리기보다 이 페이지의 표기를 사용한다.

## 역할과 용어

모듈 이름은 아래 여섯 개로 통일한다. `owner`, `controller`, `adapter`는 내부 책임이나 Commonware 연결을 설명하는 말이며 별도 모듈 이름으로 늘리지 않는다. Trait 경계가 actor·crate·server의 개수를 결정하는 것도 아니다.

| 모듈 이름 | 한 가지 중심 책임 | Rust trait 위치 |
|---|---|---|
| `TxPool` | Tx admission·후보 보관·batch 선택·결과 반영 | [§3.2](../tx/interfaces.md#인터페이스-개요) |
| `BlockService` | Producer body 생성·영속 보관·전파·조회·custody | [§4.2](../consensus/block-body.md#인터페이스-개요) |
| `Orderer` | Native 증거와 이력을 해석해 확정 실행 순서 전달 | [§4.5](../consensus/ordered-input.md#합의와-baton-연결) |
| `Baton` | 실행 순서 조율·사전 실행 예약·재예약 | [§5.2](../baton/interfaces.md#인터페이스-개요) |
| `Executor` | 실행 branch 관리·state finalization·state sync·QMDB 적용·복구·조회 | [§6.2](../execution/interfaces.md#인터페이스-개요) |
| `Runtime` | 주어진 branch state에서 application tx 계산 | [§6.2](../execution/interfaces.md#인터페이스-개요) |

`TxPolicy`는 정적 분석·선택 정책, `Planner`는 direction 선택 알고리즘의 보조 trait다. `ResultService`는 **Executor 내부**에서 결과 서명·수집·인증 검증·조회를 맡는 보조 trait다. Executor가 peer 통신과 state sync를 소유하며 ResultService를 별도 최상위 서비스로 두지 않는다. Trait 경계만으로 별도 actor·crate 배치를 결정하지 않는다. Native `Multimmit`, `Automaton`, `Relay`, `Reporter`, `DatabaseSet` 등의 upstream 이름은 그대로 사용한다.

| 데이터 이름 | 뜻과 완료 조건 |
|---|---|
| `StoredBody` | Body와 필요한 parent 자료의 local durable custody 완료. Native header 인증은 별도 |
| `CandidateBlock` | Authenticated producer header와 StoredBody가 exact context로 대응한 실행 후보. Cut 포함·순서 확정은 별도 |
| `Report` / `Direction` | 실행 의도 보고 / leader의 advisory 순서 안내. Baton은 모듈이고 direction이 메시지 이름 |
| `PreparedPolicy` | 완료한 유효 후보 평가에서 나온 proposal 결속 후보. Native owner의 actual-context 재검증·채택은 별도 |
| `OrderedRange` | 인증 이력에서 확인한 뒤집히지 않는 연속 exact 실행 입력 |
| `Checkpoint` | 특정 base state·runtime·입력 prefix의 실행을 끝낸 재사용 지점. Raw QMDB batch와 다름 |
| `ExecutionResult` | 완료된 speculative 실행의 checkpoint·context·outputs. Canonical 적용 완료는 아님 |
| `CommitResult` | Exact ordered range의 state·outputs·cursor가 함께 복구 가능한 local durable 적용 결과 |
| `ExecutionStatement` / `ResultCertificate` | Exact range·base·runtime·result에 서명하는 subject / 같은 subject의 distinct eligible `f+1` signatures |

Producer·validator·leader·non-leader는 노드의 **역할**이다. Cut은 native finality 사건이다. 불변 순서 경계(immutable ordering frontier)는 direction이 재배열할 수 없는 입력 prefix의 끝이고, `AppliedCursor`는 local state를 durable 적용한 위치다. 두 경계와 `ExecutionResult`·`CommitResult`·`ResultCertificate`의 완료 조건은 합치지 않는다.

<details>
<summary>이전 이름에서 새 이름으로 찾아보기</summary>

| 이전 표기 | 통일한 표기 |
|---|---|
| ExecutionController / scheduling controller | Baton |
| BranchOwner / CanonicalApplyOwner / Execution owner | Executor 내부의 branch 관리 / canonical single writer |
| Application runtime | Runtime |
| ExecutionSigner / ResultCollector | ResultService 내부의 서명 / 수집 역할 |
| BodyService / body builder / custody adapter | BlockService의 내부 역할 |
| ProofArchive / HistoryResolver / ordered delivery / Marshal 역할 | Orderer의 이력 보관·해석·전달 역할. Upstream Marshal trait와는 별개 |
| BodyReady / BlockAvailable | StoredBody / CandidateBlock — 두 단계는 유지 |
| BranchReady / speculative outcome | ExecutionResult |
| CommitApplied / durable commit result | CommitResult |
| OnBlockAvailable / OnCommitApplied | Baton::on_block / on_commit — 로컬 입력 / 선택적 적용 알림 |
| OnOrderedRange / 이전 Baton commit 전달 | Orderer → Executor::commit — Baton 경유 제거 |

</details>

Producer와 validator는 별개의 역할이며 한 노드가 둘 다 수행할 수 있다. Leader의 direction은 producer들에게 전파하고, 해당 실행을 담당하는 validator의 Baton에도 전달되어야 한다. Producer에게만 보내고 모든 executor가 받았다고 가정하지 않는다.

**Native producer-parent header ID와 application input state root는 다르다.** Producer lane의 parent만으로 여러 lane을 합친 실행 state를 결정하지 않는다. Producer block body digest, producer header ID, leader proposal ID, canonical ordered-input ID도 구분한다.

Producer별 prefix가 고정되었어도 여러 lane을 합친 exact 실행 순서는 별도로 확인해야 한다. 그 확인을 마친 연속 입력 구간이 `OrderedRange`이며, 이력의 빈 구간과 순서 settledness를 처리하는 과정은 [§2.7](../e2e/canonical.md#cut-commit--ordered-range--실행-commit)에 설명한다.

Tx를 담는 것은 [producer payload/body](../e2e/block-body.md#block-lifecycle-mempool--propose--body-전파)다. 여러 lane의 순서 근거를 모으는 native leader proposal 자체는 transaction-free이며, Baton policy를 actual proposal context에 연결하는 경합은 [proposal freeze 흐름](../e2e/leader.md#planner-completion과-proposal-freeze의-경합)에서 다룬다.
