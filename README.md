# Baton

구현 문서는 **[Baton Docs](docs/README.md)**에서 읽고 수정한다. [전체 목차](docs/SUMMARY.md)에서 레이어별·E2E 케이스별 페이지를 하나씩 검토한다. `.gitbook.yaml`과 `SUMMARY.md`를 포함한 GitBook 호환 Markdown 구조다.

| 읽을 문서 | 내용 |
|---|---|
| [구현 문서](docs/README.md) · [목차](docs/SUMMARY.md) | 네 레이어, 모듈 책임·Rust trait 초안·source map, E2E sequence, 빈 미결정 정책 표 |
| [Rust 인터페이스](docs/overview/rust-interfaces.md) · [단일 Rust 파일](docs/assets/interfaces/baton.rs) | 핵심 모듈 6개와 보조 역할 3개의 trait 선언·메서드·레이어 연결 |
| [연구·논문 초안](baton-paper.md) | 알고리즘, 조건부 안전성·재사용 논증, native prefix 통합 의무, 평가 계획 |

2026-10-03 사용자 구조를 기준으로 구현 개요와 컴포넌트 연결 설명을 정리했다. Bank는 현재 범위에서 제외한다. **Protocol 구현, native 통합 증명, E2E 실행, benchmark 결과는 없다.** 문서의 새 message / owner 이름은 제안 계약이며 existing upstream API와 구분한다.

이전 문서 39개와 관련 연구 자료는 [보관 진입점](archive/2026-10-03-root-history/README.md)에 원래 폴더 구조로 정리했다. 이전 구현 문서는 [archive](archive/2026-10-03-root-history/repository/research/archive/2026-10-03-implementation-outline/README.md)로 옮겨 보존했다. 다른 과거 Overpass 문서와 기존 research/archive도 연구 이력이며 새 구현 문서의 대체물이 아니다. 자세한 출처와 예전 Google Docs revision은 [handoff](BATON_HANDOFF.md)에 남겼다. [AGENTS.md](AGENTS.md)는 이어서 작업할 때의 지침이다.

Source pin: [Commonware 534af0ede48affd35b2111522527547b4cc9bf72](https://github.com/commonwarexyz/monorepo/tree/534af0ede48affd35b2111522527547b4cc9bf72). [Tempo Technical Overview](https://app.notion.com/p/2dfc1352439b801db5b6cf6fe21fc315?pvs=204)와 [Tempo DeepWiki](https://deepwiki.com/tempoxyz/tempo)는 구조 설명 방식의 참고이며 Tempo의 Simplex / Reth / REVM을 채택한 것은 아니다.

Canonical GitHub repository는 [djm07073/baton-research](https://github.com/djm07073/baton-research)다. 기존 local checkout 이름과 origin을 변경하지 않았다. Google Docs와 Markdown은 자동 양방향 동기화하지 않는다.

## 문서 미리보기

Node.js 20 이상과 Python 3을 사용한다. 아래 명령은 이 저장소 루트에서 실행한다.

```sh
npm ci
npm run docs:check
npm run docs:build
npm run docs:serve
```

[로컬 미리보기](http://127.0.0.1:8765)는 왼쪽 목차·검색·페이지 내 목차·이전/다음 이동을 제공한다. `site/`는 생성된 미리보기이며 Git에 넣지 않는다. 수정할 원본은 `docs/`다. Diagram source와 렌더된 그림은 `docs/assets/diagrams/`에 함께 보관하며, Markdown의 Mermaid source를 바꾸면 그림과 manifest도 다시 렌더해야 한다.

GitBook에서는 이 저장소의 `.gitbook.yaml`이 지정한 `docs/`를 Git Sync의 문서 루트로 사용할 수 있다. 이 저장소에는 연결용 소스를 준비했으며 GitBook 계정 연결·서비스 발행은 수행하지 않았다.

[IMPLEMENTATION_SPEC.md](IMPLEMENTATION_SPEC.md)는 이전 섹션 링크를 보존하는 진입점이다. 분리 직전 본문과 그림은 [보관 스냅샷](archive/2026-10-03-before-gitbook/README.md)에 보존했다. 현재 문서와 스냅샷을 동시에 수정하지 않는다.
