# Cut별 ordering에 맞춘 state 기반 producer 배치

> **2026-09-23 문서 경계:** 이 파일과 실행 모델은 이전 v3 soft-routing 명세다. 최신 영문 draft의 [Section 4](./research/paper/sections/04-placement.tex)는 greedy grouping과 DA ACK 이전 hard placement 검사를 제안한다. 해당 변경은 이 계산 모델이나 consensus에 아직 구현되지 않았다. 아래 자유로운 fallback/fanout을 새 hard-placement의 중복 방지·liveness 근거로 읽지 않는다. 새 배치 활성화와 기존 certified block·pending tx의 권한 이전은 draft의 D4/P3 미해결 항목이다.

> 갱신일: 2026-09-21  
> 상태: v3 연구 명세; 배치 계산의 실행 가능한 모델 포함, consensus/Block-STM 통합·E2E·성능 검증 전  
> 실행 기준: [Block-STM R/W/Defer](./blockstm-execution-model.md), [회전형 ordering](./rotating-round-robin-dag.md)  
> 논문: [paper-outline.md](./paper-outline.md)  
> 이력: [v2 고정 배치](./state-affinity-placement-v2.md), [v1 batch-local 배치](./state-affinity-placement-v1.md)

## 1. 결정과 범위

**Transaction에 선언된 state 접근을 이용해 관련 tx를 모으되, 해당 ordering slot의 lane 우선순위에 맞춰 선호 producer를 회전시킨다.** 같은 state의 논리적 우선순위 위치는 유지하고 그 위치를 담당하는 실제 producer가 달라진다. State ownership·데이터 저장 위치를 옮기는 sharding이 아니다.

- Signed tx의 주요 object/state와 `read/write/typed-defer` 선언을 사용한다. 배치용 사전 실행은 하지 않는다.
- 각 occurrence에는 tx 전체가 포함되며 여러 lane으로 분할하지 않는다. 동일 signed tx의 중복 occurrences는 생길 수 있다. Multi-state tx도 한 producer 후보 목록을 가진다.
- **배치는 soft preference다.** 권장 producer가 아닌 곳의 포함을 이유로 기존에 유효한 block을 거부하지 않는다. 실제 producer의 독점 포함 권한이나 inclusion certificate를 추가하지 않는다.
- 기존 DA/ordering 확정 절차와 정족수는 변경하지 않는다. 배치·전달·실행 완료를 ordering vote의 선행조건으로 만들지 않는다.
- Block 수신 이후 pre-cut Block-STM 실행은 유지한다. 최종 결과는 실제 cut, canonical parent, runtime/order/fee 규칙으로만 정한다.
- 초기 명세는 고정 lane 집합·고정 설정·고정 application schema를 사용하는 한 실험 epoch다. 실행 중 membership/schema/seed 변경은 지원하지 않는다. 이는 기존 proof/PAC baseline이나 Commonware fork를 교체한 구현이 아니다.

스펙의 완료 범위는 배치 함수, forwarding/fallback, cut 경계 처리와 실행기 연결의 의미다. 네트워크 codec·암호 구현, application별 fee/replay 세부 정책, consensus adapter와 실행 엔진 이식은 별도 구현 작업이다.

## 2. 입력과 두 종류의 slot

### 2.1 공통 설정과 접근 선언

설정은 genesis 또는 이미 확정된 configuration 경로에서 읽는다. 같은 실험 epoch 동안 불변이다.

| 입력 | 의미 |
|---|---|
| `config_digest` | chain/domain, epoch, lane 목록, schema/runtime 버전, seed, 점수·전달 규칙을 묶는 설정 식별자 |
| `lanes = [L0, …, L(m−1)]` | 중복 없는 고정 canonical producer 목록; `m >= 1` |
| `position(scope)` | scope를 `0..m−1`의 고정 논리 위치에 대응시키는 함수 |
| `H` | 미확정 tx를 모든 producer에게 재전파하기까지의 finalized-cut 수; 초기값 `H=m`, 양의 정수 |
| 입력·전송 한도 | tx bytes, 정규화 scope 수, peer queue, pending bytes와 재전송 budget; 실험 설정으로 고정·기록 |

