# Pre-cut 실행을 위한 Block-STM 모델: Read / Write / Deferred Update

> 갱신일: 2026-09-21  
> 상태: 대화에서 채택한 실행 모델의 설계 기록; 코드 이식·E2E·성능 검증 전  
> 연결: [회전형 block ordering](./rotating-round-robin-dag.md), [논문 개요](./paper-outline.md), [재실행 문헌 조사](./reexecution-reduction-literature.md)

## 1. 이번 결정과 범위

**Block-STM의 transaction 단위 speculative execution·검증·재실행을 사용하고, 합성 가능한 갱신은 `defer(delta)`로 다룬다.** Aptos Aggregators V2를 실행 기법의 직접 참고점으로 사용한다. 새 consensus나 범용 VM을 만드는 결정은 아니다.

- Consensus의 ordering 단위는 **block**이며 block 내부 transaction 순서는 고정한다. 실행·캐시·재실행 단위는 **transaction**이다.
- Producer lane은 기본적으로 state의 독점 owner가 아니다. Shared-state 실행을 기준으로 한다. [State-affinity 배치](./state-affinity-placement.md)는 관련 tx를 같은 lane·가능하면 같은 block에 모으는 선택적 최적화이며 안전성의 전제가 아니다.
- `read / write / defer`는 state의 영구적인 세 종류가 아니라 **transaction의 접근 방식**이다. 한 tx가 같은 key를 읽고 defer할 수도 있으며 두 관측을 모두 추적한다.
- 지원 workload는 signed tx에 주요 object/state와 conservative R/W/typed-Defer 범위를 선언한다. **접근 정보를 얻기 위한 별도 사전 실행은 요구하지 않는다.** 공통 규칙으로 implicit 접근을 보강하고 runtime이 scope/mode containment를 검사한다. 선언 안에서 실제 접근과 조건 분기는 달라질 수 있다. 임의 EVM 전체 지원이나 사전 실행 trace의 완전성을 가정하지 않는다.
- Seer의 instruction trace·분기 예측·VM checkpoint는 필수가 아니다. 일반 계산이 무효화되면 해당 tx를 처음부터 재실행한다.
- 이번 갱신은 execution layer만 다룬다. Ordering quorum, DA 인증, fixed-cut adapter의 wire/safety 규칙이나 execution-signature threshold를 변경·확정하지 않는다.
- 이전 proof/PAC·dual-branch SDK를 되살리지 않는다. 기존 Commonware fork가 아래 모델을 구현했다고 간주하지 않는다.

목표는 **같은 cut의 DA/ordering과 실행 준비를 겹치고, cut 이후 남는 검증·재실행·결과 구성 비용을 줄이는 것**이다. 지연 반영 자체를 state-finality 단축으로 계산하지 않는다.

## 2. AIP-47에서 가져오는 것

