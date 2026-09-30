# Evidence-Refined State Lattice

> 상태: brainstorming note, **authoritative protocol이 아님**  
> 기준일: 2026-08-25  
> 현재 baseline: [proof-aware-multimmit-paper.md](./proof-aware-multimmit-paper.md)

## 1. 해결하려는 구조적 문제

Commonware Multimmit의 local finality는 arrival-first `n-f` vote pool로 즉시 발생하고 L-QC는 나중에 조립된다. Correct replicas가 서로
다른 exact vote pools를 가질 수 있으므로 다음 상황이 가능하다.

```text
OrderingFrontier(Pool_A) = OrderingFrontier(Pool_B)
ProofFrontier(Pool_A) != ProofFrontier(Pool_B)
```

Proof-ready state를 cut마다 하나의 globally unique root로 강제하려면 state evidence를 다시 ordering하거나 별도 agreement round가
필요하다. 그러면 줄이려던 cut-to-state gap이 다시 생긴다.

대안은 state finality를 scalar checkpoint가 아니라 **monotonic evidence lattice**로 정의하는 것이다.

## 2. 핵심 직관

Ordering cut은 실행 가능한 event의 상한을 정한다. Validity evidence는 그 안에서 이미 안전하게 확정할 수 있는 event 집합을 늘린다.

```text
fixed canonical ordering upper bound O
  + growing validity evidence E_0 <= E_1 <= E_2 ...
  -> growing finalized state ideals I_0 <= I_1 <= I_2 ...
```

Proof가 늦게 도착해도 ordering cut을 변경하지 않는다. 기존 state effect를 revoke하지 않고, 새 evidence가 허용하는 dependency-closed
effect만 추가한다.

## 3. State event graph

Canonical ordering cut `O` 안의 application state events를 directed graph/hypergraph `G_O=(V,D)`로 만든다.

### 3.1 Vertices

```text
LocalEvent(i,h)
  = lane i의 exact canonical block/effect transition

CrossEvent(X)
  = X의 모든 participant fragments를 collapse한 one atomic hypernode
```

Cross fragments를 서로 다른 vertices로 두지 않는다. Complete DCLP와 participant proof coverage를 갖춘 경우에만 하나의
`CrossEvent(X)` candidate가 된다.

### 3.2 Dependency edges

`u -> v`는 `v`를 state-finalize하려면 `u`가 먼저 state-final해야 함을 뜻한다.

최소 edge:

1. Lane/root continuity
2. Object-version producer-to-consumer
3. Read-after-write and write-after-write dependency
4. Cross participant pre-state dependencies
5. Canonical nonce/conflict winner before loser/no-op resolution
6. Application-declared invariant dependency

Prepared cross effects를 읽는 suffix는 반드시 해당 `CrossEvent`의 descendant가 된다.

### 3.3 Deterministic conflict order

같은 mutable object version을 소비하려는 conflicting events에는 canonical ordering cut이 결정한 winner/no-op 순서를 적용한다. 따라서
두 validity proofs가 서로 다른 event를 동시에 winner로 만들 수 없다.

## 4. State ideal

집합 `I subseteq V`가 다음 조건을 만족하면 state ideal이다.

```text
v in I => every predecessor of v is in I
```

추가 eligibility:

- Event의 exact blocks가 `O` 안에 있다.
- Event transition을 덮는 valid proof/effect checker evidence가 있다.
- CrossEvent는 ReadyBundle/DCLP, all-participant proof coverage와 joint predicate를 만족한다.
- Input versions와 nonce가 single-consumption rule을 통과한다.

Evidence set `E`가 허용하는 maximal ideal:

```text
I(O,E) = deterministic maximal dependency-closed eligible event set
```

여러 maximal set이 가능한 conflict는 canonical event order로 tie-break하여 determinism을 유지한다.

## 5. Lattice property

같은 canonical ordering history 안의 valid ideals `I_1`, `I_2`에 대해:

```text
meet: I_1 AND I_2 = I_1 intersection I_2
join: I_1 OR  I_2 = I_1 union I_2
```

Order ideals의 intersection과 union도 order ideal이다. 따라서 서로 다른 exact transcripts가 만든 checkpoints가 같지 않아도 conflict 없이
join할 수 있다.

Validity evidence도 함께 합친다.

```text
Checkpoint(O,E_1) join Checkpoint(O,E_2)
  = Checkpoint(O,E_1 union E_2)
```