`AllowedAccess = Normalize(SignedDeclaredAccess ∪ ProtocolDerivedAccess)`다. Nonce/replay, fee payer, fee 집계 등 implicit 접근도 빠뜨리지 않는다. `ProtocolDerivedAccess`는 signed tx와 고정 schema만 사용하며, producer·slot·로컬 state 값에 따라 달라지면 안 된다. Producer-dependent fee collector 같은 실제 실행 접근을 정적으로 확장할 수 없다면 허용 범위를 보수적으로 선언하거나 해당 application을 초기 workload에서 제외한다.

Scope 식별자는 application/schema와 canonical object/state ID를 포함한다. 초기 배치 단위는 schema가 정한 **서로 구분되는 canonical object/root**다. 같은 root의 세부 필드와 중복 항목은 하나로 합쳐 점수를 계산하고, runtime 권한은 별도의 정확한 허용 범위를 유지한다. 임의 wildcard/range의 무제한 전개는 지원하지 않는다. 등록된 tx-local fresh-ID 생성 범위는 허용할 수 있지만 임의 undeclared write 권한은 아니다.

접근 선언은 권한이나 성공 증명이 아니다. 실제 접근이 scope와 mode를 벗어나기 **직전** runtime이 해당 실행 시도를 중단하고 staged application effects를 폐기한다. Pre-cut 위반도 후보 결과이므로 최종 순서에서 입력이 바뀌면 재검증한다. Canonical context에서도 위반하면 기존 failure/fee 규칙의 `AccessViolation`이다. 전달·재실행으로 선언을 확대하지 않는다.

### 2.2 배치 목표 `q`와 실제 포함 `k`