[AIP-47: Aggregators V2](https://github.com/aptos-foundation/AIPs/blob/main/aips/aip-47.md)는 학술 논문이 아니라 Aptos의 채택된 기술 제안이다. 원문에서 확인한 핵심은 다음과 같다.

| 기법 | AIP-47의 의미 |
|---|---|
| Aggregator | 보통의 값 덮어쓰기와 증감 연산을 구분해 추적한다. |
| Delayed field | 실행 중 실제 숫자 대신 내부 식별자를 사용하고 output 구성 시 값으로 치환한다. |
| Snapshot | 특정 실행 지점의 값을 나중에 출력에 채울 수 있다. 정확한 값을 제어 흐름에 사용하면 별도 읽기 검증이 필요하다. |
| 조건 검증 | `try_add/try_sub`가 반환한 조건의 성립 범위를 기록한다. 실제 입력에서도 결과가 같으면 재사용하고 달라지면 재실행한다. |
| Block-STM 연결 | 관측·변경을 다중 버전으로 추적하고, 최종 검증 및 materialization을 수행한다. |

내부 delayed ID는 노드마다 달라도 되지만 최종 output에 그대로 노출하지 않는다. 정확한 읽기, 범위 경계와 참/거짓 변화가 있으면 병렬성이 줄거나 재실행이 필요하다. 이 기술은 **가변적인 pre-cut block 집합의 재사용을 자동 해결하지 않는다.**

구현을 읽을 때는 [`captured_reads.rs`](https://github.com/aptos-labs/aptos-core/blob/main/aptos-move/block-executor/src/captured_reads.rs)의 값/조건 관측과 [`versioned_delayed_fields.rs`](https://github.com/aptos-labs/aptos-core/blob/main/aptos-move/mvhashmap/src/versioned_delayed_fields.rs)의 버전·최종 처리 경로를 함께 참고한다. 링크는 이동하는 `main`이므로 실제 이식 시 commit을 고정해야 한다.

아래 절은 이 선행기술을 참고한 **우리 모델의 요구사항·적용 설계**이며, Aptos가 그대로 제공하거나 이미 검증한 기능이라는 뜻이 아니다.

## 3. 실행 의미와 접근 규칙

### 3.1 결과의 기준은 하나의 순차 실행

Finalized cut의 exact block occurrences를 공통 block-order rule로 펼치고, 각 block 안의 고정 tx 순서를 이어 붙인 목록을 reference order로 둔다. Canonical parent, application/runtime 및 fee 규칙 버전도 고정한다.

```text
ReferenceResult = SerialExecute(canonical_parent, ordered_transactions, runtime_rules)
ParallelResult  = ReferenceResult
```

이 등식은 state root만이 아니라 tx별 status, events, gas/fee 결과와 materialized outputs에도 성립해야 한다. 독립 작업의 실제 worker 완료 순서는 달라도 된다.

### 3.2 세 가지 접근

| 접근 | 실행 기록 | 검증·최종 처리 |
|---|---|---|
| `read(key)` | 값과 그 값을 만든 version/provenance | tx 앞의 유효한 `write/defer` 및 tx 내부 선행 갱신을 반영한 값과 검증 |
| `write(key, value)` | 지정 값 또는 삭제; 계산에 사용한 읽기는 별도 기록 | reference order 위치에 적용. Blind write도 다른 write/defer와의 적용 순서는 보존 |
| `defer(key, delta)` | 등록된 연산 종류·변경량·필요한 제약 | 유효한 변경량만 합성하고 canonical output에서 실제 값으로 구체화 |

초기 defer 연산은 **정수 덧셈·뺄셈과 명시적인 범위 조건**으로 제한한다. 임의 함수나 일반적인 `write(x, read(x)+d)`를 개발자의 표시만 보고 defer로 바꾸지 않는다. Runtime이 지원하는 연산과 타입을 강제한다.

예약과 범위 검증은 대체 관계가 아니다. 이미 유효한 예약으로 보장한 경계는 그 근거를 검사하고, 그렇지 않은 조건은 speculative predicate로 기록해 최종 순서에서 검증한다. `defer` 선언이 지불 능력을 증명하지는 않는다.

### 3.3 의존성을 지워도 되는 범위

아래는 같은 key에 대한 접근 관계다. 서로 다른 key의 접근은 다른 숨은 입력·effects가 없다면 독립적이다.

| 조합 | 실행·검증 규칙 |
|---|---|
| Read / Read | 읽기끼리는 충돌하지 않음. 둘 다 올바른 선행 버전을 관측해야 함 |
| Read / Write 또는 Write / Write | reference order를 보존하고 필요한 읽기 검증·적용 순서 관리 |
| Defer / Defer | 연산이 합성 가능하고 각 단계의 제약·관측이 유지될 때 계산을 병렬화. 무조건 conflict-free가 아님 |
| Defer / 정확한 Read | 읽는 위치 이전의 delta를 포함해 값을 계산·검증. 뒤의 delta는 포함하지 않음 |
| Defer / Write·삭제 | 덮어쓰기·삭제 경계를 넘겨 delta를 합산하지 않음. 타입·존재 여부도 검사 |

Conservative block-level DAG는 충돌 가능성을 찾는 요약이다. 이를 block 전체 실행 완료 barrier로 강제하면 fee 같은 key 하나 때문에 모든 tx를 직렬화할 수 있다. **Reference block order는 유지하되 worker는 tx 단위로 추측 실행하고, 실제 의존성과 delta 조건은 Block-STM 검증이 처리한다.**

블록별 D 집합만 같다는 이유로 edge를 없애지 않는다. 같은 block 안에 해당 key의 정확한 읽기·일반 write가 있으면 그 관계도 포함한다. Runtime에서 확인되지 않은 접근 힌트를 안전성 근거로 사용하지 않는다. 실제 내부 dependency graph가 다른 worker 일정 때문에 달라도 최종 reference semantics는 같아야 한다.

## 4. 관측 기록과 재사용 단위

Tx incarnation마다 다음 정보를 보관한다. 아래는 공개 SDK trait가 아닌 개념적 기록 항목이다.

- Stable occurrence identity: block digest와 block 내부 tx 위치. 변하는 dense scheduler index와 분리한다.
- Execution context: parent, candidate generation, order/rule/runtime·fee 버전, tx bytes 및 접근 범위.
- 정확한 읽기: key, 값, version/provenance, 존재·부재 및 지원하는 range 조건.
- Tx 내부의 read/write/삭제/defer/조건 검사/snapshot 사이 **전체 상대 순서**, 또는 같은 의미를 복원하는 동등한 표현. VM instruction trace를 요구하는 것은 아니다.
- Deferred snapshot의 기준 위치: key, tx occurrence와 tx 내부 operation 위치.
- Status/events, gas 결과, application effects와 실패해도 유지되는 protocol fee effects의 구분.

예를 들어 `try_sub(balance, 60)`이 참이었다면 “balance를 읽었다”뿐 아니라 **그 위치에서 60 이상이었다**는 조건을 기록한다. 정확한 값을 다른 계산에도 사용했다면 이 조건만으로 재사용하지 않고 정확한 읽기도 검증한다. 여러 증감·조건이 있으면 전체 tx의 각 prefix에서 관측이 보존되어야 한다.

첫 모델의 일반 read 재사용은 보수적인 version/provenance 검증을 따른다. Predicate-only 재사용은 별도 제한된 의미 최적화다. Arbitrary value-equivalent reuse나 instruction-level repair까지 도입하는 것은 아니다.

Snapshot은 값을 단순히 출력에 보관할 때만 계산과 분리할 수 있다. 실제 숫자를 분기·해시·주소 계산 등에 사용하면 정확한 읽기로 전환한다. Placeholder 치환으로 tx의 다른 계산·가스·크기 제한이 바뀌지 않도록 encoding 규칙을 고정하며, 그 조건을 만족하지 않는 타입은 일반 읽기로 처리한다.

예를 들어 tx 내부 `write(10) → defer(+5) → snapshot → write(20)`은 snapshot=15, 최종값=20이다. 마지막 write와 delta 목록만 따로 저장해서는 이 의미를 복원할 수 없다.

## 5. Pre-cut에서 finalized cut으로

### 5.1 실행과 cut 변경

1. Admission·서명·접근 범위를 가능한 한 먼저 검사하고, 받은 block으로 현재 후보 순서를 구성한다.
2. Block-STM-style worker가 tx를 speculative execute하고 다중 버전의 읽기·쓰기·delta·조건을 기록한다. 결과는 overlay에만 publish한다.
3. Late block, exclusion, parent·anchor·회전 변경 시 후보 generation을 갱신한다. 새 순서의 **직전 writer와 선행 delta 집합**을 다시 찾는다.
4. 선택되지 않은 occurrence의 application/fee 효과를 후보 결과에서 제거한다. 남은 tx의 일반 읽기·조건·snapshot 위치를 검증한다.
5. Exact read 또는 조건 결과가 달라진 tx를 처음부터 재실행한다. 후속 관측도 재검증하지만 모든 후속 tx를 무조건 재실행하지는 않는다.
6. 계산은 유효하고 output-only snapshot 값만 바뀌면 snapshot을 새 위치 기준으로 구체화한다. 그 값의 소비자는 다시 검증한다.

Block-STM 원 모델은 preset transaction order를 전제로 한다. 그러므로 기존 실행기에 블록을 계속 insert/delete하는 것만으로 위 보장이 생기지 않는다. **후보별 버전 공간·generation, stable occurrence mapping, cache import 재검증을 담당하는 adapter**가 필요하다. 안전한 초기 fallback은 새 exact-order 실행 문맥을 만들고 그 문맥에서 검증한 캐시만 가져오는 것이다.

실패한 tx의 delta 제거, `try_*`의 false→true 변화로 생긴 새 delta, conditional no-write, 삭제 후 재생성도 invalidation 원인이다. 이전 incarnation의 늦은 완료는 새 generation에 publish하지 않는다. 알려진 미완료 writer는 unresolved/ESTIMATE로 표시해 소비자의 반복적인 낭비를 줄인다.

### 5.2 Pseudocode — 의미를 보여주는 기준 경로

아래는 최종 검증의 순차 oracle이다. 실제 worker scheduling의 병렬 알고리즘을 구현한 코드가 아니다.

```text
on_candidate_change(candidate, parent):
    generation = next_generation()
    order = flatten_blocks_by_common_rule(candidate)
    context = new_version_context(parent, order, generation)
    seed_only_context_checked_cached_attempts(context)
    execute_and_validate_speculatively(context)

on_finalized_cut(cut, canonical_parent):
    verify_full_ordering_finality(cut)
    obtain_all_selected_block_bodies()
    order = flatten_blocks_by_common_rule(cut)
    prefix = fresh_overlay(canonical_parent)

    for tx in order:
        attempt = cached_attempt(tx.stable_occurrence)
        if not validate_all_observations(attempt, prefix, tx.context):
            attempt = execute_from_start(tx, prefix)
        checked = stage_materialize_and_check(attempt, fork(prefix), tx.position)
        if checked.requires_reexecution:
            attempt = execute_from_start(tx, prefix)
            checked = stage_materialize_and_check(attempt, fork(prefix), tx.position)
        if not checked.valid:
            stop_without_signing_and_report_internal_error()
        append_atomic_application_and_fee_effects(prefix, checked.output)
        record_canonical_status_events_and_gas(checked.output)

    result = compute_canonical_state_and_effects_commitments(prefix)
    sign_result_bound_to_exact_cut_parent_and_rules(result)
```

`validate_all_observations`가 실패하거나 캐시가 없으면 재실행한다. 재실행과 materialization은 tx-local staging에서 이루어지며, 검증된 output을 append하기 전에는 `prefix`를 변경하지 않는다. `stage_materialize_and_check`는 tx의 모든 내부 접근 순서를 재현하고, application abort라면 그 effects를 제거한 뒤 결정된 fee effects만 유지한다. Application 실패 결과도 이 검사가 유효하면 정상적인 canonical output이다.

로컬 자원 제한·데이터 누락은 tx의 application failure로 바꾸지 않는다. 캐시에서 조건 오류가 드러나면 staging을 버리고 재실행한다. 이미 고정된 올바른 prefix에서 새 순차 실행까지 내부 검사를 통과하지 못하면 무한 retry하거나 잘못된 root를 서명하지 않고 중단·진단한다.

최적화된 병렬 경로는 이 oracle과 같은 결과를 내야 한다. Prefix 검증·delta 합성 자체의 비용은 남으며 이를 0이라고 주장하지 않는다.

### 5.3 결과 인증과 물리 반영

최초 모델은 **모든 deferred 값을 materialize한 state root와 tx outputs**를 실행 결과 서명 대상으로 한다. 내부 delayed ID, speculative reservation, 해결되지 않은 조건이 남은 결과에는 서명하지 않는다. 정확한 cut·canonical parent·규칙과 전체 ordering-finality evidence를 요구하는 기존 인증 경계를 유지한다.

디스크 apply를 나중에 하는 것은 가능하지만 result certification과 read readiness는 별도다. 미구체화 delta 자체를 canonical state commitment로 삼는 별도 저장 모델은 이번 결정에 포함하지 않는다.

### 5.4 Block에 담기 전의 state-affinity 배치

[배치 설계](./state-affinity-placement.md) v3는 signed tx의 선언, 공통 설정과 **배치 목표 slot q**로 producer 후보 순서를 계산한다. State의 고정 논리 위치를 q의 lane priority에 대응시켜 실제 producer를 회전시킨다. 로컬 mempool·부하·현재 state의 사전 실행 결과·아직 미확정인 cut은 배치 입력이 아니다. Producer가 미포함을 결정하면 다음 후보로 전달하고, 원본을 보관한 정상 sender/relay는 H finalized cuts 뒤 모든 후보에 재전파한다. State ownership이나 새 quorum을 요구하지 않는 soft preference다.

`tx1: D(A), D(B), W(C)`와 `tx2: D(A), R(C), R/W(E)`는 설정에 따라 같은 producer를 우선할 수 있으나 항상 함께 배치된다고 보장하지 않는다. 실제로 같은 block에 모이면 관련 body·고정 내부 순서와 unresolved/ESTIMATE 처리가 reader의 낭비를 줄일 수 있다. D–D의 낮은 배치 가중치는 범위·predicate 검증 생략을 뜻하지 않는다.

최종 block 순서는 실제 producer output과 **실제 포함 slot k**의 공통 ordering rule에서만 정한다. q≠k가 가능하며 전체 rank는 상대 block 높이, k의 lane priority, block 내부 index를 따른다. 알려진 선행 writer의 결과를 필요로 하는 reader만 기다리고 독립 작업은 실행한다. 회전 자체가 충돌이나 재실행을 없애는 것은 아니다.

Nonce·기존 admission이 우선한다. 전달 기록은 이전 in-flight block을 취소하지 않으며, 권장 producer가 아니어도 기존 유효 block을 배치 규칙만으로 거부하지 않는다. 중복 selected occurrences는 기존 replay/status/fee 규칙을 따른다. 실제 배치가 달라지면 canonical order도 달라질 수 있다. **같은 exact cut에 대해서는** 기존 순차 oracle과 일치해야 한다. Slot/anchor/parent 변경은 새 generation에서 검증하며, 설정/선언/권장 lane 일치만으로 cache를 재사용하지 않는다.

선언 범위 밖 접근은 해당 state 접근을 수행하기 직전에 차단하고 해당 시도의 staged application effects를 버린다. Pre-cut 위반은 후보 결과이며, 관측 재검증·재실행 뒤 canonical context에서도 위반한 경우에만 최종 `AccessViolation`과 기존 fee 규칙을 적용한다. 전달·재실행으로 선언을 넓히지 않는다. 제거한 것은 profiling pass이며 block 수신 이후의 pre-cut execution이 아니다.

## 6. 가스·잔액과 DoS 경계

수수료 **지불 계정 차감**과 **수수료 총액 집계**를 분리한다.

- Fee total에 더하는 변경은 실행 흐름이 그 즉시 값을 읽지 않는다면 defer의 좋은 첫 적용 대상이다. 정수 overflow 등 경계는 여전히 검사한다.
- Payer 잔액은 부족할 수 있다. 예약·지불 능력·nonce와 fee rules를 검증해야 하며 “최종 합산하면 된다”로 바꾸지 않는다.
- Sui [SIP-58](https://github.com/sui-foundation/sips/blob/main/sips/sip-58.md#transaction-format)은 최대 유출량 reservation과 실행 전 scheduler의 underflow 방지를 사용한다. Aptos-style speculative predicate 검증과 같은 프로토콜은 아니다.
- 우리 pre-cut에서는 예약 역시 해당 candidate에 상대적이다. 같은 canonical 돈을 여러 후보/lane에서 독립적으로 확정 예약했다고 취급하지 않는다. 초기 모델은 정본 payer 검사를 유지하고, 일반 잔액의 deferred debit은 admission·예약 의미를 명세한 경우에만 확장한다.
- Application abort에서는 그 tx의 application writes/deltas를 버리되, 정해진 fee 규칙에 따라 유지할 gas/fee effects는 별도 적용한다. 입력 거부, 유료 runtime failure, speculative retry를 구분한다.
- 실제 사용자 fee는 정본 실행의 결정적 규칙으로 계산한다. 노드별 실행·재시도 횟수에 따라 다른 요금을 부과하지 않는다.
- 미선택 작업과 반복 retry 비용은 일반 실패 가스로 회수된다고 보장할 수 없다. Speculative CPU/attempt·overlay·delta/snapshot 보관량을 제한하고, 한도를 넘은 작업은 finalized-order 처리로 넘긴다. Cut 및 정본 state progress에 필요한 자원을 따로 확보한다.

새 Computing Gas 모델이나 무료 사전 실행의 무제한 허용을 도입하는 결정은 아니다.

## 7. 작은 예시와 반드시 보존할 의미

### A. 공통 수수료 카운터

초기 `fee_total=100`, T1의 fee delta가 `+3`, T2가 `+5`이고 두 계산 모두 total 값을 읽지 않는다고 하자. 연산·범위가 유효하면 fee 때문에 둘을 직렬 실행할 필요는 없다. 최종 값은 108이다. Cut이 T1만 선택하면 103이며 T2 delta를 섞지 않는다. 가스 산출에 사용한 다른 읽기가 바뀌면 delta도 다시 계산해야 한다.

### B. 합계가 맞아도 조건이 달라지는 경우

초기 `balance=100`, 순서 T1→T2, 각각 `try_sub(70)`과 `try_sub(60)`이다. T1 성공 뒤 잔액은 30이므로 T2는 false다. Cut이 T1을 제외하면 T2는 true가 되고 잔액은 40이다. **False였던 tx도 재검증 대상이며 새 delta가 생길 수 있다.**

최종 순서가 고정된 뒤에도 `balance=50`, `try_sub(70)` 다음 `add(60)`은 단순히 `50-70+60`으로 계산할 수 없다. 첫 조건은 실패하므로 debit이 발생하지 않는다. 해당 tx가 실패 시 다른 효과 없이 종료한다는 예제 의미에서는 최종 값이 110이다.

### C. Snapshot은 최종 총액이 아니다

초기 카운터 100, T1이 `+3` 후 snapshot을 output에 보관하고 T2가 `+5` 후 snapshot을 보관하면 출력 값은 각각 103, 108이다. 둘 모두에 마지막 값 108을 넣으면 틀리다. T1이 제외되면 T2 snapshot은 105로 다시 구성한다. Snapshot이 제어 흐름에 쓰였다면 output patch만으로 끝내지 않는다.

### D. 덮어쓰기와 정확한 읽기

`x=100`, 순서가 `defer(+3) → write(10) → defer(+5)`이면 마지막 x는 15다. 세 변경을 한 번에 초기 값에 더할 수 없다. 첫 defer 뒤의 reader는 103, write 뒤의 reader는 10을 보아야 하며, 값에 따라 결정한 결과가 달라지면 재실행한다.

## 8. 검증과 실험

### 8.1 안전성 acceptance criteria

같은 parent·exact cut·block/tx order·runtime으로 실행한 순차 oracle과 최종 root뿐 아니라 status/events/gas/모든 outputs가 같아야 한다. 다음 사례를 property tests 및 adversarial traces에 포함한다.

1. 독립 R/W, 동일 key 순수 delta, read/write/defer 혼합 및 tx 내부 여러 접근.
2. Late lower-rank writer/delta 삽입과 selected/unselected predecessor 교체.
3. Parent 변경, slot 회전, 다른 branch의 동일 높이 block, 중복 occurrence 처리.
4. Bound 근처에서 조건 true→false 및 false→true; tx 내부 중간 prefix의 overflow/underflow.
5. 같은 최종 숫자라도 중간 predicate·snapshot·events가 달라지는 순서.
6. Application abort 뒤 delta 제거와 실패해도 유지되는 fee effects.
7. Snapshot-only output 재구성과 snapshot 값을 읽어 분기하는 tx의 재실행.
8. 일반 write·삭제·재생성, 부재 읽기 및 지원 범위 내 range 의존성.
9. Worker 완료 순서와 내부 delayed IDs가 달라도 같은 canonical outputs.
10. 잘못된 defer 선언, stale generation의 늦은 완료, 잘못된 parent/cut의 캐시·서명 거부.
11. 자원 한도 도달 후 fallback이 tx 성공·실패 의미를 바꾸지 않음.
12. 선언 scope/mode containment, implicit nonce/fee, root/subkey 범위, pre-cut 접근 위반 뒤 canonical 분기 변경과 최종 status/fee 일치.

### 8.2 비교군과 지표

동일한 transaction 의미와 fee 규칙을 사용한다. Native coin/account 표현 변경으로 성공률이 달라지는 실험은 별도다.

| 비교군 | 분리하려는 효과 |
|---|---|
| Post-cut plain Block-STM | 추측 실행 overlap 없는 기준 |
| Post-cut Block-STM + deferred updates | 합산 최적화 자체의 효과 |
| Pre-cut plain Block-STM + exact-cut cache validation | DA/ordering과 실행 overlap 효과 |
| Pre-cut Block-STM + deferred updates + exact-cut validation | 이번 모델의 결합 효과 |
| Pre-cut full replay | 캐시 재사용의 이득과 비용 |

추가 ablation은 predicate 재사용, snapshot patch, dirty 작업 병합, speculation budget이다. 기존 RTT × application operation count 축에 defer 비율, 정확한 read 빈도, 공유 fee payer, 경계값 근접도, cut churn을 추가한다.

배치 ablation은 hash routing, 고정 physical affinity, cut별 회전 affinity를 동일 실행기에서 비교하고, 동점 규칙·같은 block packing·알려진 writer의 scheduling 효과를 분리한다. Packing 대기·과대 선언·전달/fanout 비용·lane 편중·nonce/중복 처리와 late predecessor 원인의 재실행을 함께 측정한다. Cut 내부와 경계의 invalidation, target q와 inclusion k의 차이를 기록한다. 같은 확정 trace의 cache 비교와 배치를 바꾸는 E2E 비교는 구분한다. 별도 profiling 실행은 기본 경로가 아닌 비교군이다.

Cut→certified state, 제출→certified state, durable readiness p50/p95/p99를 분리한다. 재실행 CPU, 재검증·predicate 검사, materialization·root 계산, signature 수집, 메모리, ordering latency와 goodput을 모두 보고한다. Logical defer operations와 최종 물리 write 수는 같지 않으므로 별도 집계한다. Application failure와 실행기 retry를 실패율 하나로 합치지 않는다.

## 9. 논문에서의 위치와 남은 결정

Block-STM, aggregators와 deferred materialization을 새 발명으로 주장하지 않는다. 우리의 기여 후보는 **Autobahn-family의 불완전한 multi-producer 입력을 DA/ordering과 함께 실행하고, 확정 cut에 맞춰 계산·조건·지연 출력을 안전하게 재사용·보정하여 state-finalization 지연을 줄이는 경계와 그 효과**다.

남은 구현 결정은 대상 Block-STM 코드/버전, access schema와 초기 application, fee admission·예약 규칙, deferred 타입/encoding, 메모리·재시도 한도다. 이번 문서는 이 항목들이 구현되었다고 주장하지 않는다. 합의 adapter와 인증 정족수는 별도 명세 대상이며 실행 접근 분류로 정당화되지 않는다.

### 출처

- [Block-STM, PPoPP 2023](https://arxiv.org/html/2203.06871v3): preset-order execution, 다중 버전 읽기 검증과 tx 재실행의 기반.
- [AIP-47: Aggregators V2](https://github.com/aptos-foundation/AIPs/blob/main/aips/aip-47.md): 관련 기술 제안 및 구현 링크. 위 §2가 원문 요약이며 이후는 우리 적용 설계.
- [Aptos Labs: Aggregators](https://medium.com/aptoslabs/aggregators-how-sequential-workloads-are-executed-in-parallel-on-the-aptos-blockchain-e7992c70cefb): 공통 supply counter와 합산 연산의 동기.
- [SIP-58: Sui Address Balances](https://github.com/sui-foundation/sips/blob/main/sips/sip-58.md): reservation 기반 scheduling과 accumulator settlement의 비교점.
