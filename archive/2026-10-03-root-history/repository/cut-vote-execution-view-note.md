# Overpass: Cut Vote, Execution Plan, and Sync Overlap

> 2026-09-27 후속 결정: [Autobahn-family / Multimmit 적용 노트](./overpass-family-multimmit-review.md)를 함께 본다. 아래의 동일 proposal 실행계획 설명은 Autobahn 경로의 설명이며 Multimmit의 모든 L-QC가 동일 prefix를 확정한다는 뜻이 아니다. 최신 논문의 signer·checkpoint 정책은 M2로 열어 두었고, 아래의 “기존 자격 유지”는 이 노트를 쓴 당시 범위다.

> 기록일: 2026-09-26  
> 범위: 최신 Overpass 논문의 shared-state speculative execution 설명을 명확히 하는 연구 노트. 기존 proof/PAC SDK, Commonware 구현, execution signer 자격은 변경하지 않는다.

## 1. 이번에 합의한 핵심 표현

**동일한 Autobahn cut 제안에 투표하는 정상 replica들은 동일한 실행 대상 prefix의 참조와 공통 ordering rule을 공유한다. 따라서 누락된 block synchronization과 확보된 입력의 speculative execution을 cut consensus와 병렬로 진행할 수 있다.**

여기서 사용자가 말한 execution view는 **어떤 block 범위를 어떤 기준 순서로 실행할지에 대한 candidate execution plan**이다. 이미 확보한 body들의 집합, transaction-level dependency DAG, 실행 진행도 또는 실행 결과를 뜻하지 않는다.

"Cut에 투표한 replica들은 이미 같은 block과 execution view를 가지고 있다"는 문장은 다음으로 바꾸어 사용한다.

> 같은 cut 제안은 같은 block prefix들을 지정한다. 동일한 ordering context와 rule 아래 정상 replica들은 그 제안에 대한 같은 block-level 기준 순서를 계산할 수 있으며, 본문 확보와 execution은 각 replica에서 비동기적으로 진행된다.

서로 다른 제안/view에 대한 투표를 하나의 집단으로 묶지 않는다. Byzantine replica가 실제로 같은 계획을 유지하거나 실행한다고 가정하지 않는다.

## 2. 알고 있는 것과 아직 준비되지 않을 수 있는 것

| 항목 | Cut 제안 수신·투표 시점의 의미 |
|---|---|
| 선택 대상 | 같은 lane tip identity와 그 tip이 인증된 hash ancestry로 지정하는 prefix 범위를 공유한다. 높이만 같다는 뜻이 아니다. |
| Block-level 순서 | 같은 slot, 누적 ordering 경계, lane priority와 ordering-rule version이 있으면 같은 기준 순서를 정한다. 이전 slot의 경계가 아직 미정이면 그 context가 확보될 때까지 조건부 계획이다. |
| 전체 block body와 ancestor 목록 | 투표 시점에 모두 로컬에 있을 필요는 없다. Compact tip 참조만으로 누락된 모든 ancestor의 hash나 transaction bytes를 이미 열거할 수 있다고 주장하지 않는다. Sync로 chain과 본문을 확보·검증한다. |
| Transaction dependency | Body 또는 인증된 access metadata를 확보해야 분석할 수 있다. Tip과 ordering rule만으로 완성된 transaction-level DAG를 안다고 주장하지 않는다. |
| 실행 가능한 parent state | Ordering context와 별개다. 필요한 state가 준비되지 않았으면 기다리거나 명시적인 speculative parent에서 실행하고 최종 문맥에서 검증한다. |
| 실행 결과 | Cut vote는 execution 완료, 같은 read version, 같은 speculative root 또는 application 성공의 증거가 아니다. |

## 3. Overpass에서 겹치는 두 실행 구간

```text
Block 도착: 공통 ordering rule로 현재 입력의 candidate 순서를 구성
  -> 확보한 입력을 speculative execute (cut 제안 전에도 가능)

동일한 cut 제안 수신
  +-- 기존 cut consensus 진행
  +-- 제안에 포함된 누락 block/history Sync
  +-- 확보한 입력과 준비된 state로 speculative execution 진행
          |
          v
전체 ordering finality 확보
  -> exact selected inputs / 누적 경계 / canonical parent 확인
  -> 유효한 작업 재사용, 영향받은 작업 재검증·필요한 재실행
  -> 기존 실행 결과 인증 조건 충족 -> canonical adoption
```