이 주장이 성립하려면 다음이 필수다.

1. 두 checkpoints가 같은 canonical history 또는 compatible ordering prefixes에 속한다.
2. Proof statement가 exact block/object versions에 binding된다.
3. Cross fragments는 partial vertices가 아니라 one hypernode다.
4. Conflicting writes의 canonical winner가 proof readiness와 무관하게 고정된다.
5. State commitment가 independent ideal components를 composition할 수 있다.

### 5.1 Root-only proof는 join할 수 없다

초기 Merkle root `R0`에서 서로 다른 keys `x`, `y`를 갱신하는 independent effects를 생각한다.

```text
proof_X: R0 -> RX   // x := 1
proof_Y: R0 -> RY   // y := 1
```

Proof public outputs가 `RX`, `RY`뿐이면 hash one-wayness 때문에 `RXY`를 `R0,RX,RY`에서 계산할 수 없다. 더 심각하게는 X를 먼저
적용한 뒤 Y proof의 declared pre-root `R0`가 현재 root `RX`와 일치하지 않는다. Application-level commutativity만으로 cryptographic
root transition proof가 자동 rebase되는 것은 아니다.

따라서 lattice join에는 다음이 필요하다.

```text
RebasableEffectProof {
  exact operation/block binding,
  consumed object versions,
  read object commitments,
  created/written object commitments,
  semantic validity proof,
  authenticated sparse multipatch,
  dependency manifest
}
```

Semantic proof는 global root transition보다 input/output objects와 effect validity를 인증한다. Cut/checkpoint에서 current root에 대한
membership, version single-consumption과 multipatch composition을 별도로 검증한다. Read/write versions가 그대로이면 unrelated root changes
후에도 proof를 재사용할 수 있다.

### 5.2 두 execution mode

#### Prefix mode

Lane-wide cumulative proof를 사용한다. Lane마다 scalar proof prefix만 전진하며 cross effect를 읽는 suffix는 component 전체가 준비될 때까지
멈춘다.

장점:

- Existing VM/IVC proof와 결합하기 쉽다.
- Per-lane root continuity theorem이 단순하다.

한계:

- 한 proof gap이 lane suffix 전체를 막는다.
- 서로 다른 lane roots는 vector로 join할 수 있지만 lane 내부 independent effects를 부분 join할 수 없다.

#### Effect mode

Root-independent/rebasable effect proofs와 object-version dependencies를 사용한다. State checkpoint는 event-level ideal이 된다.

장점:

- Proof lag가 exact dependency cone에 한정된다.
- Independent effects를 different arrival order에도 합칠 수 있다.

한계:

- Complete access/effect declaration과 authenticated multipatch가 필요하다.
- Arbitrary dynamic contract를 compiler/runtime가 effect proof 형태로 낮춰야 한다.
- Proof/metadata overhead와 trusted compiler surface가 커진다.

논문은 두 mode를 혼합하여 theorem을 쓰면 안 된다. Prefix-mode claim은 lane-scoped lag containment, effect-mode claim만 dependency-cone
containment로 제한한다.

## 6. Checkpoint representation

```text
StateLatticeCheckpoint {
  epoch,
  ordering_evidence_id,
  ordering_frontier,
  proof_evidence_commitment,
  ideal_commitment,
  lane_or_component_frontiers,
  component_state_roots,
  consumed_object_versions_root,
  materialization_commitment
}
```

Global monolithic root 하나만 내보내면 incomparable ideals의 관계를 잃는다. Portable checkpoint는 vector/component roots와 ideal commitment를
함께 제공하고, convenience global root는 그 vector를 canonical Merkle composition하여 만든다.

```text
GlobalRoot(I) = MerkleRoot(sorted component checkpoints of I)
```

## 7. 두 종류의 advancement

### 7.1 Consensus-anchored advancement

Exact direct vote pool/L-QC transcript에서 quorum-supported proof coordinates를 추출한다.

```text
Pool/L-QC arrives
  -> derive ordering bound O
  -> derive supported evidence snapshot E_q
  -> publish named Checkpoint(O,E_q)
```

장점은 common custody와 portable checkpoint naming이다.

### 7.2 Objective proof refinement

이미 final한 exact ordering cut 안의 event에 대한 valid proof sidecar가 뒤늦게 도착하면 다음 cut을 기다리지 않는다.