- `h`: 이 노드가 ordering-finality 증거와 필요한 ordering metadata를 검증한 **연속 finalized ordering prefix**의 마지막 slot. 더 높은 slot의 certificate 하나만 보고 gap을 뛰어넘지 않는다. 선택된 block body 복구, tx 포함 확인, execution/state 준비는 기다리지 않는다.
- `q=h+1`: 새 routing attempt의 목표 slot. 같은 tx/config/**q**에 대해 후보 순서가 결정적이다.
- `k`: 해당 block occurrence가 처음 canonical ordered input으로 들어간 실제 slot. `q=k`는 보장하지 않는다.

`q`는 전달 힌트이지 cut membership·실행 위치 예약이 아니다. 노드가 서로 다른 finalized prefix까지 동기화되어 있으면 다른 q를 사용하는 것이 정상이다. 같은 q에서도 실제 mempool과 admission이 다르므로 block contents까지 같아지는 것은 아니다.

배치에는 아직 미확정인 `C_q`, candidate tips, cumulative ordering boundary, parent state, 현재 queue length를 넣지 않는다. 따라서 cut 결정을 기다려야 배치할 수 있는 순환 의존이 없다. Parallel slots가 열려 있어도 최초 정책은 다음 연속 slot을 목표로 잡는 단순한 hint를 사용하며 consensus가 다음 slots를 진행하는 것을 막지 않는다.

## 3. Cut별 state→lane 매핑

### 3.1 회전 함수

Slot 번호는 1부터 시작하고 view change나 wall-clock으로 회전하지 않는다.

```text
rotation(q)             = (q - 1) mod m
lane_at_priority(q, j)  = lanes[(j + rotation(q)) mod m]
priority_q(lanes[i])    = (i - rotation(q)) mod m
preferred_lane(s, q)    = lane_at_priority(q, position(s))
```

`position(s)`는 설정의 명시적 scope→position 표를 먼저 사용하고, 없는 scope는 `H_scope(seed, canonical_scope) mod m`로 정한다. 새 slot마다 seed를 바꾸지 않는다. 표·seed는 leader의 임의 선택이 아니다.

초기 연구 hash profile은 domain-separated SHA-256이다. 각 field는 `u32be(byte_length) || canonical_bytes`로 인코딩하고 domain도 첫 field로 넣는다. Scope hash는 `("scope-v3", seed, scope)`다. Hash 전체를 unsigned big-endian 정수로 해석한다. 예제 실행 모델의 strings는 canonical UTF-8 fixture ID이며 production adapter는 chain의 canonical ID bytes와 동일한 field encoding을 사용해야 한다.

### 3.2 Multi-state tx의 후보 목록

정규화된 scope 하나의 배치 가중치는 다음과 같다.

- `R`, `W`, `R+W`: **1**. 같은 scope를 여러 번 적거나 R+W라고 2점으로 세지 않는다.
- 조건 관측이 있는 defer 또는 순수 합성 가능성이 정적으로 보장되지 않는 등록된 defer: **1**.
- 등록된 schema가 배치상 순수 합성 대상으로 분류한 D-only: **0**. 실제 범위·predicate 검증 비용이 0이라는 뜻은 아니다.

Defer 분류는 고정 타입/profile로 정하며 실제 실행 결과를 보고 바꾸지 않는다. D로 정확한 값을 읽어 분기·주소 계산을 한다면 필요한 R도 선언해야 한다.

```text
rank_producers(tx, config, q):
    access = normalize_declared_and_protocol_access(tx, config.schema)
    scores[0..m-1] = 0
    for each unique scope in access:
        scores[position(scope)] += weight(merged_modes(scope))
    if every score is zero:
        positions = sort j by (H_zero(seed, tx_id, uint64be(j)), j)
    else:
        positions = sort j by (-scores[j], j)
    return [lane_at_priority(q, j) for j in positions]
```

`H_zero`의 domain은 `"zero-v3"`다. Zero-score fallback도 **논리 위치**를 먼저 정한 뒤 회전한다. 물리 lane ID를 hash에 넣으면 전체 후보 목록의 회전 성질이 깨진다. Hash 동률은 j로 해소하고 점수 계산은 검사된 정수 연산을 사용한다. 정규화 scope 수의 상한 때문에 점수의 최대값도 bounded다.

Producer가 이 목록의 첫 후보를 우선하지만, block 용량·nonce·application admission과 기존 packing 규칙이 우선한다. 같은 lane에 배치해도 같은 block 또는 연속 tx 위치까지 보장하지 않는다. Pending pool에서 모든 tx를 전역적으로 모으거나 같은 state의 모든 tx를 기다리는 barrier는 두지 않는다.

### 3.3 사용자 예시

`position(C)=0`, `position(E)=1`, A/B는 순수 D라고 하자. 여기서는 application 접근만 표시하며 실제 점수에는 implicit 접근도 포함한다.

| Tx | 논리 위치 0/1/2 점수 | q=1: L0,L1,L2 | q=2: L1,L2,L0 | q=3: L2,L0,L1 |
|---|---|---|---|---|
| tx1: D(A), D(B), W(C) | 1 / 0 / 0 | L0 우선 | L1 우선 | L2 우선 |
| tx2: D(A), R(C), R/W(E) | 1 / 1 / 0 | L0 우선 | L1 우선 | L2 우선 |

두 tx는 같은 논리 위치를 선호하며 producer만 회전한다. 더 많은 다른 scope나 implicit 접근이 추가되면 선택이 달라질 수 있다. **모든 연결된 multi-state tx를 한 lane에 모으는 알고리즘은 아니다.**

## 4. 전달·침묵·미포함 tx의 수명

### 4.1 불변 tx와 routing metadata

Application tx identity는 원본 signed payload·nonce·접근 선언으로 정한다. 재배치 시 원본 bytes와 tx ID는 바꾸지 않는다. 전달은 tx 외부의 metadata로 표현한다.

- 제출자 서명의 routing intent: `(domain, tx_id, config_digest, start_finalized_slot, start_finality_digest)`. 고정 application schema가 해당 tx의 제출 권한자로 인정하는 signer의 서명을 검사한다. 시작 anchor는 genesis 또는 검증 가능한 finalized prefix다.
- Attempt: `(intent_digest, q, basis_finality_digest)`. Basis의 연속 prefix 끝이 h이면 q=h+1이다. 동일 intent/q/basis는 동일 attempt다.
- `Pass`: `(attempt_digest, candidate_index, from, to)`에 현재 후보 producer가 서명한다. 해당 attempt의 목록에서 다음 index로만 전달하며 tx와 intent를 함께 전송한다.

`start_finality_digest`와 `basis_finality_digest`는 인증서의 임의 signer subset/인코딩이 아니라 **canonical cut/prefix 내용의 identity**다. 이를 입증하는 full native finality evidence는 별도로 검증한다. 동일 finalized 내용에 다른 유효 인증서가 붙었다고 새 attempt가 되지 않는다.

Intent는 application 실행 권한을 추가하지 않고 cut 포함을 보장하지 않는다. Intent를 재작성해도 tx ID가 달라지지 않는다. 노드는 tx ID별로 가장 이른 **유효하게 서명·검증된** 시작 anchor를 보존하고 뒤의 intent·Pass로 pending age를 초기화하지 않는다. 이미 처리한 tx의 새 intent는 재실행 권한이 아니다. 오래된 anchor를 선택해 재전파를 촉진하는 행위도 bounded traffic만 만들도록 rate limit한다.

Pass는 빠른 전달/관측 기록이지 admission certificate가 아니다. 새 attempt에는 새 q의 목록을 사용하고 예전 Pass를 재사용하지 않는다. 서명·from/to·index가 틀린 Pass는 버리지만 유효한 원본 tx를 영구 실패시키지 않는다. Producer는 Pass를 수신하지 않아도 직접 수신·fallback으로 받은 tx를 포함할 수 있다.

### 4.2 정상·실패 경로

1. 제출자/relay는 intent와 검증 가능한 anchor를 보관하고, q의 첫 후보에게 원본 tx를 보낸다.
2. Producer는 정적 검사를 통과한 tx를 include하거나, 이번에 포함하지 않기로 하면 다음 후보에게 원본+Pass를 전달한다. 거짓 서명·잘못된 형식처럼 영구적인 입력 오류는 전달하지 않는다.
3. 같은 attempt 내 후보 index는 증가한다. 마지막 후보도 포함하지 않기로 하면 outgoing Pass 없이 순회를 끝내고 다음 finalized-prefix event를 기다린다. 루프를 돌지 않는다.
4. h가 전진하면 아직 canonical ordered occurrence가 확인되지 않은 tx는 새 q=h+1로 재배치한다. 새 목록의 첫 후보부터 시작한다. 로컬 부하로 순위 자체를 바꾸지 않는다.
5. `h - start_slot >= H`이면 다음 preferred 후보만 기다리지 않고 **모든 eligible producers에 원본을 재전파**한다. 초기 H=m이다. Prefix를 여러 cuts 건너뛰어 복구해도 현재 h로 나이를 계산하므로 fallback이 생략되지 않는다.

Fallback은 전달 fanout일 뿐 새로운 vote/handshake가 아니다. 각 노드는 `(tx_id, destination, h)` 기준으로 중복 전송을 억제하고 per-peer/전체 budget을 적용한다. 이후 finalized-prefix 전진마다 미확정 tx의 재전송을 재평가하며, 같은 h에서 로컬 timer로 같은 목적지에 재전송하는 것은 허용한다. Timer가 slot·회전·canonical expiry를 결정하지는 않는다.

Dedup은 같은 논리 전송의 중복 생성을 막으며 transport retry를 금지하지 않는다. Budget 때문에 아직 enqueue하지 못한 목적지는 미전송 pending으로 유지하고 cut 전진·restart 이후에도 공정하게 처리한다. 매 cut마다 목록 앞쪽만 보내고 나머지를 버리거나, enqueue 전에 전송 완료로 표시하지 않는다. 이 fair draining 없이 모든 정상 producer에 전달된다고 주장하지 않는다.

정상 제출자 또는 하나 이상의 정상 relay가 원본과 시작 anchor를 보관해야 한다. 모든 사본을 Byzantine producer 하나에만 넘기고 버렸다면 복구를 보장할 수 없다. Pending 저장이 가득 차면 ingress backpressure/재시도 응답을 사용한다. 최소 한 사본이 보관된다는 조건을 확인하지 않은 silent eviction에 liveness 보장을 붙이지 않는다. Crash 이후 동일 anchor·tx ID·전송 이력을 복구하거나 제출자가 원본을 재전송한다.

### 4.3 포함되었다는 주장과 실제 확정

| 관측 | 처리 |
|---|---|
| Producer의 수신 ACK 또는 "포함했다"는 주장 | canonical 종료 근거가 아님. Fallback age를 초기화하지 않음 |
| 유효한 block body에 포함되어 있으나 미확정 | block occurrence를 추적. 이미 만든 block을 수정하지 않으며 canonical 포함 전 fallback은 유지 |
| Finalized prefix에 정확한 tx occurrence 포함 | 새 routing을 종료. 실행 status·fee는 canonical 실행 결과로 판단 |
| Cut에 미선택된 기존 block | 기존 consensus의 later selection 대상일 수 있음. block의 lane/bytes/identity를 바꾸지 않음 |
| 기존 block과 재전파된 복사본이 모두 선택됨 | 각 occurrence를 canonical 순서의 기존 replay/nonce/status/fee 규칙으로 처리 |

**재전파는 이미 발행한 block을 다른 lane으로 옮기거나 취소하는 행위가 아니다.** 이전 producer가 늦게 포함해 중복이 생길 수 있다. 검증된 in-flight 포함이 없어야만 재전송할 수 있다고 요구하면 withholding에 막히므로 exclusivity를 약속하지 않는다. Canonical replay protection은 필수 application 전제이며, 독립 occurrence에 수수료가 한 번만 부과된다고 별도 약속하지 않는다.

Routing에는 자동 application expiry를 추가하지 않는다. 기존 tx가 자체 expiry를 가지면 실제 canonical 위치에서 기존 runtime 규칙으로 처리한다. 로컬 보관 기간 만료는 네트워크 어디에도 tx가 없다는 증거나 canonical cancel이 아니다. 최초 실험에는 epoch 재구성 중 새 intent를 생성하지 않으며, 다음 epoch로의 tx 이월 정책은 이 고정-membership 명세 범위 밖이다.

### 4.4 Pseudocode — 전송과 실행 연결

```text
on_submit(signed_tx, signed_intent):
    check_static_format_signature_access_bounds_and_intent()
    verify_start_anchor_and_sync_contiguous_ordering_prefix()
    retain_by_tx_id_without_resetting_earliest_anchor()
    dispatch_pending()

dispatch_pending():
    h = latest_verified_contiguous_finalized_slot()
    for retained tx without a verified canonical occurrence:
        q = h + 1
        route = rank_producers(tx, config, q)
        destinations = all_lanes if h - tx.start_slot >= H else [route[0]]
        send_original_with_attempt_under_dedup_and_transport_budgets(destinations)

on_valid_pass(attempt, index):
    check_same_attempt_and_exact_from_to_signature()
    send_to_next_candidate_if_any_without_waiting_for_votes()

on_finalized_prefix_advance(prefix):
    verify_native_finality_and_fill_slot_gaps()
    advance_h_from_ordering_metadata_without_waiting_for_bodies_or_execution()
    stop_routing_only_for_occurrences_already_verified_in_that_prefix()
    dispatch_pending()
    schedule_missing_body_fetch_and_execution_notification_in_background()

on_received_block(block):
    validate_native_block_and_signed_transactions()
    keep_immutable_block_and_occurrence_identity()
    update_candidate_generation_and_speculatively_execute()
```

전체 tx의 제출 시각이 아니라 실제로 선택된 block 순서가 정본 실행을 결정한다.

Body가 없어 정확한 포함을 확인하지 못한 tx는 pending으로 유지한다. Fetch 결과로 포함을 확인하면 전달을 멈추되 h나 다른 tx의 fallback은 그 fetch를 기다리지 않는다.

## 5. Block ordering과 실행의 연결

실제 slot k에 선택된 block b의 실행 순서는 기존 회전 규칙을 사용한다.

```text
rank_k(b) = (height(b) - cumulative_anchor_k(lane(b)), priority_k(lane(b)))
tx_order  = (rank_k(block), fixed_index_within_block)
```

`cumulative_anchor_k`는 이전 ordering slots에 이미 canonical input으로 배정된 경계이지 worker 실행 완료 높이가 아니다. Rank 계산 전 native already-ordered filtering, 인증된 lane path와 exact block identity를 검증한다. 같은 lane/height의 다른 branch를 같은 occurrence로 취급하지 않는다.

Priority는 **상대 block 높이가 같을 때의** 비교다. L0가 최우선이어도 L1의 relative-height 1 block은 L0의 relative-height 2 block보다 앞선다. 배치 함수는 미래 producer queue·block height를 모르므로 최우선 후보가 가장 빠른 실행 위치를 보장하지 않는다.

q가 아닌 k에서 포함되면 k의 priority·누적 anchor·canonical parent로 처리한다. 미확정 선행 slot이 있을 때의 anchor/parent는 잠정값이며 확정 뒤 새 execution generation을 만든다. 이전 generation의 늦은 worker 완료를 새 overlay에 publish하지 않는다.

실행기 규칙:

1. 수신한 block의 선언된 R/W/D와 **전체 rank**로 알려진 선행 의존성을 찾는다.
2. Reader가 필요로 하는 알려진 선행 writer 또는 deferred delta가 미완료이면 해당 reader의 의존성을 대기시킨다. 배치 점수 0인 D도 뒤따르는 정확한 read의 입력이다. 독립 tx는 계속 실행하며 block 전체·모든 lane의 barrier는 만들지 않는다.
3. 아직 오지 않은 block의 완전성은 가정하지 않는다. 수신한 입력만으로 진행한 부분은 speculative로 유지한다.
4. Late writer, cut 제외, parent/anchor/slot 변경 시 actual read provenance, 존재·부재·range, defer predicate와 snapshot을 검증한다. 달라진 tx는 재실행하고 입력이 유지된 계산은 재사용한다.
5. Deferred 값을 materialize하고 exact cut/parent 결과만 기존 결과 인증 조건에 넘긴다. Routing intent나 같은 producer 배치는 cache 재사용의 증명이 아니다.

같은 lane에 모으는 것은 관련 body와 block 내부 순서를 일찍 함께 얻기 위한 수단이다. Declaration-aware waiting은 기본 Block-STM에 무조건 제공된다고 가정하지 않고, 이 adapter에 추가·평가하는 scheduling policy로 둔다.

## 6. 성질·한계·공격

### 6.1 결정성과 회전의 성질

같은 signed tx, 정규화 schema, config와 q는 같은 후보 목록을 얻는다. 실제 block inclusion, worker schedule, 완료 시각까지 같아지는 것은 아니다.

고정 논리 위치 j를 slot q의 물리 lane으로 옮기는 순열을 P_q라고 하면 후보 목록 전체가 같은 순열로 회전한다.

```text
Route(tx,q) = P_q(Route(tx,1))
priority_q(preferred_lane(scope,q)) = position(scope)
```

따라서 같은 workload에 하나의 공통 순열만 적용했다면 primary 동거 관계와 cross-lane dependency 수는 변하지 않는다. **회전 자체가 state conflict를 줄이는 것은 아니다.** 고정 physical affinity에서 tie-break만 회전시키는 비교군에는 이 동거 불변성을 그대로 적용하지 않는다.

m slots를 한 바퀴 돌면 같은 논리 위치의 primary 역할을 각 producer가 한 번씩 담당한다. 그러나 workload의 시간 변화·block 용량·fallback이 있는 실제 부하 균등성, state 간 순서 공정성이나 MEV 방지는 보장하지 않는다. State의 priority 위치는 고정된다.

Multi-key tx에서 동점이 많으면 작은 논리 위치를 선호하는 편중이 생길 수 있다. 물리 producer를 교대해도 해당 cut의 hot lane이 사라지지는 않는다. 같은 state의 tx라도 서로 다른 q로 배치되면 다른 물리 lane으로 가므로 cut 경계의 동거·재사용은 위 불변성의 대상이 아니다.

### 6.2 재실행 감소의 주장 범위

전제를 제한하면 **알려진 선행 write를 무시하고 reader를 먼저 실행해서 생기는 재실행**은 방지할 수 있다. 충분조건은 완전한 허용 접근 범위, 해당 read 앞의 selected writers/deltas 완전성, 안정된 parent/input, 전체 rank를 따르는 준비된 결과의 사용이다. Cut 전에 이 조건들이 모두 성립했다고 일반적으로 증명할 수 없으므로 항상 retry=0이라고 주장하지 않는다.

주장하는 인과는 “관련 tx 배치 → 입력·상대 순서의 조기 파악 → 알려진 의존성을 지키는 실행 → 늦은 입력·역순 실행에 의한 무효화 감소 → cut 이후 잔여 작업 감소”다. 선언은 충돌의 상한이며 R-R, blind W-W, 순수 D-D의 동거를 모두 retry 감소로 세지 않는다.

제한된 분석 예: M개의 독립 writer→reader 쌍에서 동거한 쌍은 안정된 선행 결과를 사용하고, 다른 lane의 쌍만 확률 p로 한 번 retry하며, 순서·parent·다른 의존성이 바뀌지 않는다고 가정한다. 각 tx를 독립·균등하게 배치하는 이상적 baseline의 기대 retry는 `M(1−1/m)p`, 동거 확률 a인 affinity 배치에서는 `M(1−a)p`다. a>1/m일 때 이 모델에서 감소한다. 현재 multi-key 점수가 임의 workload에서 이 조건을 만족한다고 증명한 것은 아니다.

### 6.3 안전성과 liveness

- Same exact cut/parent/runtime/order의 결과는 routing history와 무관하게 serial oracle과 일치한다. 다른 배치가 다른 cut/order를 만든 경우까지 같은 결과라고 주장하지 않는다.
- 회전과 Pass가 기존 block을 무효화하지 않는다. Canonical replay/nonce 처리 없이 중복 안전성을 주장하지 않는다.
- Byzantine producer는 순서·포함·Pass를 조작할 수 있다. Mapping이 악의적인 producer를 신뢰할 수 있게 만들지는 않으며 실제 순서는 기존 consensus와 exact-cut execution으로 결정된다.
- False ACK/withheld Pass가 age reset이나 ordering 정지를 만들지 않는다. H cuts 뒤의 fanout은 모든 후보에 전달할 기회를 준다. H는 포함 완료 latency의 상한이 아니다.
- Liveness는 ordering 진전, 원본을 보관하는 정상 sender/relay, eventual delivery, 최소 하나의 정상 producer의 fair admission·충분한 용량에 의존한다. 네트워크 포화나 expiry 전 전달 실패에서 성공을 보장하지 않는다.
- 과대 선언, scope/tx-ID grinding, hot key는 편중·불필요한 의존성·트래픽을 늘린다. Scope/bytes 상한과 admission/transport budget을 적용한다. 새 gas/처벌 protocol은 도입하지 않는다.

## 7. 평가 계획

같은 선언·fee/replay 의미·실행 자원·offered load로 비교한다.

| 배치 | 분리하는 효과 |
|---|---|
| tx-ID hash → 고정 물리 lane | State affinity 없는 기준 |
| state affinity → 고정 물리 lane, 고정 tie-break | 같은 lane 배치의 효과 |
| state affinity → 고정 물리 lane, current-priority tie-break | 동점 처리만 회전하는 효과 |
| state affinity → slot별 회전 lane | 이 v3, 논리 priority 정렬과 물리 producer 회전 |

각 비교에서 같은 Block-STM을 사용하고 declaration-aware predecessor waiting의 on/off를 구분한다. 명시적 same-block packing을 추가하면 별도의 on/off 축으로 둔다. Routing만으로 자연스럽게 생긴 동거와 추가 packing 대기를 혼동하지 않는다.

주요 workload는 독립 key, 단일 hot key, 여러 hot components, multi-key bridge, 순수/조건부 D, 공통 fee payer다. RTT × application operation 수에 더해 cut별 tx 집합 변화, cut을 가로지르는 의존성, producer 속도 차이, Pass/fallback 비율, slot catch-up, late tip과 cut 제외를 바꾼다.

필수 지표:

- Cut→state certification / durable readiness, submit→state의 p50/p95/p99, ordering latency·goodput.
- Actual dependency의 same-lane/same-block 비율, 알려진/지연 도착 predecessor가 만든 invalidation, retry 횟수와 CPU/committed tx.
- Cut 내부와 cut 경계의 invalidation, parent/anchor 변경, queue/packing/dependency 대기, 총 CPU, 미완료 backlog.
- 실제 producer 부하, 선언 bytes, Pass 수, fallback fanout bytes, target q와 inclusion k의 차이, 중복 occurrence와 status/fee.

고정 exact-order trace의 executor 비교와 routing이 block/cut/order를 바꾸는 E2E 비교를 나눈다. 여러 seed·독립 반복·confidence interval을 사용하며 미완료 tx를 latency 집계에서 숨기지 않는다. Cut 자체를 늦춰 cut→state 차이만 작게 만든 결과는 개선으로 보지 않는다.

## 8. 검증과 구현 인계

[실행 가능한 계산 모델](./research/placement/cut-routing.mjs)과 [테스트](./research/placement/cut-routing.test.mjs)는 이미 정규화된 fixture scope/mode를 받아 후보 순위·fanout 대상·실제 block rank를 계산한다. 서명, schema 확장, 네트워크, 실행 캐시, fee/replay와 consensus는 구현하지 않는다.

모델 interface는 `rankProducers(tx, config, slot)`, `deliveryTargets(tx, config, state)`, `compareOccurrences(left, right, config, slot, anchors)` 세 함수다. Scope는 이미 canonicalized·implicit-expanded 상태이며, rank 비교는 검증된 동일 lane path와 already-ordered filtering 이후만 사용한다. 모델 정수 범위는 JavaScript safe integer로 제한하며 chain의 wire integer 타입을 정의하지 않는다. 오류 입력은 계산 오류로 거부하고 application failure로 바꾸지 않는다.

```sh
node --test research/placement/cut-routing.test.mjs
```

2026-09-21 검증 기록: 위 계산 모델의 **42개 테스트 통과**. 회전·multi-state 동점·mode 병합·hash 고정 예제·m=1/4·큰 slot, H 전후 및 catch-up fanout, q≠k rank, anchor 변경·잘못된 rank 입력을 검사했다. 별도 세 독립 리뷰에서 전달 수명, 실행 문맥, 회전 수학/평가를 점검하고 ordering 진척과 body fetch 분리·fair fanout·exact prefix identity를 보강했다. 서명·Pass transport·재시작·Block-STM/consensus E2E는 아래의 향후 acceptance 대상이며 이 테스트가 검증한 것은 아니다.

Engine 통합 전 필수 acceptance cases:

1. 같은 tx/config/q에서 선언 순서·mempool·부하를 바꿔도 후보 순위 일치. Scope 중복, pure/conditional D, implicit access, zero-score fallback.
2. 세 cuts의 완전 회전, m=1, 회전 wrap, 큰 slot, invalid config/범위 밖 mode 거부.
3. Same-attempt Pass 인증, 새 attempt에 old-q Pass를 재사용하는 지시·index 역행·위조 signer 거부. 잘못된 지시를 버려도 유효 원본 tx는 유지한다. 모든 후보 미포함, silence, false ACK, H 경계와 gap catch-up, restart 뒤 age 유지.
4. q≠k의 늦은 block, 기존 block과 재전파의 중복, finalized occurrence 뒤 전달 종료와 canonical status/fee 일치.
5. 상대 height가 lane priority보다 우선. 누적 anchor 변경에 따른 의존성 방향 변경, non-monotonic raw tips와 already-ordered filtering.
6. Late/excluded writer, generation의 늦은 완료, actual access 위반, defer 조건 변경에서 serial oracle과 state/status/events/fee 일치.
7. Producer가 권장 배치를 무시해도 유효 cut의 실행 safety 유지. 공격 상황에서도 ordering을 실행 대기에 묶지 않음.

여기의 수식·예시 테스트는 성능 향상, 암호 안전성, network liveness, Commonware E2E의 증거가 아니다. v1 JSON fixture와 과거 점검도 v3 구현 완료의 증거로 사용하지 않는다.

참고: [Block-STM](https://arxiv.org/html/2203.06871v3)은 preset-order execution·관측 검증, [AIP-47](https://github.com/aptos-foundation/AIPs/blob/main/aips/aip-47.md)는 typed deferred value의 참고점이다. 이 문서의 cut-relative routing/fallback은 이들이 제공하는 기존 기능이 아니라 여기서 정의한 연구 설계다.
