# Glowlog 디자인 하네스 — 역할

> 출처: R6 인터뷰 (2026-10-10)
> 단계: `harness/pipeline.md` / 게이트: `harness/gates.md`
> 수치 원본: `harness/rules.json` — 이 문서의 표와 다르면 rules.json이 우선한다.

## 에이전트와 편집 범위

| 에이전트 | 담당 | 편집 허용 범위 | 사용 도구 |
|---|---|---|---|
| `researcher` | S1·S2 | `runs/*/01-*`, `runs/*/02-*` | Read, Write, Glob, Grep, uibowl MCP 4종 |
| `designer` | S3·S4 | `runs/*/03-draft-*`, `screens/`, `components/` | Read, Write, Edit, Glob, Grep |
| `judge` (판정자) | G1~G4·S5 | **편집 없음** | Read, Bash(`python3 harness/scripts/judge.py`만) |
| 오케스트레이터 (메인 Claude) | 진행·복귀 | `runs/*/state.json`, `runs/*/04-components-before.css` (복사만) | — |
| 본인 | 사람 승인 (기록은 `choose.py`) | `runs/*/03-choice.md` | — |

- 편집 범위는 폴더가 아니라 파일 패턴 단위로 정한다 (S4 산출물이 `runs/`·`screens/`·`components/`에 나뉘어 있기 때문).

## 판정자 (읽기 전용)

- `judge` 에이전트에는 Edit·Write 도구를 주지 않는다.
- `05-report.json`은 `harness/scripts/judge.py`가 직접 쓴다.
- `judge`는 스크립트를 실행하고 리포트를 읽어 요약만 한다. 판정 결과를 조작할 수 없다.

## 편집 범위 위반 판정

- 방식: 사후 검사
- S5에서 이번 실행 중 바뀐 파일을 모두 모아, 해당 단계의 허용 범위 밖이면 위반으로 센다.
- 조건: 범위 밖 수정 파일 수 = 0 (`harness/gates.md` S5 조건 ⑤)
- 사전 차단: `.claude/settings.json` PreToolUse 훅 → `harness/scripts/guard.py`가 에이전트별 편집 범위·judge 명령·고정 문서를 호출 전에 막는다 (상세: `harness/orchestrator.md` "사전 차단")

## 자연어 트리거

| 이렇게 말하면 | 동작 |
|---|---|
| "화면 {N} 만들어줘, 키워드: A, B" | 새 실행 폴더를 만들고 S1부터 시작 (기존 폴더 재사용 금지) |
| "이어서 해줘" | 가장 최근 실행의 `state.json` 단계부터 재개 |
| "a로 할게" / "b로 할게" (+ 이유) | `choose.py`로 선택·이유·시안 해시를 기록 → CHOICE 판정 → S4 |
| "둘 다 별로야" | 시안 반려 → S2로 복귀 (1회 한도) |
| "판정만 돌려줘" | 최근 실행에 대해 `judge`만 `--adhoc`으로 실행 (이력에는 남지만 순서·재시도 대조에서 제외) |

## 에이전트 정의 파일

- `.claude/agents/researcher.md`, `.claude/agents/designer.md`, `.claude/agents/judge.md`