```text
valid exact-cut proof arrives
  -> E := E union {proof}
  -> I := I(O,E)
  -> atomically join newly eligible effects
```

Validity proof는 self-authenticating하므로 correctness를 위한 새 vote가 필요 없다. Node마다 refinement 관찰 시점은 다를 수 있지만, 모든
correct nodes의 checkpoints는 join-compatible하다. 다음 L-QC는 latest checkpoint를 portable anchor로 만들 수 있으나 local/objective
finality의 선행조건은 아니다.

Protocol-wide retrievability가 필요하면 proof/effect sidecar commitment에 existing Multimmit `n-2f` DA threshold profile을 적용한
`ValidityArtifactAvailabilityCertificate`를 사용한다. 정확히 `n=5f+1`이면 `3f+1` custody shares이며 적어도 `2f+1` honest holders가
남는다. 이 certificate는 proof correctness나 event canonicality를 대신하지 않는다.

```text
State evidence edge
  = canonical ordering inclusion
    + valid proof artifact
    + artifact availability certificate
```

Local node가 artifact를 직접 보유한 경우 certificate 전에도 objective verification은 가능하지만, portable/BFT-retrievable checkpoint는
certificate-ready 시점으로 측정한다.

### 7.3 Missing-proof resolution

Canonical order에서 earlier event `x`가 object version을 소비할 수 있는데 proof가 아직 없다면, later conflicting event `y`를 finalize할 수
없다. `x`가 나중에 valid해질 가능성을 배제할 objective evidence가 없기 때문이다.

선택지는 다음뿐이다.

1. `x` proof가 도착할 때까지 해당 dependency cone을 기다린다.
2. Public block/state data로 permissionless prover takeover를 허용한다.
3. Proof receipt/expiry를 consensus-visible inbox에 ordering하여 deterministic no-op을 만든다.
4. Deadline 후 deterministic reexecution slow path를 사용한다.

3번은 proof를 다시 ordering하지 않는 claim을 약화시키고, 4번은 non-proof execution latency가 돌아온다. 초기안은 1+2를 사용하고
unrelated components만 전진시키는 것이 가장 정직하다. Proof producibility를 위해 block payload, execution version과 witness-reconstruction
data가 DA-retrievable해야 한다.

## 8. Finality 의미

이 모델은 finality를 세 수준으로 나눈다.

```text
Event finality:
  event v가 ideal에 들어가고 이후 제거되지 않는다.

Component state finality:
  dependency component c의 frontier/root가 proof evidence로 확정된다.

Full-cut state completion:
  ordering cut O 안의 모든 state events가 ideal에 들어간다.
```

첫 두 수준은 proof가 준비된 component부터 앞당길 수 있다. Full-cut completion은 가장 느린 proof/dependency를 기다린다.

논문은 component/event finality를 full global state completion과 혼동하면 안 된다.

## 8.1 Deterministic refinement algorithm

Replica state:

```text
O                  // latest compatible Multimmit ordering upper bound
G_O                // ordered event/dependency hypergraph
VerifiedEvidence   // exact-event validity proofs and effect data
I                  // currently finalized state ideal
Roots              // lane/component authenticated roots for I
Pending            // proof arrived before its ordering/dependencies
```

```text
OnOrderingFact(F):
  O := ExtendCompatible(O, OrderingFrontier(F))
  G_O := AddDeclaredEventsAndDependencies(G_O, F)
  Advance()

OnValiditySidecar(p):
  require WellFormedAndBounded(p)
  require VerifySemanticProof(p)
  VerifiedEvidence[p.event_id] := p
  Advance()

Advance():
  repeat
    candidates := CanonicalOrder({
      v in G_O \ I |
      EvidenceReady(v)
      AND Predecessors(v) subseteq I
      AND NoUnresolvedEarlierConflict(v)
      AND InputsLive(v)
      AND CrossEligibility(v)
    })
    if candidates is empty: break

    for each maximal disjoint batch B in candidates:
      patch := ComposeAuthenticatedEffects(B, Roots)
      require VerifyPatchAndNewRoots(patch)
      atomically persist (I := I union B, Roots := patch.new_roots)
```

`CanonicalOrder`는 proof arrival order를 사용하지 않는다. Arrival order가 다른 correct replicas도 같은 evidence set에서 같은 ideal/root를
계산해야 한다.

