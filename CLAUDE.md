# Glowlog — Claude 작업 지침

## 필수 규칙

- 모든 디자인 및 코드 작업 시 **반드시 `/design.md`를 먼저 읽고** 시작할 것
- 토큰값을 임의로 추측하거나 변경하지 말 것
- 기능 요구사항은 `/PRD.md` 참조
- 토큰·효과·컴포넌트 규칙의 단일 기준(SSOT)은 `/design.md`

## 프로젝트 개요

- **앱명**: Glowlog
- **종류**: 뷰티/스킨케어 루틴 트래킹 모바일 앱
- **프레임 사이즈**: 390 × 844 (iPhone 14 기준)
- **언어**: 한국어

## 핵심 화면 (3개)

| # | 화면명 | 역할 |
|---|--------|------|
| 1 | 오늘 한 관리 작성 | 카테고리 선택 → 제품·시술 입력 → 사진 첨부 → 저장 |
| 2 | 날짜·루틴 목록 | 진행 중 루틴 카드 + 달력, 날짜별 기록 요약 |
| 3 | Before / After 비교 | 시작일 vs 최근 기록 사진·메모 나란히 표시 |

## 디자인 시스템 핵심 원칙 요약

- **Frosted Glass**: `backdrop-filter: blur(12px)` + `rgba(255,255,255,0.72)` — blur 20px 초과 금지
- **Iridescent Gradient**: `linear-gradient(135deg, #F2C4CE, #E8D5F5, #C5D8F7, #C5EDE0)`
- **그림자 없음**: `drop-shadow` / 외부 `box-shadow` 사용 금지 — `box-shadow: inset` inner glow만 허용
- **토큰만 사용**: 임의 hex 값 금지 — 허용 값은 `design.md` `## 판정 규칙 (기계용)` 참조
- **Auto Layout 필수**

## 금지 사항

- 소셜/커뮤니티/팔로우 기능
- 제품 구매·커머스 연동
- AI 피부 분석
- 로그인·회원가입 화면
- 알림·푸시 설정 화면

## 하네스 실행

이 프로젝트는 화면 1개를 만드는 디자인 하네스로 운영한다.
메인 Claude 세션이 오케스트레이터이며, 트리거를 받으면 **반드시 `/harness/orchestrator.md`를 먼저 읽고** 그 순서대로 진행한다.

### 트리거

| 이렇게 말하면 | 동작 |
|---|---|
| "화면 {N} 만들어줘, 키워드: A, B" | 새 실행 시작 (S1부터, 기존 폴더 재사용 금지) |
| "이어서 해줘" | 최근 실행 재개 |
| "a로 할게" / "b로 할게" | `choose.py`로 시안 선택 기록 → CHOICE 판정 → S4 |
| "둘 다 별로야" | 시안 반려 → S2 |
| "판정만 돌려줘" | judge만 실행 (`--adhoc`: 이력의 순서·재시도 대조에서 제외) |

### 오케스트레이터 금지 행동

- 산출물(01~03, `screens/`, `components/`)을 직접 작성하지 않는다 — 에이전트에 맡긴다
- 게이트 통과 전에 다음 단계로 넘어가지 않는다
- CHOICE 게이트(선택값 + 시안 해시) 통과 없이 S4를 시작하지 않는다. 본인이 말하지 않았는데 `choose.py`를 실행하지 않는다
- 실행 중 고정 문서(`PRD.md`, `design.md`, `CLAUDE.md`, `story-*.md`, `harness/` 전체)를 수정하지 않는다

### 사전 차단 (guard 훅)

- `.claude/settings.json`의 PreToolUse 훅이 `harness/scripts/guard.py`로 편집 범위·judge 명령·고정 문서 수정을 호출 전에 막는다. 이 파일은 저장소에 커밋한다 (빠지면 동료 환경에서 강제가 사라짐)
- 렌더 판정용 Chrome 경로는 환경변수 `GLOWLOG_CHROME` 또는 `harness/rules.json` `render.chrome_candidates`

### 하네스 사용 전 필수

- 규칙(`design.md`, `harness/rules.json`, `harness/scripts/`)을 고친 뒤와 하네스 사용 전에 회귀 검사 4단계가 모두 통과해야 한다 — `python3 harness/tests/run_all.py` (`harness/review.md` 1절)
  ① 판정 함수 샘플 68건 + 🚦 커버리지 ② 게이트 예시 12개(실제 명령) ③ 재판정 자기 검증 ④ `runs/*` 실행 기록 재판정 (예전 PASS가 지금 FAIL이면 깨짐)
- 렌더 판정에 Google Chrome 필요

### 문서 지도

| 문서 | 내용 |
|---|---|
| `story-service.md` | 서비스 유저스토리, 어기면 안 되는 것 |
| `story-work.md` | 원래 손작업 흐름 |
| `harness/purpose.md` | 입력, 수신자, 완료 기준 |
| `harness/pipeline.md` | S1~S5 단계, 입출력 |
| `harness/artifacts.md` | 폴더·파일 구조, 재개 |
| `harness/gates.md` | 게이트 통과 조건, 사람 승인, 실패 복귀 |
| `harness/roles.md` | 에이전트별 편집 범위, 판정자, 트리거 |
| `harness/orchestrator.md` | 진행 순서, 규칙, state.json, 멈춤 보고 |
| `harness/review.md` | 판정 스크립트 검증, 시범 실행 리뷰 |
| `harness/rules.json` | 운영 수치·금지 키워드·편집 범위 (규칙 원본 ①) |
| `design.md` `## 판정 규칙 (기계용)` | 디자인 허용값 (규칙 원본 ②) |
| `harness/templates/` | 산출물 양식 (`03-choice.md`는 복사 금지) |
| `harness/scripts/` | `judge.py` 판정, `snapshot.py` 단계 스냅샷, `choose.py` 사람 승인 기록, `new_run.py` 실행 폴더 생성, `guard.py` 사전 차단 훅 |
| `harness/tests/` | `run_all.py` 회귀 검사 (`run_fixtures.py` 68건, `run_gates.py` 게이트 예시 12개, `rejudge.py` 실행 기록 재판정), `build_fixtures.py`·`build_gate_cases.py` 샘플 생성 |
