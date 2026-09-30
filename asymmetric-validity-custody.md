# Asymmetric Validity Custody

> 상태: brainstorming note, **authoritative protocol이 아님**  
> 기준일: 2026-08-25  
> 현재 baseline: [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)

## 1. 질문

Validity proof를 `n-2f` validators에게 다시 dispersal/certify하지 않고도 strict proof-backed state finality의 durable availability를 보장할
수 있는가?

핵심 관찰:

1. Original block, declared effect와 materialization data는 이미 Multimmit DA path에서 `n-2f` custody를 가진다.
2. Late artifact 중 새로 필요한 것은 작은 succinct proof bytes다.
3. Proof correctness는 quorum intersection이 아니라 public verifier가 판단한다.
4. Proof를 적어도 한 correct validator가 보관하면 eventual synchrony 아래 다른 correct nodes가 복구할 수 있다.

따라서 data와 proof에 같은 threshold를 쓸 필요가 없다.

## 2. 세 availability layer

### 2.1 Ordered effect data

```text
DataAvailability(block/effect/materialization) = n-2f
```

정확히 `n=5f+1`이면 `3f+1` shares이며 적어도 `2f+1` correct holders가 있다.

Block payload에 다음이 먼저 binding되어야 한다.

```text
statement_id
declared input/read versions
declared output/write commitments
effect/materialization commitment
proof system and execution version
```

Proof가 나중에 도착해도 이를 열어야 한다.

### 2.2 Objective proof visibility

Observer가 exact proof를 받아 직접 검증하면 그 observer에게 correctness evidence는 이미 충분하다.

```text
ObjectiveProofReady(observer, statement)
  = observer holds proof
    AND Verify(proof, statement)=true
```

이 시점에는 quorum이 필요 없다. 다만 observer가 proof의 유일한 holder일 수 있어 network-wide durability는 보장하지 않는다.

### 2.3 Durable proof custody

`f+1` distinct validators가 proof를 검증하고 statement에 대해 artifact retention receipt를 발행한다.

```text
ProofCustodyReceipt {
  epoch,
  statement_id,
  artifact_commitment,
  proof_system_id,
  retention_until,
  signer
}
```

```text
DurableProofCertificate
  = f+1 matching verified-custody receipts
```

At most `f` Byzantine validators이므로 certificate에는 적어도 한 correct holder가 있다.

## 3. 왜 f+1이면 충분한가

EC uniqueness에는 두 conflicting quorums의 honest intersection이 필요하다. Proof custody에는 conflicting results를 vote로 배제할 필요가
없다.

```text
Correctness: proof soundness
Canonicality: exact Multimmit ordering inclusion
Durability: at least one correct proof holder
Materialization: original n-2f block DA
```

따라서 proof durability threshold의 목적은 다음 하나다.

```text
|Custodians| > f
```

즉 최소 `f+1`이다.

### Lemma — Honest custodian

At most `f` Byzantine faults에서 `f+1` distinct verified-custody receipts를 가진 certificate는 적어도 한 correct signer를 포함한다.

### Corollary — Eventual proof recovery

Correct custodian이 `retention_until`까지 proof bytes를 보관하고 post-GST authenticated requests에 응답한다면, certificate를 가진 correct
requester는 proof를 eventually recover할 수 있다.

이 정리는 즉시 응답 latency나 bandwidth를 보장하지 않는다. `n-2f` custody보다 tail recovery는 약하다.

## 4. Receipt rule

Correct validator는 다음 조건에서만 receipt를 발행한다.

1. Exact statement/effect data가 original DA-certified block에 binding된다.
2. Proof artifact encoding과 size가 bounded다.
3. Public verifier가 proof를 accept한다.
4. Artifact commitment가 실제 retained bytes와 일치한다.
5. Required retention storage를 durable하게 reserve했다.
6. 동일 statement에 대한 local receipt limit을 넘지 않는다.

Receipt는 state root에 대한 신뢰 vote가 아니다. Recipient도 proof를 fetch하고 독립적으로 검증한다.

Proof system이 randomized encodings를 허용하면 같은 statement에 여러 artifact commitments가 있을 수 있다. Safety 문제는 없지만 storage
spam을 막기 위해 validator는 statement당 bounded candidates만 custody한다.

## 5. Timing

Proof producer가 proof를 생성한 시점을 `t_p`, validator `j`의 one-way network delay를 `delta_j`, proof verification 시간을 `v_j`라고 하자.

Objective observer finality:

```text
T_objective
  = t_p + delta_observer + v_observer + T_dependency_join
```

`f+1` durable custody:

```text
T_custody
  = t_p
    + (f+1)-th order statistic of (delta_j + v_j + return_delta_j)
    + T_certificate_gossip
```

`n-2f=3f+1` full DA custody와 비교하면 network round 수는 같을 수 있지만 response order statistic이 낮아진다. Heterogeneous/straggling
validators에서 tail latency를 줄이는 것이 목표다.

State event finality profiles:

```text
Local objective profile:
  max(T_ordering, T_objective, T_predecessors) + T_join

Portable durable profile:
  max(T_ordering, T_custody, T_predecessors) + T_fetch_verify_join
```

Proof가 ordering cut 전에 준비되면 두 profile 모두 same-cut 후보가 된다. Proof가 cut 뒤에 준비돼도 다음 ordering cut을 기다리지 않는다.

## 6. Same-cut piggyback