- **제안 전:** 도착한 block을 사용하므로 최종 포함 집합이 아직 미정이다. Late predecessor, cut 제외와 parent 변경 때문에 보정이 생길 수 있다.
- **제안 후·확정 전:** 해당 candidate의 실행 대상이 구체화된다. Sync와 실행을 consensus와 겹칠 수 있지만 제안이 최종 선택됐다고 간주하지 않는다.
- **확정 후:** 전체 입력을 검증하고 canonical parent에 맞춘 결과만 채택한다. Cut 확정 시 모든 replica가 body 확보나 execution을 마쳤다는 보장은 없다.

필요한 입력·state dependency는 존중한다. 독립 작업은 진행할 수 있고, 누락된 predecessor의 영향이 불명확한 작업을 추측 실행했다면 재검증해야 한다. 실행 완료나 전체 Sync를 ordering vote의 새로운 선행조건으로 추가하지 않는다. 자원 경합 때문에 ordering 성능이 저하되지 않는지는 별도 평가 대상이다.

## 4. Autobahn과 Multimmit을 혼동하지 않기

- **Autobahn 기본 certified-tip 경로:** tip의 `f+1` PoA로 availability를 검증하고, 리더가 제안한 cut 전체를 기존 Prepare/Confirm 또는 native fast path로 확정한다. Replica는 누락된 body를 fetch하기 전에도 cut에 투표할 수 있다. Autobahn의 optimistic uncertified-tip 최적화는 별도 경로이며 이 설명의 전제가 아니다.
- **Multimmit:** 리더 제안에 상대적인 chain별 지지 위치를 vote에 기록하고, L-QC의 보고와 추출 규칙으로 finalized 범위를 도출한다. 리더가 제안한 모든 tip이 그대로 최종 cut이 된다고 해석하지 않는다. Chain-local membership finality와 실제 global ordered-prefix placement도 구분한다.

따라서 Autobahn의 "같은 cut proposal에 대한 실행 계획" 설명을 Multimmit의 "모든 voter가 이미 동일한 최종 tip 집합을 지지한다"는 주장으로 옮기지 않는다.

## 5. 논문의 contribution과 연결

핵심 기여는 deterministic ordering 자체나 Sync/consensus 중첩 자체가 아니다. Autobahn은 이미 non-blocking/timely sync를 설계한다. Overpass는 **공통 ordering의 사전 적용으로 application execution까지 dissemination·cut consensus와 중첩하고, operation-aware producer placement로 late predecessor에 따른 speculative-work invalidation을 줄이는 것**을 제안한다.

측정할 것은 cut 투표자의 view 일치 여부가 아니라, **cut 확정 전에 완료·재사용 가능한 실행량, 확정 후 남는 보정 비용, 최종 state-finalization latency**다. 개선은 연구 가설이며 항상 cut과 동시에 state-final이 된다는 보장은 아니다.

### 논문에 사용할 English wording

> Correct replicas voting for the same Autobahn cut proposal share authenticated references to the same candidate lane prefixes. Given the same cumulative ordering boundaries and ordering rule, they can derive a common block-level execution plan without first acquiring every block body. Overpass overlaps synchronization and speculative execution of available inputs with cut consensus. This shared plan does not imply identical local data availability, transaction-level dependency knowledge, or completed execution; canonical adoption still requires full ordering finality and validation against the exact selected inputs and canonical parent.

## 6. 근거

- [Autobahn, §5.1 and §5.2.1–5.2.2](https://www.cs.cornell.edu/lorenzo/papers/Suri24Autobahn.pdf): `f+1` PoA, Prepare 투표 뒤 비동기 fetch, non-blocking sync와 committed-cut deterministic zipping. Appendix A.3의 timely-sync 분석은 execution 완료 보장이 아니다.
- [Multimmit, Extending Blocks for Faster Finality](https://arxiv.org/pdf/2607.21021): proposal-relative voting, L-QC 기반 범위 추출 및 membership/total-order placement의 구분. 2026-09-26 확인한 온라인 PDF는 v5(2026-09-18); 로컬 fork와 동일 버전이라고 가정하지 않는다.

이 노트는 설명의 명확화이며 formal proof, implementation 또는 benchmark 완료 기록이 아니다.
