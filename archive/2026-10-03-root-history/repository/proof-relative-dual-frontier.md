# Proof-Relative Dual Frontier for Multimmit

> 상태: brainstorming note, **authoritative protocol이 아님**  
> 기준일: 2026-08-25  
> 현재 baseline: [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)

## 1. 목적

별도 Execution Certificate나 proof transaction의 다음-cut sequencing 없이, validity proof가 cut 전에 준비된 state prefix를
Multimmit의 현재 L-QC와 함께 final하게 만든다.

```text
one exact attributed vote transcript
  -> Ordering Frontier O_k
  -> Proof-Relative State Frontier S_k <= O_k
```

목표:

```text
proof ready before the direct-finality pool freezes
  => T_state-finality - T_ordering-cut ~= local join/apply cost
```

Commonware implementation에서는 `n-f` votes가 local arrival-first pool에 도달하면 L-QC aggregation보다 먼저 ordering finality fact가
발생한다. 따라서 local fast path는 같은 frozen pool에서 두 projection을 즉시 계산하고, L-QC는 그 exact transcript를 외부에 전달하는
portable evidence다.

## 2. EC와의 차이

EC는 validators가 같은 execution result를 재현하고 그 result에 quorum vote한다.

Proof-relative frontier에서 validator는 다음만 수행한다.

1. Public validity proof를 검증한다.
2. Proof가 인증하는 exact transition statement와 materialization data를 보관한다.
3. 기존 ordering vote에 자신이 보유한 highest proof-ready checkpoint를 첨부한다.

Validity는 proof-system soundness에서 나온다. Vote threshold는 proof의 수학적 validity를 만들지 않으며,
proposal-relative checkpoint selection과 proof/effect custody를 제공한다.

## 3. Proof checkpoint

Lane `i`의 proof checkpoint:

```text
ProofCheckpoint {
  epoch,
  lane_id,
  start_height,
  end_height,
  exact_block_sequence_commitment,
  pre_state_root,
  local_post_state_root,
  prepared_cross_effects_root,
  receipt_root,
  execution_version,
  materialization_data_commitment
}
```

Proof bytes는 randomized proving 때문에 달라질 수 있으므로 vote는 proof byte digest가 아니라 canonical public statement/checkpoint ID를
지원한다. Correct voter는 해당 checkpoint를 검증하는 적어도 하나의 proof artifact와 materialization sidecar를 보관해야 한다.

```text
CheckpointId = H(domain, canonical ProofCheckpoint fields)
```

Proof는 single block, recursive lane prefix 또는 contiguous segment를 인증할 수 있다.

## 4. Vote extension

기존 Multimmit vote의 ordering positions/extensions에 다음 필드를 추가한다.

```text
ProofSupportVector {
  for each lane i:
    highest_connected_checkpoint_i
}
```

Correct validator의 vote rule:

1. Ordering vote eligibility와 reservation은 기존 Multimmit 규칙을 따른다.
2. Proof verification은 별도 bounded worker에서 ordering과 병렬로 수행한다.
3. Vote를 reserve하는 순간 이미 verified-and-retained 상태인 checkpoint만 snapshot한다.
4. Proof가 없거나 늦어도 genesis/current state frontier를 보고하고 ordering vote를 정상적으로 낸다.
5. Proof readiness는 ordering vote의 선행조건이 아니다.
6. Reported checkpoint는 voter가 ordering vote에서 지원하는 exact lane path를 넘을 수 없다.

Proof bytes를 vote에 직접 넣지 않는다. Vote는 checkpoint ID와 compact position/root만 포함하고 artifact는 별도 gossip/fetch한다.

## 5. Dual-frontier extraction

Committee size `n=5f+1`, L-QC vote transcript size `m=n-f=4f+1`라고 하자.

Ordering frontier `O_k`는 기존 Multimmit drop rule로 계산한다.

각 lane의 reported proof checkpoint heights를 canonical branch와 root continuity로 정규화한 뒤, state support threshold `q_s`를
만족하는 최대 checkpoint를 선택한다.

```text
S_raw_k[i]
  = max checkpoint h <= O_k[i]
    supported by at least q_s votes in the L-QC
    and connected to the prior finalized state root
```

Equivalent order-statistic extraction:

```text
sort reported proof heights descending
S_raw_k[i] = q_s-th greatest compatible height, clipped to O_k[i]
```

### Threshold profiles

Proof soundness 때문에 `q_s`는 correctness quorum이 아니다.

