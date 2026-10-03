# 참고자료와 문서 상태

연구 초안·이전 자료·설명 방식의 참고 출처를 모았다. 최신 사용자 결정과 현재 문서가 이전 스냅샷에 우선한다.

## 참고자료와 문서 상태

[Tempo Technical Overview](https://app.notion.com/p/2dfc1352439b801db5b6cf6fe21fc315?pvs=204)의 **전체 구조 → 컴포넌트별 책임·인터페이스 → propose / verify / finalize sequence** 전개를 참고했다. [Tempo DeepWiki architecture overview](https://deepwiki.com/tempoxyz/tempo/2-architecture-overview)에서는 레이어 구성, 실제 파일 mapping, actor system, P2P channels, inter-layer communication을 설명하는 구성을 확인했다. 이 자료들은 설명 방식의 참고이며, 기술 사실과 재사용 가능 여부는 아래 pinned Commonware 소스로 검증한다. Tempo의 Simplex + Reth/REVM / Engine API 구현을 Baton의 채택 기술로 옮기지는 않는다. 이번 설계는 Native Multimmit + Baton + generic execution / QMDB다.

연구 알고리즘과 조건부 논증의 출처는 [Baton 연구 초안](https://docs.google.com/document/d/1PtUpMGMNMkyo1UEY2bNciJD3oIiGLRf407PW_T3Er5I/edit)이다. 예전 [Google 구현 스펙](https://docs.google.com/document/d/10x4RvqG8e07Tai0s20e-wpCfz8COgH0JGR5daKE1xO8/edit)은 상세 계약의 이전 참고자료이며 이번 개요와 자동 동기화하지 않는다.

문서의 diagram과 인터페이스는 계획이다. Pin의 source와 현재 연결 경계를 확인한 것으로 native correctness·성능·QMDB crash recovery 테스트가 완료되었다고 주장하지 않는다. 미결정 사항은 위 각 레이어 표의 빈 결정 칸에 채운다.