Proof가 ordinary Multimmit vote reservation 전에 도착하면 별도 receipt message 없이 기존 signed vote에 compact custody coordinate를 포함할 수
있다.

```text
proof held/verified before vote
  -> vote includes (statement_id, artifact_commitment)
  -> exact direct-finality pool contains >= f+1 matching custodians
  -> same frozen pool yields ordering cut + durable proof custody
```

이는 proof correctness를 vote로 정하지 않는다. Correct signers가 retained artifact를 나중에 serve할 수 있다는 뜻이다.

Proof가 vote 뒤에 도착하면 standalone receipt gossip을 사용한다. State refinement는 다음 view/cut을 기다리지 않는다.

## 7. Cross-lane operation

Cross operation `X`에는 participant fragments별 materialization data가 original participant blocks의 DA에 들어 있다. Proof custody는 두 방식이
가능하다.

### One joint proof

```text
JointProof(X)
  -> f+1 custodians of one artifact
  -> verify all participant effects and joint predicate
```

가장 단순하고 cross-lane proof completeness가 artifact 하나에 묶인다.

### Participant-local proofs

```text
for every participant lane i:
  valid DurableProofCertificate(X,i)
AND DCLP(X)
AND joint predicate proof/checker
```

Custodian sets가 서로 교차할 필요는 없다. 각 artifact certificate에 적어도 한 correct holder가 있고 atomicity는 state ideal의 one hypernode
selection이 보장한다.

## 8. 공격 분석

### Byzantine-only receipts

`f` Byzantine nodes만으로 `f+1` certificate를 만들 수 없다.

### Invalid proof poisoning

Correct validators가 verify-before-receipt를 지키면 invalid proof는 `f+1` receipts를 얻을 수 없다. Recipient의 independent verification도
필수다.

### Honest single-holder bottleneck

Worst case certificate의 correct holder가 한 명뿐이면 recovery bandwidth와 latency가 나빠진다.

완화:

- Initial proof broadcast는 모든 validators에게 수행
- Custodian signer bitmap을 certificate에 보존
- Fetch fanout to all custodians
- Popular artifacts의 opportunistic replication
- `q_p in {f+1, 2f+1, 3f+1}` adaptive profile 평가

### Receipt then delete

Correct signer는 durable reservation 이후에만 서명하고 `retention_until` 전에 삭제하지 않는다. Byzantine deletion은 honest custodian lemma로
safety/liveness를 깨지 않는다.

### Artifact spam

Proof가 valid해도 동일 statement의 randomized variants를 무한 생성할 수 있다.

완화:

- Statement당 first valid artifact 또는 deterministic preference
- Per-prover bond/fee
- Per-epoch storage/gossip budget
- Cumulative proof가 artifact를 subsume하면 earlier variants prune

### Withheld original effect data

Proof bytes만 있어도 queryable state를 만들 수 없다. State-final eligibility는 referenced effect/materialization commitment의 original DA
certificate와 recovery를 함께 요구한다.

### Proof-producibility failure

Custody threshold는 아직 생성되지 않은 proof를 만들지 못한다. Public witness reconstruction, permissionless prover takeover 또는 deterministic
slow path가 필요하다.

## 9. Retention and compaction

Proof artifact는 다음 중 하나가 성립할 때까지 보관한다.

1. A later cumulative/recursive proof cryptographically subsumes it.
2. A portable state checkpoint plus snapshot availability artifact makes replay proof unnecessary.
3. Protocol-defined retention epoch expires and state sync no longer promises that historical checkpoint.

Correct custodian가 arbitrary local timer로 삭제하지 않도록 `retention_until`은 consensus-visible epoch/height로 표현한다.

## 10. Novelty 경계

`f+1`이 one honest party를 보장한다는 quorum arithmetic, proof broadcast, custody receipts와 signer bitmap은 novelty가 아니다.

방어 가능한 역할:

1. Multimmit의 `n-2f` block/effect DA와 `f+1` succinct-proof durability를 명시적으로 분리한다.
2. Proof correctness, effect availability와 proof durability가 요구하는 trust thresholds가 서로 다름을 formalize한다.
3. Same-cut vote piggyback와 post-cut standalone receipt를 하나의 latency-adaptive path로 만든다.
4. Evidence-refined state lattice에서 receipt threshold가 safety가 아니라 recovery latency parameter임을 보인다.

이 mechanism은 main novelty가 아니라 consensus-free validity refinement의 tail-latency optimization으로 두는 편이 안전하다.

## 11. Evaluation

Threshold profiles:

```text
q_p = 1              // objective local only
q_p = f+1            // one correct custodian
q_p = 2f+1           // at least f+1 correct custodians
q_p = n-2f=3f+1      // at least 2f+1 correct custodians
```

Metrics:

```text
proof broadcast-to-objective-finality
proof broadcast-to-durable-custody
proof recovery success and p50/p95/p99
custodian count and correct-holder lower bound
receipt/certificate bytes
validator verification CPU
proof storage and pruning delay
same-cut durable-finality ratio
ordering latency regression from vote piggyback
```

Faults:

```text
f Byzantine non-serving custodians
one slow correct custodian
invalid proof flood
randomized valid-proof variants
proof arrives immediately before/after vote reservation
effect data recovery delay
```

성공 기준은 `f+1`이 항상 가장 빠르다는 것이 아니다. It must materially lower proof-custody tail latency while maintaining successful recovery
under the assumed fault bound and without delaying ordering votes.