| Profile | `q_s` | Honest supporters guaranteed | 의미 |
|---|---:|---:|---|
| Minimal custody | `f+1` | `1` | 적어도 한 honest retriever |
| Censorship-resilient custody | `2f+1` | `f+1` | globally `3f+1`가 support하면 어떤 `4f+1` L-QC에도 최소 `2f+1` 잔존 |
| Robust custody | `3f+1=n-2f` | `2f+1` | EC baseline과 같은 availability strength, readiness는 더 느릴 수 있음 |

권장 초기안은 `q_s=2f+1`이다.

- Proof 하나만으로 validity는 충분하다.
- `f+1` honest artifact holders는 eventual synchrony 아래 recovery에 충분하다.
- `3f+1` global supporters 중 Byzantine/aggregator가 최대 `f` supporters를 제외해도 L-QC 안에 `2f+1`가 남는다.

Deployment가 stronger materialization availability를 요구하면 `3f+1` profile을 평가한다. Threshold 선택은 safety가 아니라
latency/custody trade-off로 논문에 명시한다.

## 6. Evidence-relative state checkpoint

L-QC는 모든 attributed votes를 보존하므로 누구나 동일 transcript에서 `S_raw_k`를 재계산할 수 있다.
별도의 aggregated state signature가 필요하지 않다.

```text
StateCheckpoint = H(
  exact_evidence_id,
  previous_compatible_checkpoint,
  sorted[(lane_id, checkpoint_id, height, local_post_root)],
  selected_cross_components
)
```

이 commitment는 L-QC 밖에서 임의로 선택하는 값이 아니라 signed transcript의 deterministic derived fact다.

단, 서로 다른 replica의 first-arrival `n-f` pools는 같은 ordering tip을 만들면서도 proof-support voter 구성이 다를 수 있다. 따라서
state checkpoint는 ordering cut 하나의 globally unique 함수가 아니라 **exact direct-pool/L-QC evidence에 상대적인 checkpoint**다.
서로 다른 valid checkpoints는 동일 canonical history의 compatible prefix/order ideal이어야 하며, 더 높은 proof-ready checkpoint로
monotonic하게 refine할 수 있어야 한다.

## 7. Cross-lane dependency closure

Per-lane scalar proof frontiers만 독립적으로 적용하면 한 fragment만 state-finalize될 수 있다. Baseline의 prepared overlay를 유지한다.

1. `local_post_state_root`는 canonical local effects만 포함한다.
2. Cross fragment는 `prepared_cross_effects_root`에만 포함한다.
3. Per-lane `S_raw_k`를 먼저 계산한다.
4. ReadyBundle/DCLP, exact canonical placement, participant proof coverage와 application predicate가 모두 준비된 cross operation만
   component 후보로 만든다.
5. Candidate components를 canonical anchor/nonce order로 검사하여 dependency-closed set을 선택한다.
6. Selected component patches를 participant lane roots에 all-or-none으로 적용한다.

```text
FinalizeCross(X, LQC_k) iff
  valid ReadyBundle/DCLP(X)
  AND exact participant blocks <= O_k
  AND every participant prepared effect is covered by a supported proof checkpoint
  AND participant pre-roots are reachable
  AND joint application predicate accepts
  AND nonce is unconsumed
```

Participant supporter sets의 common intersection을 safety 조건으로 요구하지 않는다. 각 participant proof/effect artifact가
`q_s` supporters에게 개별적으로 recoverable하고 누구나 proof를 검증할 수 있으면 된다. Atomicity는 deterministic component selection과
one durable commit record가 보장한다.

## 8. Same-cut fast path

Timeline:

```text
producer block / DA
  -> speculative execution and proof generation
  -> proof gossip and validator verification/custody
  -> leader proposal
  -> ordering votes snapshot order position + proof checkpoint
  -> n-f arrival-first pool freezes
       -> derive O_k
       -> derive proof-supported S_k
  -> aggregate the same frozen transcript into a portable L-QC
  -> root join / durable apply
```

Proof가 vote snapshot 전에 충분히 전파되면 state frontier가 ordering cut과 같은 L-QC에서 전진한다.

```text
Gap_same_cut ~= T_transcript_extract
                + T_dependency_closure
                + T_atomic_root_commit
```

Hyli식 proof transaction을 다음 block/cut에 다시 sequence하는 latency가 없다.

## 9. Late-proof path

Proof가 L-QC vote snapshot 뒤에 도착하는 경우 두 정책이 가능하다.

### Policy A — Next-LQC checkpoint

다음 L-QC vote가 proof checkpoint를 support할 때까지 기다린다.

장점:

- 모든 externally advertised state frontier가 L-QC-derived fact다.
- Proof/effect custody가 명확하다.