`NoUnresolvedEarlierConflict`가 중요하다. 같은 input version을 먼저 소비할 수 있는 earlier ordered event의 validity가 미정이면 later
consumer를 확정하지 않는다. 그렇지 않으면 earlier proof가 늦게 도착했을 때 later effect를 revoke해야 한다.

Declared read/write/object sets는 ordered payload에 먼저 binding되어야 하고 semantic proof가 그 선언의 complete access를 증명해야 한다.
Dynamic hidden access는 이 algorithm의 fast path에 들어갈 수 없다.

## 9. Latency

Event `v`의 state-finality time:

```text
T_final(v) = max(
  T_ordering_inclusion(v),
  T_validity_evidence(v),
  max_{u predecessor of v} T_final(u)
) + T_join(v)
```

따라서 proof lag의 영향은 graph dependency cone으로 한정된다. Unrelated component는 계속 전진한다.

Full-cut latency:

```text
T_full(O) = max_{v in O} T_final(v)
```

이는 slowest-event barrier이므로 논문의 주요 latency metric으로만 쓰면 component-level benefit을 숨길 수 있다. 함께 측정한다.

```text
per-event cut-to-finality distribution
per-component frontier lag
full-cut completion latency
join-compatible checkpoint divergence duration
```

Proof를 후속 transaction으로 ordering하는 baseline과 비교하면:

```text
Gap_proof_tx
  = T_proof_generation
    + T_proof_submission
    + T_wait_next_ordering_cut
    + T_verify_apply

Gap_objective_refinement
  = T_proof_generation_and_gossip_after_cut
    + T_verify_join
```

본 모델이 제거하는 것은 proof generation 자체가 아니라 `proof submission -> next ordering cut` 구간이다. Proof가 ordering cut 전에
준비되면 generation/gossip도 ordering과 overlap되어 local gap이 root join 수준으로 줄어든다.

## 10. Cross-lane example

Cross operation `X`가 lanes A, B, C를 건드린다고 하자.

```text
A local predecessor ---\
B local predecessor ----> CrossEvent(X) ---> A/B/C dependent suffixes
C local predecessor ---/
```

Eligibility:

```text
all A/B/C exact fragments in ordering bound
AND valid DCLP
AND proof coverage for all participant prepared effects
AND joint predicate/effect composition proof
AND input versions live
```

하나라도 없으면 `CrossEvent(X)`는 ideal에 들어가지 않는다. A/B/C의 X-independent local events는 dependency edge가 없으면 전진할 수
있고, X output을 읽는 suffix만 기다린다.

## 11. Safety theorem 후보

### Theorem 1 — Ideal determinism

같은 canonical ordering bound, prior checkpoint와 validity evidence set을 가진 correct validators는 같은 maximal state ideal을 계산한다.

### Theorem 2 — Evidence monotonicity

`E_1 subseteq E_2`이면 `I(O,E_1) subseteq I(O,E_2)`다.

### Theorem 3 — Cross-transcript joinability

Compatible Multimmit ordering evidence에서 유도된 valid state ideals의 union은 conflict-free valid ideal이며 deterministic checkpoint로
materialize할 수 있다.

### Theorem 4 — No revocation

Proof soundness, exact canonical binding과 fixed conflict order 아래에서 ideal에 포함된 state event는 이후 valid evidence 도착으로 제거되지
않는다.

### Theorem 5 — Dependency-scoped lag

Event `x`의 validity evidence가 누락되어도 `x`의 descendant가 아닌 eligible event의 state finality를 막지 않는다.

### Theorem 6 — Cross-lane atomicity

Cross operation을 one hypernode로 표현하고 complete participant eligibility에서만 ideal에 넣으면 participant effect의 strict subset은 어떤
valid checkpoint에도 나타나지 않는다.

## 12. 치명적 반례와 제약

### Hidden dependency

Application이 complete access/dependency set을 제공하지 않으면 두 independent로 보인 proofs가 실제 shared invariant를 깨뜨릴 수 있다.
Dynamic access는 joint proof 또는 SlowPath로 보낸다.

### Monolithic lane proof

Whole-lane root proof가 cross effect를 local root에 미리 섞으면 해당 effect를 제외한 ideal root를 만들 수 없다. Prepared cross root와
canonical local root를 분리해야 한다.

### Non-composable state commitment

