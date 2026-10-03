# Baton

구현 스펙은 **[IMPLEMENTATION_SPEC.md](IMPLEMENTATION_SPEC.md) 한 파일**에서 읽고 수정한다.

| 읽을 문서 | 내용 |
|---|---|
| [구현 스펙](IMPLEMENTATION_SPEC.md) | Multimmit example에 Tx / Baton / generic execution / QMDB를 연결하는 네 레이어, 책임·인터페이스·source map, lifecycle sequence, 빈 미결정 정책 표 |
| [연구·논문 초안](baton-paper.md) | 알고리즘, 조건부 안전성·재사용 논증, native prefix 통합 의무, 평가 계획 |

2026-10-03 사용자 구조를 기준으로 구현 개요와 컴포넌트 연결 설명을 정리했다. Bank는 현재 범위에서 제외한다. **Protocol 구현, native 통합 증명, E2E 실행, benchmark 결과는 없다.** 문서의 새 message / owner 이름은 제안 계약이며 existing upstream API와 구분한다.

이전 문서 39개와 관련 연구 자료는 [보관 진입점](archive/2026-10-03-root-history/README.md)에 원래 폴더 구조로 정리했다. 이전 구현 문서는 [archive](archive/2026-10-03-root-history/repository/research/archive/2026-10-03-implementation-outline/README.md)로 옮겨 보존했다. 다른 과거 Overpass 문서와 기존 research/archive도 연구 이력이며 새 구현 문서의 대체물이 아니다. 자세한 출처와 예전 Google Docs revision은 [handoff](BATON_HANDOFF.md)에 남겼다. [AGENTS.md](AGENTS.md)는 이어서 작업할 때의 지침이다.

Source pin: [Commonware 534af0ede48affd35b2111522527547b4cc9bf72](https://github.com/commonwarexyz/monorepo/tree/534af0ede48affd35b2111522527547b4cc9bf72). [Tempo Technical Overview](https://app.notion.com/p/2dfc1352439b801db5b6cf6fe21fc315?pvs=204)와 [Tempo DeepWiki](https://deepwiki.com/tempoxyz/tempo)는 구조 설명 방식의 참고이며 Tempo의 Simplex / Reth / REVM을 채택한 것은 아니다.

Canonical GitHub repository는 [djm07073/baton-research](https://github.com/djm07073/baton-research)다. 기존 local checkout 이름과 origin을 변경하지 않았다. Google Docs와 Markdown은 자동 양방향 동기화하지 않는다.