단점:

- Proof가 cut 직후 도착해도 최대 한 view/cut quantization latency가 생긴다.

### Policy B — Objective late join

이미 canonical ordering cut 안의 exact blocks에 대한 proof가 도착하면 누구나 즉시 검증하여 local state frontier를 전진시킨다.
다음 L-QC는 이를 portable checkpoint로 기록한다.

장점:

- Cryptographic proof가 도착한 즉시 state correctness를 확인할 수 있다.

단점:

- Node마다 materialization 시점이 다르고 L-QC 전에는 common custody checkpoint가 없다.

초기 논문은 same-cut fast path와 Policy A를 protocol claim으로 두고, Policy B를 latency optimization/ablation으로 비교하는 편이 명확하다.

## 10. Safety reasoning

### Proof validity

유효한 proof가 canonical checkpoint를 인증하면, proof-system soundness 아래 그 pre-state와 exact block sequence에서 다른 correct
post-state는 존재하지 않는다.

### Canonicality separation

Valid proof도 `O_k`가 선택한 exact canonical branch 밖에 있으면 state effect가 없다. Proof는 ordering을 만들지 않는다.

### Compatible state checkpoints

서로 다른 valid direct-pool/L-QC transcripts가 서로 다른 proof-ready heights를 추출해도 같은 canonical lane의 compatible prefixes여야
하며, 동일 checkpoint height의 conflicting roots는 proof soundness로 배제된다. Cross-lane components까지 포함한 compatibility는 별도의
dependency-order theorem이 필요하다.

### Custody

`q_s=2f+1` supporters 중 최대 `f`가 Byzantine이므로 적어도 `f+1` honest validators가 proof/effect artifact를 보관한다.

### Cross-lane atomicity

Participant local roots가 prepared effects를 제외하고 component selector가 complete participant set만 one-record apply하면,
cross operation의 strict subset은 canonical state에 나타나지 않는다.

## 11. 공격과 한계

### False proof-support report

Byzantine voter는 보유하지 않은 checkpoint를 보고할 수 있다. Threshold 안의 honest supporters와 fetch challenge가 artifact recovery를 제공한다.
반복 false report는 signed accountability evidence이지만 slashing은 safety 전제가 아니다.

### Aggregator/subset censorship

L-QC aggregator가 proof-supporting votes를 가능한 만큼 제외할 수 있다. 어떤 `4f+1` subset에서도 `2f+1` state support를 남기려면
전체 committee에서 적어도 `3f+1`가 vote snapshot 전에 proof를 support해야 한다.

이 조건이 안 되면 state frontier가 덜 전진할 수 있지만 ordering safety/liveness는 영향받지 않는다.

### Direct finality before L-QC assembly

Commonware는 `n-f` local votes로 leader를 즉시 finalize하고 L-QC를 비동기 조립한다. 따라서 metric을 다음처럼 분리한다.

```text
T_direct_ordering_fact
T_local_proof_checkpoint
T_portable_lqc
T_external_proof_checkpoint
```

Local same-cut claim은 첫 두 시점의 차이다. 외부 client-facing finality는 L-QC와 proof artifact가 모두 도착한 시점이므로 L-QC aggregation,
gossip와 fetch latency가 남는다.

### Proof availability without materialization

Proof bytes만 보유하고 changed values/effect log/authenticated-tree update data가 없으면 root correctness는 검증할 수 있어도 queryable state를
복원하지 못한다. Support rule은 materialization data commitment와 retention을 함께 요구해야 한다.

### Proof lag

Proving throughput이 block arrival rate보다 낮으면 proof frontier backlog가 계속 증가한다. Recursive folding은 proof size를 줄일 수 있지만
proving capacity 부족을 자동으로 해결하지 않는다.

### Dynamic cross-lane access

Proof 생성 전에 participant/read-write set을 결정할 수 없는 transaction은 independent lane proof composition이 어렵다. Joint proof 또는
SlowPath가 필요하다.

### Vote size

모든 lane checkpoint를 raw vector로 넣으면 vote size가 lane 수에 비례한다. 기존 ordering position vector와 같은 lane order를 공유하여
delta encoding하고, unchanged frontier run-length encoding 또는 vector commitment를 평가한다.

## 12. Related-work boundary