독립 ideals의 authenticated patches를 합칠 수 없으면 union의 root를 얻기 위해 post-cut reexecution이 필요하다. Object/version effect logs,
sparse Merkle multipatches 또는 component roots가 필요하다.

### Root-bound proof rebase failure

Global pre/post-root만 인증하는 cumulative proof는 independent effect라도 다른 finalized patch 위로 rebase할 수 없다. Effect mode에서 이를
재사용하려면 object-local semantic proof와 current-root membership/update witness를 분리해야 한다.

### Giant component

모든 transaction이 하나의 hot mutable object에 의존하면 graph가 한 component가 되고 lag isolation benefit이 사라진다. 이것은 프로토콜로
없앨 수 없는 application dependency다.

### Proof availability

Proof correctness와 state/effect materialization data availability는 다르다. Proof-support vote 또는 sidecar DA는 exact proof/effect artifacts의
retention을 함께 보장해야 한다.

## 13. Novelty 경계

개별 구성요소는 새롭지 않다.

- Asynchronous proof generation: Mina/Hyli/vProgs
- Highest supported prefix extraction: GRANDPA/Multimmit
- Sidecar custody: blob/DA systems
- Object dependency DAG: sharded execution/object systems
- Lattice/order ideal mathematics: 고전적이다.
- [Anoma Resource Machine](https://specs.anoma.net/v1.0.0/arch/system/state/resource_machine/data_structures/transaction/transaction.html)은 resource logic/compliance/delta proofs, nullifiers와 composition-independent transaction proofs를 정의한다.
- [Kaspa vProgs](https://down.kastop.com/2025/vProgs_yellow_paper.pdf)는 conditional read/write proofs, Computation DAG와 state-commitment stitching proof를 정의한다.
- [Generalized Lattice Agreement](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/Generalized20Lattice20Agreement20-20PODC12.pdf)는 commutative update sets를 lattice로 합치는 replicated state machine을 제안한다.

방어 가능한 novelty 후보는 다음 결합이다.

> We define state finality over Multimmit as an evidence-refined lattice rather than a single cut-indexed root. Exact attributed vote transcripts name proof-supported state ideals, while late self-authenticating proofs monotonically join additional dependency-closed effects without a new ordering round. This makes heterogeneous replica checkpoints compatible and confines proof lag to its dependency cone.

직접 선행기술과 비교해야 할 핵심은 “late proof” 자체가 아니라 다음 성질이다.

1. Arrival-first Multimmit finality transcripts가 서로 달라도 state checkpoints가 join 가능하다.
2. Proof를 후속 payload로 ordering하지 않고 existing cut을 monotonic refine한다.
3. Cross-lane operation을 atomic hypernode로 포함한 dependency-scoped finality를 제공한다.
4. Same-cut named checkpoint와 post-cut objective refinement를 하나의 algebra로 설명한다.
5. Composition-independent effect proofs를 consensus payload로 재제출하지 않고 already-final Multimmit ordering evidence에 late-bind한다.

따라서 “resource/effect proofs”, “computation DAG”, “proof composition” 또는 “state lattice” 각각을 novelty로 주장하면 안 된다. Kaspa
vProgs는 proofs를 L1 operations/covenant index에 넣어 stitching된 commitment를 settle하고, Anoma는 proof-carrying resource transaction을
구성한다. 남는 차별점은 exact Multimmit arrival-first evidence에 대한 **consensus-free proof refinement**, 서로 다른 proof subsets의
checkpoint joinability와 zero-added-ordering-round property다.

## 14. 평가 계획

Topologies:

```text
independent lanes
sparse cross-lane graph
power-law shared objects
single hot-object giant component
```

Faults:

```text
proof delay/withholding
different first-arrival vote pools
invalid proof sidecar
missing participant proof
conflicting object consumers
materialization data withholding
```

Metrics:

```text
event/component/full-cut T_cut_to_state
ideal size / ordering-cut size
proof-lag descendant cone size
checkpoint join latency
checkpoint divergence duration across replicas
materialization bytes and root-composition cost
additional consensus rounds = 0
ordering latency regression
```

성공 기준은 full-cut barrier 하나가 아니라, proof가 늦은 component를 제외한 event들의 irrevocable finality가 실제로 앞당겨지고 서로 다른
replica checkpoints가 byte-identical deterministic join으로 수렴하는 것이다.