- [Hyli pipelined proving](https://docs.hyli.org/concepts/pipelined-proving/)은 blob transaction을 먼저 sequence하고 proof transaction을 나중에 sequence/settle한다.
- [Mina parallel scan state](https://minaprotocol.com/wp-content/uploads/technicalWhitepaper.pdf)는 block production과 recursive SNARK work queue를 분리한다.
- [Kaspa vProgs](https://kaspa.co.il/wp-content/uploads/2025/09/vProgs_yellow_paper.pdf)는 conditional proof batches와 Computation DAG로 proof dependencies를 stitch한다.
- [Flow execution verification](https://arxiv.org/abs/1909.05832)은 execution receipts와 verification approvals를 consensus 이후 pipeline한다.
- [Algorand State Proofs](https://dev.algorand.co/concepts/protocol/state-proofs/)는 block intervals에 대한 network-signed state proofs를 별도 transaction으로 다시 consensus에 넣는다.

약한 novelty:

- Asynchronous proof generation
- Recursive lane proof
- Proof-ready state frontier
- Proof availability vote/certificate

차별화 후보:

1. 기존 Multimmit attributed ordering votes에 proof checkpoint custody를 proposal-relative extension으로 넣는다.
2. 동일 L-QC transcript에서 full ordering cut과 더 짧은 proof-relative state cut을 동시에 추출한다.
3. Proof readiness가 ordering vote의 선행조건이 아니며 proof transaction을 다음 cut에 다시 sequence하지 않는다.
4. Per-lane proof frontier를 prepared overlays와 dependency-closed N-lane component selection에 결합한다.
5. `q_s`를 proof correctness가 아닌 custody/censorship-resilience parameter로 분석한다.

권장 claim:

> We extend Multimmit votes with proposal-relative proof checkpoints and derive two frontiers from the same L-QC transcript: a full ordering cut and a proof-supported, dependency-closed state cut. Validity follows from succinct proofs, while the L-QC support order statistic provides canonical checkpoint selection and artifact custody without a separate execution certificate or proof-transaction round.

## 13. Formal properties 후보

### Theorem 1 — Proof-relative checkpoint validity

Sound proof system과 exact canonical binding 아래에서 `S_k`가 선택한 모든 local checkpoint는 canonical transaction sequence의 correct state transition이다.

### Theorem 2 — Dual-frontier determinism

같은 previous state frontier와 exact attributed direct-pool/L-QC transcript를 가진 correct validators는 같은 `O_k`, raw proof frontier와
dependency-closed `S_k`를 계산한다.

### Theorem 2b — Cross-transcript compatibility

같은 leader/view의 서로 다른 valid arrival-first transcripts가 추출한 state checkpoints는 canonical state-history partial order에서
compatible하며, 어느 checkpoint도 동일 object version에 상충하는 final effect를 만들지 않는다.

### Theorem 3 — Custody

`q_s=2f+1` support로 선택된 checkpoint artifact를 적어도 `f+1` correct validators가 retention rule에 따라 보유한다.

### Theorem 4 — Ordering non-interference

Proof checkpoint가 current state frontier에 머물러도 ordering vote가 유효하고 existing Multimmit position extraction이 변하지 않으므로,
proof lag만으로 ordering progress가 중지되지 않는다.

### Theorem 5 — Cross-lane all-or-none

Dependency-closed component selector와 prepared local roots 아래에서 selected N-lane operation의 participant effects는 모두 적용되거나 모두 적용되지 않는다.

## 14. 평가 계획

Baselines:

```text
B0 post-cut execution
B1 asynchronous proof + next-block proof transaction
B2 proof-ready local join without L-QC support
B3 proof-relative dual-frontier L-QC
B4 B3 + cross-lane dependency closure
B5 EC baseline
```

Metrics:

```text
proof_ready_before_vote_ratio
proof_supporters_per_lqc
same_cut_state_finality_ratio
T_ordering_cut
T_cut_to_state p50/p95/p99
T_direct_fact_to_portable_lqc
T_direct_fact_to_external_checkpoint
proof/effect fetch success and latency
vote size overhead
proof verification CPU
state_frontier_lag
```

Threshold sweep:

```text
q_s in {f+1, 2f+1, 3f+1}
```

Faults:

- Byzantine leader/aggregator omits proof supporters
- False custody reports
- Proof/effect withholding
- Proof arrives just before/after vote snapshot
- Invalid/non-canonical proof
- Missing cross-lane participant proof
- Recursive proof lag and backlog

성공 기준:

1. B3가 B1의 extra proof-transaction cut latency를 제거한다.
2. B3의 ordering cut latency가 B0/B1보다 유의하게 악화되지 않는다.
3. `q_s=2f+1`에서 artifact recovery가 fault bound 안에서 성공한다.
4. Cross-lane partial proof/placement에서도 participant subset state가 적용되지 않는다.
5. 모든 correct validator가 동일 L-QC transcript에서 byte-identical state cut commitment를 계산한다.

## 15. 현재 판단

1. 엄밀한 protocol state finality를 EC 없이 줄이려면 validity proof는 가장 현실적인 선택이다.
2. Proof를 다음 transaction/cut에 넣는 모델은 선행기술이 강하고 추가 latency가 있다.
3. **Proof-Relative Dual Frontier**는 기존 Multimmit L-QC를 재사용해 same-cut ordering/state finality를 제공하는 더 강한 후보다.
4. 핵심 novelty는 proof가 아니라 proposal-relative vote transcript에서 dual frontier와 custody를 추출하는 규칙이다.
5. 가장 큰 위험은 proof-ready supporter 수, vote-size 증가, proof materialization availability와 cross-lane closure 복잡도다.

## 16. 무엇이 final해지는가

논문은 다음 두 시점을 분리해야 한다.

```text
T_root-finality
  = canonical ordering + valid transition proof + deterministic state-cut selection이 고정된 시점

T_materialization
  = selected effect data를 durable tree/database에 실제 반영하고 query 가능한 시점
```

Proof-relative L-QC가 직접 줄이는 것은 `T_root-finality - T_ordering-cut`이다. Proof가 인증한 post-state root와 exact transition은
같은 L-QC transcript로 고정되므로 이 간격을 local extraction 수준으로 줄일 수 있다. 반면 effect sidecar fetch, database update와 index
construction은 그 뒤에도 남을 수 있다.

따라서 실험에서 `state finality`를 단순히 "DB write 완료"로 정의하면 contribution이 흐려지고, 반대로 root만 확정한 뒤 query latency를
숨기면 과장이다. 두 metric을 모두 보고해야 한다.

```text
T_cut_to_root_final
T_cut_to_queryable_state
```

## 17. Commonware Multimmit 적합성 점검

현재 Commonware 구현의 L-QC는 단순 aggregate signature만 보존하지 않는다. `Lqc.tally`가 signer bitmap, reference vote와 deviations를
보존하고, 각 signer의 exact `VoteBody`를 다시 복원하여 final tip을 계산한다. 따라서 attributed transcript에서 proof-support order
statistic을 계산한다는 전제는 구현과 맞는다.

그러나 기존 `VoteBody.extensions`는 arbitrary application metadata가 아니다. 각 extension은 voter가 DA-vote한, proposal position 이후의
contiguous producer-block suffix를 표현하며 Multimmit ordering algebra가 직접 사용한다. Proof checkpoint를 이 필드에 섞으면 ordering
semantics와 final-tip extraction을 깨뜨린다.

필요한 wire change는 다음과 같다.

```text
VoteBody {
  existing round / leader / positions / ordering_extensions,
  proof_checkpoints: CompactProofCheckpointVector,
}

Tally {
  existing ordering reference/deviations,
  proof reference vector + signer-attributed deviations,
}
```

필수 조건:

1. `proof_checkpoints`는 ordinary vote signature의 subject 안에 들어간다. Unsigned side metadata이면 aggregator가 변조할 수 있다.
2. L-QC verification은 aggregate signature가 compact proof tally까지 인증하는지 확인한다.
3. Final-tip algebra는 기존 ordering fields만 읽고 변하지 않는다.
4. State-frontier algebra만 proof checkpoint fields를 추가로 읽는다.
5. Proof checkpoint size/entry count에 codec bound를 둬 hostile vote로 인한 memory amplification을 막는다.
6. Proof verification이나 artifact fetch 실패는 해당 checkpoint를 낮출 뿐 vote reservation을 막지 않는다.

즉 이 아이디어는 application-side glue만으로 끝나지 않는다. Multimmit signed vote/tally/wire format과 finality projection을 실제로
확장해야 하며, 바로 그 지점이 prototype의 핵심 구현 범위다.

## 18. 가장 중요한 falsification test

이 설계가 의미 있으려면 다음 조건을 동시에 만족해야 한다.

```text
proof checkpoint support is ready before vote snapshot
AND ordering L-QC latency is not measurably increased
AND selected proof/effect artifact is recoverable
AND cross-lane closure completes without post-cut execution
```

첫 조건이 낮으면 same-cut ratio가 낮고, 둘째가 깨지면 state gap을 ordering latency 앞으로 옮긴 것뿐이다. 셋째가 깨지면 root-only
finality이며, 넷째가 깨지면 cross-lane workload에서는 기존 post-cut slow path가 남는다. 이 네 조건을 따로 측정해야 novelty가
실제 systems contribution인지 판별할 수 있다.
